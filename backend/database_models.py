"""
MediChat-RD 数据库模型设计
PostgreSQL + SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# ============================================================
# 用户相关表
# ============================================================

class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    
    # 用户类型
    user_type = Column(String(20), default='patient')  # patient/doctor/researcher
    
    # 患者特有字段
    gender = Column(String(10))
    birth_date = Column(DateTime)
    blood_type = Column(String(10))
    
    # 患病信息
    diagnosed_diseases = Column(JSON)  # [{"disease_id": 1, "diagnosis_date": "2024-01-01"}]
    family_history = Column(JSON)
    
    # 账户状态
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    consultations = relationship('Consultation', back_populates='user')
    health_records = relationship('HealthRecord', back_populates='user')

class Doctor(Base):
    """医生表"""
    __tablename__ = 'doctors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(50), nullable=False)
    gender = Column(String(10))
    
    # 职业信息
    title = Column(String(50))  # 主治医师/副主任医师/主任医师
    department = Column(String(50))
    hospital = Column(String(100))
    specialty = Column(Text)
    
    # 资质
    license_number = Column(String(50))
    certification = Column(String(100))
    experience_years = Column(Integer)
    
    # AI配置
    is_ai_agent = Column(Boolean, default=False)
    ai_model = Column(String(50))
    personality = Column(Text)
    speaking_style = Column(Text)
    
    # 关联
    consultations = relationship('Consultation', back_populates='doctor')

# ============================================================
# 疾病相关表
# ============================================================

class RareDisease(Base):
    """罕见病表（121种）"""
    __tablename__ = 'rare_diseases'
    
    id = Column(Integer, primary_key=True)
    name_cn = Column(String(100), nullable=False)
    name_en = Column(String(200), nullable=False)
    
    # 分类
    category = Column(String(50))  # 代谢病/神经系统/血液病/...
    subcategory = Column(String(50))
    
    # 编码
    icd10 = Column(String(20))
    icd11 = Column(String(20))
    orphanet_id = Column(String(20))
    omim_id = Column(String(20))
    
    # 遗传信息
    inheritance = Column(String(50))  # 常染色体隐性/显性/...
    genes = Column(JSON)  # [{"gene": "GLA", "role": "致病基因"}]
    
    # 流行病学
    prevalence = Column(String(50))
    prevalence_note = Column(Text)
    
    # 临床表现
    symptoms = Column(JSON)  # [{"symptom": "脾肿大", "frequency": "90%"}]
    age_of_onset = Column(String(50))
    severity = Column(String(20))
    
    # 诊断
    diagnostic_criteria = Column(Text)
    biomarkers = Column(JSON)
    imaging_findings = Column(Text)
    genetic_testing = Column(Text)
    
    # 治疗
    treatment_guidelines = Column(Text)
    approved_drugs = Column(JSON)
    clinical_trials = Column(JSON)
    gene_therapy = Column(Text)
    
    # 医疗资源
    specialist_hospitals = Column(JSON)
    expert_doctors = Column(JSON)
    patient_organizations = Column(JSON)
    
    # 数据来源
    data_sources = Column(JSON)
    last_updated = Column(DateTime, default=datetime.now)
    
    # 关联
    consultations = relationship('Consultation', back_populates='disease')

class Gene(Base):
    """基因表"""
    __tablename__ = 'genes'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    
    # 基因信息
    chromosome = Column(String(10))
    start_position = Column(Integer)
    end_position = Column(Integer)
    
    # 功能
    function = Column(Text)
    associated_diseases = Column(JSON)
    
    # 检测
    testing_methods = Column(JSON)
    reference_labs = Column(JSON)

# ============================================================
# 诊疗相关表
# ============================================================

class Consultation(Base):
    """诊疗记录表"""
    __tablename__ = 'consultations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    disease_id = Column(Integer, ForeignKey('rare_diseases.id'))
    
    # 会话信息
    session_id = Column(String(100))
    consultation_type = Column(String(20))  # initial/followup/emergency
    
    # 诊疗内容
    chief_complaint = Column(Text)
    present_illness = Column(Text)
    past_history = Column(Text)
    family_history = Column(Text)
    
    # 评估
    assessment = Column(Text)
    diagnosis = Column(Text)
    differential_diagnosis = Column(JSON)
    
    # 治疗计划
    treatment_plan = Column(Text)
    medications = Column(JSON)
    follow_up_plan = Column(Text)
    
    # 质量控制
    quality_score = Column(Float)
    needs_review = Column(Boolean, default=False)
    reviewed_by = Column(Integer)
    
    # 状态
    status = Column(String(20), default='active')
    
    # 时间戳
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    
    # 关联
    user = relationship('User', back_populates='consultations')
    doctor = relationship('Doctor', back_populates='consultations')
    disease = relationship('RareDisease', back_populates='consultations')
    messages = relationship('Message', back_populates='consultation')

class Message(Base):
    """消息表"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'))
    
    # 消息内容
    role = Column(String(20))  # user/assistant/system
    content = Column(Text)
    
    # 附件
    attachments = Column(JSON)
    
    # 元数据
    ai_model = Column(String(50))
    confidence_score = Column(Float)
    response_time = Column(Float)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    consultation = relationship('Consultation', back_populates='messages')

# ============================================================
# 药物重定位表
# ============================================================

class DrugRepurposing(Base):
    """药物重定位评估表"""
    __tablename__ = 'drug_repurposing'
    
    id = Column(Integer, primary_key=True)
    
    # 评估对象
    drug_name = Column(String(100), nullable=False)
    disease_id = Column(Integer, ForeignKey('rare_diseases.id'))
    
    # 靶点分析
    drug_targets = Column(JSON)
    disease_targets = Column(JSON)
    target_overlap = Column(JSON)
    
    # 文献证据
    pubmed_references = Column(JSON)
    evidence_summary = Column(Text)
    
    # 评估结果
    confidence_score = Column(Float)
    recommendation = Column(Text)
    risk_assessment = Column(Text)
    
    # 专家审核
    reviewed_by_expert = Column(Boolean, default=False)
    expert_comments = Column(Text)
    
    # 时间戳
    assessed_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ClinicalTrial(Base):
    """临床试验表"""
    __tablename__ = 'clinical_trials'
    
    id = Column(Integer, primary_key=True)
    
    # 试验信息
    trial_id = Column(String(50))  # NCT号
    title = Column(String(500))
    
    # 试验设计
    phase = Column(String(20))
    status = Column(String(50))
    enrollment = Column(Integer)
    
    # 研究对象
    drug_name = Column(String(100))
    disease_id = Column(Integer, ForeignKey('rare_diseases.id'))
    condition = Column(Text)
    
    # 研究详情
    interventions = Column(JSON)
    primary_outcomes = Column(JSON)
    secondary_outcomes = Column(JSON)
    
    # 机构
    sponsor = Column(String(200))
    collaborators = Column(JSON)
    
    # 时间
    start_date = Column(DateTime)
    completion_date = Column(DateTime)
    
    # 联系方式
    contact_info = Column(JSON)

# ============================================================
# 健康档案表
# ============================================================

class HealthRecord(Base):
    """健康档案表"""
    __tablename__ = 'health_records'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # 基本信息
    record_type = Column(String(50))  # lab/imaging/pathology/genetic
    record_date = Column(DateTime)
    
    # 检测结果
    test_name = Column(String(100))
    result_value = Column(String(100))
    reference_range = Column(String(100))
    unit = Column(String(20))
    is_abnormal = Column(Boolean)
    
    # 附件
    attachments = Column(JSON)
    
    # 备注
    notes = Column(Text)
    
    # 关联
    user = relationship('User', back_populates='health_records')

class GeneticTest(Base):
    """基因检测表"""
    __tablename__ = 'genetic_tests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # 检测信息
    test_type = Column(String(50))  # WGS/WES/targeted_panel
    testing_lab = Column(String(100))
    test_date = Column(DateTime)
    
    # 结果
    pathogenic_variants = Column(JSON)
    likely_pathogenic = Column(JSON)
    vus_variants = Column(JSON)  # 意义未明变异
    
    # 解读
    interpretation = Column(Text)
    clinical_significance = Column(Text)
    
    # 建议
    recommendations = Column(Text)
    genetic_counseling = Column(Boolean, default=False)

# ============================================================
# 社区相关表
# ============================================================

class Community(Base):
    """社群表"""
    __tablename__ = 'communities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 分类
    disease_id = Column(Integer, ForeignKey('rare_diseases.id'))
    community_type = Column(String(50))  # patient_family/research/support
    
    # 成员
    member_count = Column(Integer, default=0)
    moderator_id = Column(Integer)
    
    # 设置
    is_public = Column(Boolean, default=True)
    rules = Column(Text)
    
    # 统计
    post_count = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)

class CommunityPost(Base):
    """社群帖子表"""
    __tablename__ = 'community_posts'
    
    id = Column(Integer, primary_key=True)
    community_id = Column(Integer, ForeignKey('communities.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    
    # 内容
    title = Column(String(200))
    content = Column(Text)
    post_type = Column(String(50))  # question/experience/resource/event
    
    # 互动
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # 状态
    is_pinned = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ============================================================
# 数据库初始化
# ============================================================

def init_database(database_url: str = "postgresql://localhost/medichat_rd"):
    """初始化数据库"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """获取数据库会话"""
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    # 测试数据库创建
    print("数据库模型设计完成")
    print("表结构：")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
