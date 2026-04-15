"""
MediChat-RD — 罕见病患者注册系统
参考PhenoTips + RDRF：患者登记+队列管理+数据导出
"""
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
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
            # 长期管理计划
            conn.execute("""
                CREATE TABLE IF NOT EXISTS care_plans (
                    registry_id TEXT PRIMARY KEY,
                    plan_json TEXT,
                    updated_at TEXT
                )
            """)
            # 病程时间线
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patient_timeline (
                    event_id TEXT PRIMARY KEY,
                    registry_id TEXT,
                    event_type TEXT,
                    title TEXT,
                    detail TEXT,
                    source TEXT,
                    payload_json TEXT,
                    created_at TEXT
                )
            """)

    def _deserialize_patient(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        data["hpo_phenotypes"] = json.loads(data.get("hpo_phenotypes") or "[]")
        data["gene_variants"] = json.loads(data.get("gene_variants") or "[]")
        data["consent_research"] = bool(data.get("consent_research"))
        data["consent_matching"] = bool(data.get("consent_matching"))
        return data

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

        self.add_timeline_event(
            registry_id=registry_id,
            event_type="registry_enrollment",
            title=f"登记进入 {disease} 患者库",
            detail=f"患者对象已创建，包含 {len(hpo_phenotypes)} 个表型和 {len(gene_variants or [])} 条变异线索。",
            source="registry",
            payload={
                "diagnosis_status": kwargs.get("diagnosis_status", "confirmed"),
                "consent_research": bool(kwargs.get("consent_research")),
                "consent_matching": bool(kwargs.get("consent_matching")),
            },
        )

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
                results.append(self._deserialize_patient(row))
            return results

    def get_patient(self, registry_id: str) -> Optional[Dict]:
        """获取单个登记患者"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM registry_patients WHERE registry_id = ?",
                (registry_id,),
            ).fetchone()
            return self._deserialize_patient(row) if row else None

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
            cursor = conn.execute(
                "INSERT OR IGNORE INTO cohort_patients VALUES (?, ?, ?)",
                (cohort_id, registry_id, now)
            )
            if cursor.rowcount:
                conn.execute(
                    "UPDATE cohorts SET patient_count = patient_count + 1 WHERE cohort_id = ?",
                    (cohort_id,)
                )

        self.add_timeline_event(
            registry_id=registry_id,
            event_type="cohort_assignment",
            title=f"加入研究队列 {cohort_id}",
            detail="病例对象已进入 cohort 管理，可用于研究准备和标准导出。",
            source="registry",
            payload={"cohort_id": cohort_id},
        )

    def list_cohorts(self, disease: str = "", limit: int = 100) -> List[Dict]:
        """列出队列"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if disease:
                rows = conn.execute(
                    "SELECT * FROM cohorts WHERE disease LIKE ? ORDER BY created_at DESC LIMIT ?",
                    (f"%{disease}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM cohorts ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]

    def get_cohort_patients(self, cohort_id: str) -> List[Dict]:
        """获取队列中的患者"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT p.* FROM registry_patients p
                JOIN cohort_patients cp ON p.registry_id = cp.registry_id
                WHERE cp.cohort_id = ?
            """, (cohort_id,)).fetchall()
            return [self._deserialize_patient(r) for r in rows]

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

    def update_care_plan(self, registry_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """写入或更新长期管理计划"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO care_plans (registry_id, plan_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(registry_id) DO UPDATE SET
                    plan_json = excluded.plan_json,
                    updated_at = excluded.updated_at
                """,
                (registry_id, json.dumps(plan, ensure_ascii=False), now),
            )
        return {"registry_id": registry_id, "updated_at": now, "plan": plan}

    def get_care_plan(self, registry_id: str) -> Optional[Dict[str, Any]]:
        """读取长期管理计划"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT plan_json, updated_at FROM care_plans WHERE registry_id = ?",
                (registry_id,),
            ).fetchone()
            if not row:
                return None
            plan = json.loads(row[0] or "{}")
            plan["updated_at"] = row[1]
            return plan

    def add_timeline_event(
        self,
        registry_id: str,
        event_type: str,
        title: str,
        detail: str = "",
        source: str = "platform",
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """追加病程时间线事件"""
        event_id = f"evt_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO patient_timeline
                (event_id, registry_id, event_type, title, detail, source, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    registry_id,
                    event_type,
                    title,
                    detail,
                    source,
                    json.dumps(payload or {}, ensure_ascii=False),
                    now,
                ),
            )
        return {
            "event_id": event_id,
            "registry_id": registry_id,
            "event_type": event_type,
            "title": title,
            "detail": detail,
            "source": source,
            "payload": payload or {},
            "created_at": now,
        }

    def get_patient_timeline(self, registry_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取患者时间线"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM patient_timeline
                WHERE registry_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (registry_id, limit),
            ).fetchall()
            events = []
            for row in rows:
                item = dict(row)
                item["payload"] = json.loads(item.get("payload_json") or "{}")
                item.pop("payload_json", None)
                events.append(item)
            return events

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM registry_patients").fetchone()[0]
            diseases = conn.execute(
                "SELECT disease, COUNT(*) as cnt FROM registry_patients GROUP BY disease ORDER BY cnt DESC"
            ).fetchall()
            cohorts = conn.execute("SELECT COUNT(*) FROM cohorts").fetchone()[0]
            care_plans = conn.execute("SELECT COUNT(*) FROM care_plans").fetchone()[0]
            timeline_events = conn.execute("SELECT COUNT(*) FROM patient_timeline").fetchone()[0]
            
            return {
                "total_patients": total,
                "total_cohorts": cohorts,
                "care_plans": care_plans,
                "timeline_events": timeline_events,
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
