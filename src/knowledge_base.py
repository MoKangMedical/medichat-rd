"""
MediChat-RD — 知识库管理
罕见病知识库的构建、索引、检索和更新
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class KnowledgeType(str, Enum):
    """知识类型"""
    DISEASE = "disease"          # 疾病知识
    GENE = "gene"                # 基因知识
    PHENOTYPE = "phenotype"      # 表型知识
    DRUG = "drug"                # 药物知识
    GUIDELINE = "guideline"      # 诊疗指南
    LITERATURE = "literature"    # 文献证据
    CASE = "case"                # 病例


class EvidenceLevel(str, Enum):
    """证据等级"""
    LEVEL_1 = "1a"  # 系统综述/Meta分析
    LEVEL_2 = "1b"  # 随机对照试验
    LEVEL_3 = "2a"  # 队列研究
    LEVEL_4 = "2b"  # 病例对照研究
    LEVEL_5 = "3"   # 病例报告
    LEVEL_6 = "4"   # 专家意见
    LEVEL_7 = "5"   # 计算推断


@dataclass
class KnowledgeEntity:
    """知识实体"""
    entity_id: str
    entity_type: KnowledgeType
    name: str
    description: str
    attributes: dict = field(default_factory=dict)
    relations: list[dict] = field(default_factory=list)
    source: str = ""
    evidence_level: EvidenceLevel = EvidenceLevel.LEVEL_7
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.8


@dataclass
class SearchResult:
    """检索结果"""
    entity: KnowledgeEntity
    score: float
    match_reason: str
    highlights: list[str] = field(default_factory=list)


@dataclass
class QueryContext:
    """查询上下文"""
    query: str
    query_type: Optional[KnowledgeType] = None
    filters: dict = field(default_factory=dict)
    top_k: int = 10
    min_score: float = 0.3


class KnowledgeIndex:
    """知识索引 — 基于倒排索引的快速检索"""

    def __init__(self):
        self._index: dict[str, set[str]] = {}  # token -> entity_ids
        self._entities: dict[str, KnowledgeEntity] = {}

    def add(self, entity: KnowledgeEntity):
        """添加实体到索引"""
        self._entities[entity.entity_id] = entity
        tokens = self._tokenize(f"{entity.name} {entity.description}")
        for token in tokens:
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(entity.entity_id)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """搜索并返回 (entity_id, score) 列表"""
        tokens = self._tokenize(query)
        scores: dict[str, float] = {}

        for token in tokens:
            if token in self._index:
                for eid in self._index[token]:
                    scores[eid] = scores.get(eid, 0) + 1.0

        # 归一化
        if scores:
            max_score = max(scores.values())
            scores = {eid: s / max_score for eid, s in scores.items()}

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def get(self, entity_id: str) -> Optional[KnowledgeEntity]:
        return self._entities.get(entity_id)

    @property
    def size(self) -> int:
        return len(self._entities)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """简单分词"""
        import re
        text = text.lower()
        # 分离中文字符和英文单词
        chinese_chars = set(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = set(re.findall(r'[a-z][a-z0-9]+', text))
        hpo_ids = set(re.findall(r'hp:\d+', text))
        return chinese_chars | english_words | hpo_ids


class RareDiseaseKnowledgeBase:
    """
    罕见病知识库主类

    功能：
    - 加载和管理多源知识数据
    - 支持多维度检索（疾病、基因、表型、药物）
    - 知识关联和图谱查询
    - 增量更新和版本管理
    """

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or os.path.join(DATA_DIR, "rare-diseases.json")
        self.index = KnowledgeIndex()
        self.diseases: dict[str, dict] = {}
        self.genes: dict[str, dict] = {}
        self.phenotypes: dict[str, dict] = {}
        self._load_time: Optional[float] = None
        self._stats = {"total_entities": 0, "diseases": 0, "genes": 0, "phenotypes": 0}

    def load(self):
        """加载知识库数据"""
        start = time.time()
        self._load_diseases()
        self._build_index()
        self._load_time = time.time() - start
        logger.info(
            f"知识库加载完成: {self._stats['total_entities']}个实体, "
            f"耗时{self._load_time:.2f}s"
        )

    def _load_diseases(self):
        """加载罕见病数据"""
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            logger.warning(f"数据文件不存在: {self.data_path}，使用空数据")
            raw = []

        for item in raw:
            did = item.get("id", "")
            self.diseases[did] = item
            self._stats["diseases"] += 1

            # 提取基因
            gene = item.get("gene", "")
            if gene:
                self.genes[gene] = {"name": gene, "diseases": [did]}
                self._stats["genes"] += 1

            # 提取表型
            for hpo in item.get("hpo", []):
                if hpo not in self.phenotypes:
                    self.phenotypes[hpo] = {"hpo_id": hpo, "diseases": []}
                self.phenotypes[hpo]["diseases"].append(did)
                self._stats["phenotypes"] += 1

        self._stats["total_entities"] = (
            self._stats["diseases"] + self._stats["genes"] + self._stats["phenotypes"]
        )

    def _build_index(self):
        """构建检索索引"""
        for did, d in self.diseases.items():
            entity = KnowledgeEntity(
                entity_id=did,
                entity_type=KnowledgeType.DISEASE,
                name=d.get("name", ""),
                description=d.get("description", d.get("name", "")),
                attributes={
                    "omim": d.get("omim", ""),
                    "orphanet": d.get("orphanet", ""),
                    "inheritance": d.get("inheritance", ""),
                    "prevalence": d.get("prevalence", ""),
                    "gene": d.get("gene", ""),
                    "hpo": d.get("hpo", []),
                },
                source="rare-diseases.json",
            )
            self.index.add(entity)

        for gene_name, g in self.genes.items():
            entity = KnowledgeEntity(
                entity_id=f"GENE:{gene_name}",
                entity_type=KnowledgeType.GENE,
                name=gene_name,
                description=f"基因 {gene_name}，关联疾病: {', '.join(g.get('diseases', []))}",
                attributes={"diseases": g.get("diseases", [])},
            )
            self.index.add(entity)

    def search(self, query: str, **kwargs) -> list[SearchResult]:
        """综合检索"""
        ctx = QueryContext(query=query, **kwargs)
        raw_results = self.index.search(ctx.query, top_k=ctx.top_k)

        results = []
        for eid, score in raw_results:
            if score < ctx.min_score:
                continue
            entity = self.index.get(eid)
            if not entity:
                continue
            if ctx.query_type and entity.entity_type != ctx.query_type:
                continue

            results.append(SearchResult(
                entity=entity,
                score=score,
                match_reason=f"关键词匹配 (score={score:.2f})",
            ))

        return results

    def get_disease(self, disease_id: str) -> Optional[dict]:
        """获取疾病详情"""
        return self.diseases.get(disease_id)

    def get_diseases_by_gene(self, gene: str) -> list[dict]:
        """根据基因查找关联疾病"""
        g = self.genes.get(gene)
        if not g:
            return []
        return [self.diseases[did] for did in g.get("diseases", []) if did in self.diseases]

    def get_diseases_by_phenotype(self, hpo_id: str) -> list[dict]:
        """根据表型查找关联疾病"""
        p = self.phenotypes.get(hpo_id)
        if not p:
            return []
        return [self.diseases[did] for did in p.get("diseases", []) if did in self.diseases]

    def get_related_diseases(self, disease_id: str, min_shared: int = 2) -> list[dict]:
        """查找相关疾病（共享表型）"""
        target = self.diseases.get(disease_id)
        if not target:
            return []

        target_hpo = set(target.get("hpo", []))
        related = []

        for did, d in self.diseases.items():
            if did == disease_id:
                continue
            shared = target_hpo & set(d.get("hpo", []))
            if len(shared) >= min_shared:
                related.append({
                    **d,
                    "shared_phenotypes": list(shared),
                    "shared_count": len(shared),
                })

        related.sort(key=lambda x: x["shared_count"], reverse=True)
        return related

    def add_disease(self, disease_data: dict):
        """动态添加疾病知识"""
        did = disease_data.get("id", f"RD-DYN-{int(time.time())}")
        disease_data["id"] = did
        self.diseases[did] = disease_data

        entity = KnowledgeEntity(
            entity_id=did,
            entity_type=KnowledgeType.DISEASE,
            name=disease_data.get("name", ""),
            description=disease_data.get("description", disease_data.get("name", "")),
            attributes=disease_data,
            source="dynamic_add",
        )
        self.index.add(entity)
        self._stats["diseases"] += 1
        self._stats["total_entities"] += 1
        logger.info(f"动态添加疾病: {did} - {disease_data.get('name')}")

    def export_stats(self) -> dict:
        """导出知识库统计信息"""
        return {
            **self._stats,
            "index_size": self.index.size,
            "load_time_s": self._load_time,
            "data_path": self.data_path,
            "timestamp": datetime.now().isoformat(),
        }
