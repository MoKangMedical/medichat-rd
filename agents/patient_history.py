"""
MediChat-RD — 患者病例持久化
参考OrphaMind：SQLite存储诊断历史+病例管理
"""
import json
import sqlite3
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class PatientHistory:
    """患者诊断历史管理"""

    def __init__(self, db_path: str = "data/patient_history.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    nickname TEXT,
                    age INTEGER,
                    gender TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS diagnoses (
                    diagnosis_id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    session_id TEXT,
                    symptoms TEXT,
                    phenotype_extracted TEXT,
                    differential_diagnosis TEXT,
                    lab_results TEXT,
                    conclusion TEXT,
                    critical_alerts TEXT,
                    created_at TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clinical_notes (
                    note_id TEXT PRIMARY KEY,
                    patient_id TEXT,
                    note_text TEXT,
                    note_type TEXT DEFAULT 'visit',
                    created_at TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_diagnoses_patient ON diagnoses(patient_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_diagnoses_created ON diagnoses(created_at)
            """)

    def create_patient(self, nickname: str, age: Optional[int] = None, gender: Optional[str] = None) -> str:
        """创建新患者"""
        patient_id = f"p_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?)",
                (patient_id, nickname, age, gender, now, now)
            )
        return patient_id

    def save_diagnosis(self, patient_id: str, session_id: str, result: Dict) -> str:
        """保存诊断结果"""
        diagnosis_id = f"dx_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        stages = result.get("stages", {})
        symptoms = json.dumps(stages.get("symptoms", {}), ensure_ascii=False)
        phenotypes = json.dumps(stages.get("symptoms", {}).get("extracted_phenotypes", []), ensure_ascii=False)
        differential = json.dumps(stages.get("analysis", {}).get("differential_diagnosis", []), ensure_ascii=False)
        lab_results = json.dumps(stages.get("analysis", {}).get("lab_results", {}), ensure_ascii=False)
        conclusion = stages.get("analysis", {}).get("conclusion", "")
        critical_alerts = json.dumps(stages.get("analysis", {}).get("critical_alerts", []), ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO diagnoses VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (diagnosis_id, patient_id, session_id, symptoms, phenotypes,
                 differential, lab_results, conclusion, critical_alerts, now)
            )
            conn.execute(
                "UPDATE patients SET updated_at = ? WHERE patient_id = ?",
                (now, patient_id)
            )

        return diagnosis_id

    def save_clinical_note(self, patient_id: str, note_text: str, note_type: str = "visit") -> str:
        """保存临床笔记"""
        note_id = f"note_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO clinical_notes VALUES (?, ?, ?, ?, ?)",
                (note_id, patient_id, note_text, note_type, now)
            )
        return note_id

    def get_patient(self, patient_id: str) -> Optional[Dict]:
        """获取患者信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
            if row:
                return dict(row)
        return None

    def get_diagnoses(self, patient_id: str, limit: int = 20) -> List[Dict]:
        """获取患者诊断历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM diagnoses WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
                (patient_id, limit)
            ).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                # 解析JSON字段
                for field in ["phenotype_extracted", "differential_diagnosis", "lab_results", "critical_alerts"]:
                    if d.get(field):
                        try:
                            d[field] = json.loads(d[field])
                        except:
                            pass
                results.append(d)
            return results

    def search_patients(self, query: str = "", limit: int = 50) -> List[Dict]:
        """搜索患者"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if query:
                rows = conn.execute(
                    "SELECT * FROM patients WHERE nickname LIKE ? ORDER BY updated_at DESC LIMIT ?",
                    (f"%{query}%", limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM patients ORDER BY updated_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            diagnoses = conn.execute("SELECT COUNT(*) FROM diagnoses").fetchone()[0]
            notes = conn.execute("SELECT COUNT(*) FROM clinical_notes").fetchone()[0]
            return {
                "total_patients": patients,
                "total_diagnoses": diagnoses,
                "total_notes": notes,
            }


# ========== 测试 ==========
if __name__ == "__main__":
    history = PatientHistory("/tmp/test_history.db")

    # 创建患者
    pid = history.create_patient("张女士", 35, "female")
    print(f"创建患者: {pid}")

    # 保存诊断
    fake_result = {
        "stages": {
            "symptoms": {"extracted_phenotypes": [{"hpo_id": "HP:0000508", "name": "Ptosis"}]},
            "analysis": {
                "differential_diagnosis": [{"disease": "重症肌无力", "score": 95}],
                "lab_results": {"total": 3},
                "conclusion": "高度怀疑重症肌无力",
                "critical_alerts": ["🔴 肌钙蛋白危急值"],
            }
        }
    }
    dx_id = history.save_diagnosis(pid, "sess_001", fake_result)
    print(f"保存诊断: {dx_id}")

    # 保存临床笔记
    note_id = history.save_clinical_note(pid, "患者主诉眼睑下垂3个月")
    print(f"保存笔记: {note_id}")

    # 查询
    print(f"\n📊 统计: {history.get_stats()}")
    print(f"👤 患者: {history.get_patient(pid)['nickname']}")
    print(f"📋 诊断历史: {len(history.get_diagnoses(pid))}条")
