"""预置Demo数据"""
import random
from datetime import datetime, timedelta
from models import db, PharmaCompany, Patient, EducationContent, AdherenceRecord

PHARMA = [
    ('辉瑞罕见病事业部', 'enterprise', 'pfizer_rd_2024'),
    ('诺华基因治疗中心', 'pro', 'novas_gtx_2024'),
    ('罗氏神经科学部门', 'basic', 'roche_neuro_2024'),
]
DISEASES = [
    ('庞贝病', '美尔赞（阿糖苷酶α）'),
    ('脊髓性肌萎缩症', '诺西那生钠注射液'),
    ('法布雷病', '阿加糖酶β'),
    ('杜氏肌营养不良', '地夫可特'),
    ('亨廷顿病', '丁苯那嗪'),
    ('高雪病', '伊米苷酶'),
    ('遗传性TTR淀粉样变性', '帕替西兰'),
]
TEMPLATES = [
    ('庞贝病基础知识', 'disease_knowledge', '庞贝病', '庞贝病是一种罕见的遗传性代谢疾病，由于酸性α-葡萄糖苷酶缺乏导致糖原在溶酶体内累积...'),
    ('美尔赞用药指南', 'medication_guide', '庞贝病', '本品需静脉输注，每2周一次。请按时到医院进行治疗，不要自行调整用药间隔。'),
    ('输液反应处理', 'side_effect', '庞贝病', '如出现发热、寒战等输液反应，请立即通知医护人员，不要自行处理。'),
    ('SMA疾病概述', 'disease_knowledge', '脊髓性肌萎缩症', '脊髓性肌萎缩症(SMA)是一种遗传性神经肌肉疾病，特征是脊髓运动神经元退化...'),
    ('诺西那生钠注射须知', 'medication_guide', '脊髓性肌萎缩症', '本品需腰椎穿刺鞘内注射，初始3次负荷剂量后每4月维持一次。'),
    ('法布雷病患者手册', 'disease_knowledge', '法布雷病', '法布雷病是一种X连锁遗传溶酶体贮积病，可累及肾脏、心脏、神经系统...'),
    ('酶替代疗法须知', 'medication_guide', '法布雷病', 'ERT治疗需每2周进行一次静脉输注，输注期间请密切监测过敏反应。'),
    ('DMD日常护理', 'disease_knowledge', '杜氏肌营养不良', '杜氏肌营养不良症的日常管理包括适度康复训练、心肺功能监测、营养支持...'),
    ('地夫可特用药须知', 'medication_guide', '杜氏肌营养不良', '地夫可特需每日口服，请注意监测体重、骨密度等激素相关副作用。'),
    ('亨廷顿病照护指南', 'disease_knowledge', '亨廷顿病', '亨廷顿病是一种常染色体显性遗传神经退行性疾病，目前以对症治疗为主。'),
    ('定期复查时间表', 'followup', '庞贝病', '建议每3个月进行一次心肺功能评估，每6个月进行一次肌力测试。'),
    ('运动功能复查', 'followup', '脊髓性肌萎缩症', '建议每6个月进行一次运动功能评估（HFMSE/CHOP-INTEND评分）。'),
    ('肾功能监测', 'followup', '法布雷病', '建议每3-6个月检查肾功能、尿蛋白和eGFR。'),
    ('副作用自我监测', 'side_effect', '通用', '请记录任何不适症状，包括时间、程度和持续时长，复诊时告知医生。'),
    ('心理健康支持', 'disease_knowledge', '通用', '罕见病患者和家属的心理健康同样重要，如有需要可联系专业心理支持服务。'),
]

def seed_data():
    if PharmaCompany.query.first():
        return
    companies = []
    for name, plan, key in PHARMA:
        c = PharmaCompany(name=name, subscription_plan=plan, api_key=key)
        db.session.add(c)
        companies.append(c)
    db.session.flush()

    for t in TEMPLATES:
        db.session.add(EducationContent(title=t[0], category=t[1], disease=t[2], content_text=t[3]))

    patients = []
    for i in range(50):
        disease, med = random.choice(DISEASES)
        p = Patient(
            patient_id=f'RD{i+1:05d}',
            company_id=random.choice(companies).id,
            disease=disease, medication=med,
            last_interaction=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.session.add(p)
        patients.append(p)
    db.session.flush()

    for p in patients:
        for d in range(30):
            if random.random() < 0.7:
                took = random.random() < 0.85
                db.session.add(AdherenceRecord(
                    patient_id=p.patient_id,
                    date=datetime.now() - timedelta(days=d, hours=random.randint(0, 12)),
                    took_medication=took,
                    side_effects='轻微恶心' if not took and random.random() < 0.5 else None,
                    ai_interaction=random.choice(['询问用药时间','报告轻微不适','确认复查时间','询问饮食注意事项', None])
                ))
    db.session.commit()

    from adherence_engine import calculate_adherence
    for p in patients:
        score, risk = calculate_adherence(AdherenceRecord.query.filter_by(patient_id=p.patient_id).all())
        p.adherence_score = score
        p.risk_level = risk
    db.session.commit()
    print(f'✅ Demo数据: 3药企, 50患者, 15教育模板')
