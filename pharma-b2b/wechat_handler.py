"""微信消息处理器 — 模拟患者交互"""
from models import get_db
from datetime import datetime

RESPONSES = {
    "忘吃药": "⚠️ 检测到您可能漏服了药物。\n\n📋 处理建议：\n1. 如果距离下次服药时间 > 12小时，请立即补服\n2. 如果 < 12小时，请跳过这次，按原计划服药\n3. 不要一次服用双倍剂量\n\n如需进一步指导，请回复「联系医生」。",
    "副作用": "🔍 我理解您可能出现了不适反应。\n\n请告诉我具体症状：\n1. 头痛/头晕\n2. 恶心/呕吐\n3. 注射部位反应\n4. 过敏反应（皮疹/呼吸困难）\n5. 其他\n\n⚠️ 如出现严重过敏反应（呼吸困难/面部肿胀），请立即拨打120！",
    "复查": "📅 复查提醒\n\n根据您的治疗方案，建议定期复查以下项目：\n• 血常规\n• 肝肾功能\n• 疾病特异性指标\n\n建议每3个月复查一次。如需帮助预约，请回复「预约」。",
    "用药": "💊 用药指导\n\n请遵循以下原则：\n1. 按时按量服药\n2. 不要自行调整剂量\n3. 避免与其他药物同时服用（除非医生建议）\n4. 定期监测药物浓度\n\n如需了解具体药物信息，请告诉我您的用药名称。",
    "default": "您好！我是MediChat-RD健康助手 🤖\n\n我可以帮助您：\n• 💊 用药指导和提醒\n• ⚠️ 副作用应对建议\n• 📅 复查提醒\n• 📚 疾病知识科普\n• 👨‍⚕️ 紧急情况指引\n\n请告诉我您需要什么帮助？"
}

def simulate_patient_message(patient_id, message):
    db = get_db()
    patient = db.execute("SELECT * FROM patient WHERE patient_id=?", (patient_id,)).fetchone()
    if not patient:
        return {"error": "Patient not found"}

    response = RESPONSES["default"]
    for key in RESPONSES:
        if key in message:
            response = RESPONSES[key]
            break

    db.execute("UPDATE patient SET last_interaction=? WHERE patient_id=?",
               (datetime.now().strftime("%Y-%m-%d %H:%M"), patient_id))
    db.execute("INSERT INTO interaction_log(patient_id,message_type,content,ai_response) VALUES(?,?,?,?)",
               (patient_id, "inquiry", message, response))
    db.commit()
    db.close()
    return {
        "patient_id": patient_id,
        "patient_disease": patient["disease"],
        "medication": patient["medication"],
        "message": message,
        "ai_response": response,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
