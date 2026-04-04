"""
MediChat-RD 轻量级远程医疗平台（Medvi模式中国版）
极简架构：只做AI+流量层，医疗合规外包
"""
import os
import json
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

# ========== 配置 ==========
class Config:
    APP_NAME = "MediChat-RD 轻诊平台"
    VERSION = "1.0.0"
    DATA_DIR = Path("./data")
    PARTNER_HOSPITALS = [
        {"id": "h001", "name": "北京协和医院", "specialties": ["神经内科", "罕见病"], "license": "互联网医院牌照A"},
        {"id": "h002", "name": "上海华山医院", "specialties": ["神经内科", "遗传科"], "license": "互联网医院牌照B"},
        {"id": "h003", "name": "广州中山一院", "specialties": ["罕见病中心"], "license": "互联网医院牌照C"},
    ]
    SUPPORTED_DISEASES = {
        "MG": {"name": "重症肌无力", "icd10": "G70.0", "specialty": "神经内科"},
        "SMA": {"name": "脊髓性肌萎缩症", "icd10": "G12.0", "specialty": "神经内科"},
        "DMD": {"name": "杜氏肌营养不良", "icd10": "G71.0", "specialty": "神经内科"},
        "ALS": {"name": "肌萎缩侧索硬化", "icd10": "G12.2", "specialty": "神经内科"},
        "PKU": {"name": "苯丙酮尿症", "icd10": "E70.0", "specialty": "遗传科"},
    }

# ========== 数据模型 ==========
class Patient:
    def __init__(self, phone, name=None, wechat_openid=None):
        self.id = str(uuid.uuid4())[:12]
        self.phone = phone
        self.name = name or ""
        self.wechat_openid = wechat_openid
        self.created_at = datetime.now().isoformat()
        self.assessments = []
        self.consultations = []

    def to_dict(self):
        return vars(self)

class Assessment:
    """AI健康评估"""
    def __init__(self, patient_id, disease_type):
        self.id = str(uuid.uuid4())[:12]
        self.patient_id = patient_id
        self.disease_type = disease_type
        self.status = "pending"
        self.questions = []
        self.answers = {}
        self.ai_analysis = None
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return vars(self)

class Consultation:
    """远程问诊"""
    def __init__(self, patient_id, hospital_id, disease_type):
        self.id = str(uuid.uuid4())[:12]
        self.patient_id = patient_id
        self.hospital_id = hospital_id
        self.disease_type = disease_type
        self.status = "waiting_doctor"
        self.doctor_id = None
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return vars(self)

# ========== AI引擎 ==========
class AIEngine:
    """AI诊疗引擎（基于MIMO API）"""
    
    DISEASE_QUESTIONS = {
        "MG": [
            "您是否有眼睑下垂的症状？",
            "是否有吞咽困难或咀嚼费力？",
            "是否有四肢无力，尤其是下午或劳累后加重？",
            "是否有说话不清或声音嘶哑？",
            "症状首次出现是什么时候？",
            "是否有胸腺异常（胸腺瘤/胸腺增生）？",
            "是否做过乙酰胆碱受体抗体检测？",
            "目前是否在服用溴吡斯的明等胆碱酯酶抑制剂？",
        ],
        "SMA": [
            "患者目前的运动能力如何？（独坐/扶站/独走）",
            "是否有肌张力低下？",
            "是否有脊柱侧弯？",
            "是否做过SMN1基因检测？",
            "SMN2拷贝数是多少？",
            "目前是否在使用诺西那生钠或利司扑兰？",
        ],
        "DMD": [
            "患者是否出现Gowers征（用手撑腿站起）？",
            "小腿是否有假性肥大？",
            "目前是否能独立行走？",
            "是否做过DMD基因检测（缺失/重复/点突变）？",
            "是否在使用糖皮质激素？",
            "最近一次心功能检查是什么时候？",
        ],
        "ALS": [
            "首发症状是肢体无力还是言语不清？",
            "是否有肌束震颤（肉跳）？",
            "是否有吞咽困难？",
            "是否做过肌电图？",
            "是否有家族史？",
            "目前是否在使用利鲁唑？",
        ],
        "PKU": [
            "患者是经典型还是BH4缺乏型？",
            "目前血苯丙氨酸浓度是多少？",
            "是否在坚持特殊饮食？",
            "是否有智力发育迟缓？",
            "是否做过PAH基因检测？",
            "是否在使用BH4（沙丙蝶呤）？",
        ],
    }
    
    @classmethod
    def generate_assessment(cls, disease_type):
        """生成评估问卷"""
        questions = cls.DISEASE_QUESTIONS.get(disease_type, [])
        return [
            {"id": i+1, "text": q, "type": "choice" if i < 4 else "text", 
             "options": ["是", "否", "不确定"] if i < 4 else None}
            for i, q in enumerate(questions)
        ]
    
    @classmethod
    def analyze(cls, disease_type, answers):
        """AI分析评估结果"""
        positive_count = sum(1 for v in answers.values() if v == "是")
        total = len(answers)
        risk_score = round(positive_count / max(total, 1) * 100, 1)
        
        disease_info = Config.SUPPORTED_DISEASES.get(disease_type, {})
        
        # 风险分级
        if risk_score >= 70:
            risk_level = "高"
            recommendation = "建议尽快安排专科医生远程问诊"
            urgency = "urgent"
        elif risk_score >= 40:
            risk_level = "中"
            recommendation = "建议预约专科医生进行进一步评估"
            urgency = "normal"
        else:
            risk_level = "低"
            recommendation = "目前症状不典型，建议持续观察，如有变化及时就诊"
            urgency = "monitor"
        
        return {
            "disease": disease_info.get("name", disease_type),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "positive_symptoms": positive_count,
            "total_questions": total,
            "recommendation": recommendation,
            "urgency": urgency,
            "specialty": disease_info.get("specialty", "神经内科"),
            "ai_model": "MIMO-API (MediChat-RD)",
            "analyzed_at": datetime.now().isoformat(),
        }
    
    @classmethod
    def match_hospital(cls, disease_type, urgency):
        """匹配合作医院"""
        disease_info = Config.SUPPORTED_DISEASES.get(disease_type, {})
        specialty = disease_info.get("specialty", "神经内科")
        
        matched = [
            h for h in Config.PARTNER_HOSPITALS 
            if specialty in h["specialties"] or "罕见病" in h["specialties"]
        ]
        
        if not matched:
            matched = Config.PARTNER_HOSPITALS[:2]
        
        return matched[0] if matched else None

# ========== 平台核心 ==========
class MedviStylePlatform:
    """轻量级远程医疗平台"""
    
    def __init__(self, config=None):
        self.config = config or Config()
        self.config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.patients = {}
        self.assessments = {}
        self.consultations = {}
    
    def register_patient(self, phone, name=None, wechat_openid=None):
        """患者注册"""
        patient = Patient(phone, name, wechat_openid)
        self.patients[patient.id] = patient
        return patient.to_dict()
    
    def start_assessment(self, patient_id, disease_type):
        """开始AI健康评估"""
        if disease_type not in self.config.SUPPORTED_DISEASES:
            return {"error": f"不支持的病种: {disease_type}"}
        
        assessment = Assessment(patient_id, disease_type)
        assessment.questions = AIEngine.generate_assessment(disease_type)
        self.assessments[assessment.id] = assessment
        return {
            "assessment_id": assessment.id,
            "disease": self.config.SUPPORTED_DISEASES[disease_type]["name"],
            "questions": assessment.questions,
            "total": len(assessment.questions),
        }
    
    def submit_assessment(self, assessment_id, answers):
        """提交评估答案"""
        assessment = self.assessments.get(assessment_id)
        if not assessment:
            return {"error": "评估不存在"}
        
        assessment.answers = answers
        assessment.status = "completed"
        assessment.ai_analysis = AIEngine.analyze(assessment.disease_type, answers)
        
        # 自动匹配医院
        hospital = AIEngine.match_hospital(
            assessment.disease_type, 
            assessment.ai_analysis["urgency"]
        )
        
        return {
            "assessment_id": assessment_id,
            "analysis": assessment.ai_analysis,
            "matched_hospital": hospital,
            "next_step": "consultation" if assessment.ai_analysis["urgency"] != "monitor" else "monitor",
        }
    
    def create_consultation(self, assessment_id):
        """创建远程问诊"""
        assessment = self.assessments.get(assessment_id)
        if not assessment or assessment.status != "completed":
            return {"error": "请先完成评估"}
        
        hospital = AIEngine.match_hospital(
            assessment.disease_type,
            assessment.ai_analysis["urgency"]
        )
        
        consultation = Consultation(
            assessment.patient_id,
            hospital["id"],
            assessment.disease_type
        )
        self.consultations[consultation.id] = consultation
        
        # 模拟医生接诊（实际对接互联网医院API）
        consultation.doctor_id = f"doc_{hospital['id']}_001"
        consultation.status = "in_progress"
        
        return {
            "consultation_id": consultation.id,
            "hospital": hospital,
            "doctor_assigned": True,
            "status": "in_progress",
            "estimated_wait": "15分钟内",
        }
    
    def get_platform_stats(self):
        """平台统计"""
        return {
            "total_patients": len(self.patients),
            "total_assessments": len(self.assessments),
            "total_consultations": len(self.consultations),
            "disease_breakdown": {
                disease: sum(1 for a in self.assessments.values() if a.disease_type == disease)
                for disease in self.config.SUPPORTED_DISEASES
            },
            "supported_diseases": len(self.config.SUPPORTED_DISEASES),
            "partner_hospitals": len(self.config.PARTNER_HOSPITALS),
        }

# ========== Web API ==========
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

class MedviAPIHandler(SimpleHTTPRequestHandler):
    """轻量级API服务器"""
    platform = MedviStylePlatform()
    
    def do_GET(self):
        path = self.path.split("?")[0]
        
        if path == "/" or path == "/index.html":
            self._serve_file("templates/index.html", "text/html; charset=utf-8")
        elif path.startswith("/static/"):
            self._serve_file(path[1:], "text/css" if path.endswith(".css") else "application/javascript")
        elif path == "/api/diseases":
            self._json_response(Config.SUPPORTED_DISEASES)
        elif path == "/api/hospitals":
            self._json_response(Config.PARTNER_HOSPITALS)
        elif path == "/api/stats":
            self._json_response(self.platform.get_platform_stats())
        else:
            self._json_response({"error": "Not found"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        path = self.path
        
        if path == "/api/register":
            result = self.platform.register_patient(
                data.get("phone", ""),
                data.get("name"),
                data.get("wechat_openid")
            )
            self._json_response(result)
        
        elif path == "/api/assessment/start":
            result = self.platform.start_assessment(
                data.get("patient_id", ""),
                data.get("disease_type", "")
            )
            self._json_response(result)
        
        elif path == "/api/assessment/submit":
            result = self.platform.submit_assessment(
                data.get("assessment_id", ""),
                data.get("answers", {})
            )
            self._json_response(result)
        
        elif path == "/api/consultation/create":
            result = self.platform.create_consultation(
                data.get("assessment_id", "")
            )
            self._json_response(result)
        
        else:
            self._json_response({"error": "Not found"}, 404)
    
    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    
    def _serve_file(self, filepath, content_type):
        full_path = Path(__file__).parent / filepath
        if full_path.exists():
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(full_path.read_bytes())
        else:
            self._json_response({"error": f"File not found: {filepath}"}, 404)
    
    def log_message(self, format, *args):
        pass  # 静默日志

# ========== 启动 ==========
def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), MedviAPIHandler)
    print(f"🏥 MediChat-RD 轻诊平台启动成功")
    print(f"📱 访问地址: http://localhost:{port}")
    print(f"🔗 API文档: http://localhost:{port}/api/stats")
    server.serve_forever()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    run_server(port)
