"""
MediChat-RD — 自然语言处理模块
医学文本NER（命名实体识别）+ 关系抽取 + 文本摘要
"""
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class MedicalEntity:
    """医学实体"""
    text: str
    entity_type: str  # disease / symptom / drug / gene / test / body_part
    start: int
    end: int
    confidence: float = 1.0


@dataclass
class MedicalRelation:
    """医学关系"""
    subject: str
    relation: str  # causes / treats / diagnosed_by / has_symptom
    obj: str
    confidence: float = 1.0


class MedicalNLP:
    """医学NLP处理器"""

    # 医学实体词典
    ENTITY_DICT = {
        "disease": [
            "重症肌无力", "戈谢病", "脊髓性肌萎缩症", "Duchenne肌营养不良",
            "法布雷病", "血友病", "成骨不全症", "苯丙酮尿症", "多囊肾病",
            "系统性红斑狼疮", "多发性硬化", "肌萎缩侧索硬化", "Wilson病",
        ],
        "symptom": [
            "眼睑下垂", "吞咽困难", "全身无力", "下午加重", "肌肉萎缩",
            "肝脾肿大", "贫血", "血小板减少", "骨痛", "关节出血",
            "肢端疼痛", "皮肤血管角化瘤", "角膜混浊", "肾功能不全",
            "反复骨折", "蓝巩膜", "听力下降", "运动发育迟缓",
        ],
        "drug": [
            "溴吡斯的明", "泼尼松", "硫唑嘌呤", "他克莫司",
            "伊米苷酶", "维拉苷酶", "阿加糖酶", "依库珠单抗",
            "Spinraza", "Zolgensma", "利司扑兰",
        ],
        "gene": [
            "CHRNA1", "CHRNE", "GBA1", "SMN1", "DMD", "GLA",
            "F8", "COL1A1", "PAH", "PKD1", "HBB",
        ],
        "test": [
            "乙酰胆碱受体抗体", "肌电图", "冰试验", "新斯的明试验",
            "酶活性检测", "基因检测", "肌肉活检", "脑脊液检查",
            "CK", "LDH", "ALT", "AST", "肌钙蛋白",
        ],
    }

    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """医学实体抽取"""
        entities = []
        
        for entity_type, words in self.ENTITY_DICT.items():
            for word in words:
                start = 0
                while True:
                    idx = text.find(word, start)
                    if idx == -1:
                        break
                    entities.append(MedicalEntity(
                        text=word,
                        entity_type=entity_type,
                        start=idx,
                        end=idx + len(word),
                    ))
                    start = idx + 1
        
        # 去重
        seen = set()
        unique = []
        for e in entities:
            key = (e.text, e.start, e.end)
            if key not in seen:
                seen.add(key)
                unique.append(e)
        
        return sorted(unique, key=lambda x: x.start)

    def extract_relations(self, text: str, entities: List[MedicalEntity]) -> List[MedicalRelation]:
        """医学关系抽取"""
        relations = []
        
        # 模式匹配
        patterns = [
            (r"(.+?)(?:导致|引起|造成)(.+?)(?:[。，；])", "causes"),
            (r"(.+?)(?:治疗|用于治疗)(.+?)(?:[。，；])", "treats"),
            (r"(.+?)(?:诊断|检测)(.+?)(?:[。，；])", "diagnosed_by"),
            (r"(.+?)(?:表现为|症状为|有)(.+?)(?:[。，；])", "has_symptom"),
        ]
        
        for pattern, relation in patterns:
            for match in re.finditer(pattern, text):
                subject = match.group(1).strip()
                obj = match.group(2).strip()
                relations.append(MedicalRelation(
                    subject=subject,
                    relation=relation,
                    obj=obj,
                ))
        
        return relations

    def summarize(self, text: str, max_length: int = 200) -> str:
        """文本摘要"""
        sentences = re.split(r'[。！？；]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return ""
        
        # 选择包含医学实体的句子
        scored_sentences = []
        for s in sentences:
            score = 0
            for words in self.ENTITY_DICT.values():
                for w in words:
                    if w in s:
                        score += 1
            scored_sentences.append((score, s))
        
        # 按分数排序，取前几句
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        summary = ""
        for _, s in scored_sentences:
            if len(summary) + len(s) <= max_length:
                summary += s + "。"
            else:
                break
        
        return summary

    def analyze_clinical_text(self, text: str) -> Dict:
        """综合分析临床文本"""
        entities = self.extract_entities(text)
        relations = self.extract_relations(text, entities)
        summary = self.summarize(text)
        
        # 按类型统计
        entity_counts = {}
        for e in entities:
            entity_counts[e.entity_type] = entity_counts.get(e.entity_type, 0) + 1
        
        return {
            "entities": [
                {"text": e.text, "type": e.entity_type, "position": f"{e.start}-{e.end}"}
                for e in entities
            ],
            "entity_counts": entity_counts,
            "relations": [
                {"subject": r.subject, "relation": r.relation, "object": r.obj}
                for r in relations
            ],
            "summary": summary,
            "total_entities": len(entities),
            "total_relations": len(relations),
        }


# ========== 测试 ==========
if __name__ == "__main__":
    nlp = MedicalNLP()
    
    print("=" * 60)
    print("📝 医学NLP处理器测试")
    print("=" * 60)
    
    test_text = """
    患者女性，35岁，主诉眼睑下垂、吞咽困难3个月，下午症状加重。
    查体：双眼睑下垂，四肢肌力4级。乙酰胆碱受体抗体阳性。
    考虑重症肌无力，建议行肌电图检查。治疗方案：溴吡斯的明口服。
    """
    
    result = nlp.analyze_clinical_text(test_text)
    
    print(f"\n📊 实体抽取 ({result['total_entities']}个):")
    for e in result['entities']:
        print(f"   {e['type']}: {e['text']}")
    
    print(f"\n📊 实体统计: {result['entity_counts']}")
    
    if result['summary']:
        print(f"\n📝 摘要: {result['summary']}")
