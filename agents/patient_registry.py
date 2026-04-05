"""
MediChat-RD — 罕见病患者注册系统
参考PhenoTips + RDRF：患者登记+队列管理+数据导出
"""
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class PatientRegistry:
    """罕见病患者注册系统"""

    def __init__(self, db_path: str = "data/patient_registry.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            # 患者登记表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS registry_patients (
                    registry_id TEXT PRIMARY KEY,
                    patient_code TEXT UNIQUE,
                    disease TEXT,
                    disease_omim TEXT,
                    hpo_phenotypes TEXT,
                    gene_variants TEXT,
                    diagnosis_date TEXT,
                    diagnosis_status TEXT,
                    inheritance TEXT,
                    age_of_onset INTEGER,
                    gender TEXT,
                    ethnicity TEXT,
                    consent_research INTEGER DEFAULT 0,
                    consent_matching INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            # 队列表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cohorts (
                    cohort_id TEXT PRIMARY KEY,
                    name TEXT,
                    disease TEXT,
                    criteria TEXT,
                    patient_count INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            # 患者-队列关联
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cohort_patients (
                    cohort_id TEXT,
                    registry_id TEXT,
                    joined_at TEXT,
                    PRIMARY KEY (cohort_id, registry_id)
                )
            """)

    def register_patient(self, disease: str, hpo_phenotypes: List[str],
                        gene_variants: List[Dict] = None, **kwargs) -> Dict:
        """登记患者"""
        registry_id = f"reg_{uuid.uuid4().hex[:8]}"
        patient_code = f"MC{datetime.now().strftime('%Y%m%d')}{registry_id[-4:]}"
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO registry_patients 
                (registry_id, patient_code, disease, hpo_phenotypes, gene_variants,
                 diagnosis_date, diagnosis_status, inheritance, age_of_onset,
                 gender, ethnicity, consent_research, consent_matching,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                registry_id, patient_code, disease,
                json.dumps(hpo_phenotypes, ensure_ascii=False),
                json.dumps(gene_variants or [], ensure_ascii=False),
                kwargs.get("diagnosis_date", ""),
                kwargs.get("diagnosis_status", "confirmed"),
                kwargs.get("inheritance", ""),
                kwargs.get("age_of_onset"),
                kwargs.get("gender", ""),
                kwargs.get("ethnicity", ""),
                1 if kwargs.get("consent_research") else 0,
                1 if kwargs.get("consent_matching") else 0,
                now, now,
            ))

        return {
            "registry_id": registry_id,
            "patient_code": patient_code,
            "disease": disease,
            "status": "registered",
        }

    def search_patients(self, disease: str = "", hpo_terms: List[str] = None,
                       limit: int = 100) -> List[Dict]:
        """搜索患者"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if disease:
                rows = conn.execute(
                    "SELECT * FROM registry_patients WHERE disease LIKE ? LIMIT ?",
                    (f"%{disease}%", limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM registry_patients LIMIT ?", (limit,)
                ).fetchall()
            
            results = []
            for row in rows:
                d = dict(row)
                d["hpo_phenotypes"] = json.loads(d.get("hpo_phenotypes") or "[]")
                d["gene_variants"] = json.loads(d.get("gene_variants") or "[]")
                results.append(d)
            return results

    def create_cohort(self, name: str, disease: str, criteria: str = "") -> Dict:
        """创建队列"""
        cohort_id = f"cohort_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO cohorts VALUES (?, ?, ?, ?, 0, ?)",
                (cohort_id, name, disease, criteria, now)
            )

        return {"cohort_id": cohort_id, "name": name, "disease": disease}

    def add_to_cohort(self, cohort_id: str, registry_id: str):
        """添加患者到队列"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO cohort_patients VALUES (?, ?, ?)",
                (cohort_id, registry_id, now)
            )
            conn.execute(
                "UPDATE cohorts SET patient_count = patient_count + 1 WHERE cohort_id = ?",
                (cohort_id,)
            )

    def get_cohort_patients(self, cohort_id: str) -> List[Dict]:
        """获取队列中的患者"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT p.* FROM registry_patients p
                JOIN cp ON p.registry_id = cp.registry_id
                WHERE cp.cohort_id = ?
            """, (cohort_id,)).fetchall()
            return [dict(r) for r in rows]

    def export_phenopackets(self, cohort_id: str = None) -> List[Dict]:
        """导出GA4GH Phenopacket格式"""
        patients = []
        if cohort_id:
            patients = self.get_cohort_patients(cohort_id)
        else:
            patients = self.search_patients(limit=1000)

        phenopackets = []
        for p in patients:
            pp = {
                "id": p.get("registry_id", ""),
                "subject": {"id": p.get("patient_code", "")},
                "phenotypic_features": [
                    {"type": {"label": hp}, "observed": True}
                    for hp in p.get("hpo_phenotypes", [])
                ],
                "diseases": [
                    {"term": {"label": p.get("disease", "")}}
                ],
                "meta_data": {
                    "created": p.get("created_at", ""),
                    "created_by": "MediChat-RD",
                    "phenopacket_schema_version": "2.0",
                },
            }
            phenopackets.append(pp)

        return phenopackets

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM registry_patients").fetchone()[0]
            diseases = conn.execute(
                "SELECT disease, COUNT(*) as cnt FROM registry_patients GROUP BY disease ORDER BY cnt DESC"
            ).fetchall()
            cohorts = conn.execute("SELECT COUNT(*) FROM cohorts").fetchone()[0]
            
            return {
                "total_patients": total,
                "total_cohorts": cohorts,
                "disease_distribution": {d[0]: d[1] for d in diseases},
            }


# ========== 测试 ==========
if __name__ == "__main__":
    registry = PatientRegistry("/tmp/test_registry.db")
    
    print("=" * 60)
    print("📋 罕见病患者注册系统测试")
    print("=" * 60)
    
    # 登记患者
    p1 = registry.register_patient(
        disease="重症肌无力",
        hpo_phenotypes=["眼睑下垂", "吞咽困难", "全身无力"],
        gene_variants=[{"gene": "CHRNE", "variant": "c.130C>T"}],
        gender="female", age_of_onset=35,
        consent_research=True, consent_matching=True,
    )
    print(f"\n✅ 患者登记: {p1['patient_code']}")
    
    p2 = registry.register_patient(
        disease="戈谢病",
        hpo_phenotypes=["肝脾肿大", "贫血", "血小板减少"],
        gender="male", age_of_onset=10,
    )
    print(f"✅ 患者登记: {p2['patient_code']}")
    
    # 创建队列
    cohort = registry.create_cohort("MG队列", "重症肌无力", "确诊MG患者")
    print(f"\n📊 创建队列: {cohort['name']}")
    
    # 添加到队列
    registry.add_to_cohort(cohort["cohort_id"], p1["registry_id"])
    
    # 搜索
    results = registry.search_patients(disease="重症肌无力")
    print(f"\n🔍 搜索结果: {len(results)}个患者")
    
    # 统计
    stats = registry.get_stats()
    print(f"\n📊 统计:")
    print(f"   总患者数: {stats['total_patients']}")
    print(f"   队列数: {stats['total_cohorts']}")
    print(f"   疾病分布: {stats['disease_distribution']}")
    
    # 导出Phenopacket
    pp = registry.export_phenopackets()
    print(f"\n📋 导出Phenopacket: {len(pp)}个")
