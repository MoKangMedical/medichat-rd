"""MediChat-RD 药企付费模式 — 数据模型 (SQLite)"""
import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "pharma_b2b.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS pharma_company (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, plan TEXT DEFAULT 'basic',
        api_key TEXT UNIQUE, created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS patient (
        id INTEGER PRIMARY KEY, patient_id TEXT UNIQUE, company_id INTEGER,
        disease TEXT, medication TEXT, adherence_score REAL DEFAULT 0,
        risk_level TEXT DEFAULT 'medium', last_interaction TEXT,
        wechat_openid TEXT, created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS adherence_record (
        id INTEGER PRIMARY KEY, patient_id TEXT, date TEXT,
        took_medication INTEGER DEFAULT 0, side_effects TEXT,
        ai_interaction TEXT, score_delta REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS education_content (
        id INTEGER PRIMARY KEY, title TEXT, category TEXT, disease TEXT,
        content_text TEXT, company_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS interaction_log (
        id INTEGER PRIMARY KEY, patient_id TEXT, channel TEXT DEFAULT 'wechat',
        message_type TEXT, content TEXT, ai_response TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()

def seed_demo_data():
    conn = get_db()
    c = conn.cursor()
    if c.execute("SELECT COUNT(*) FROM pharma_company").fetchone()[0] > 0:
        conn.close()
        return

    companies = [
        ("辉瑞罕见病事业部", "pro", "pfizer_rd_2026"),
        ("诺华基因治疗部", "standard", "novas_gene_2026"),
        ("罗氏神经科学", "basic", "roche_neuro_2026"),
    ]
    for name, plan, key in companies:
        c.execute("INSERT INTO pharma_company(name,plan,api_key) VALUES(?,?,?)", (name, plan, key))

    diseases = [
        ("庞贝病", "阿糖苷酶α"), ("法布雷病", "阿加糖酶α"), ("戈谢病", "伊米苷酶"),
        ("脊髓性肌萎缩症", "诺西那生钠"), ("杜氏肌营养不良", "地夫可特"),
    ]
    for i in range(50):
        d = diseases[i % len(diseases)]
        cid = (i % 3) + 1
        score = round(random.uniform(35, 98), 1)
        risk = "low" if score >= 80 else ("medium" if score >= 60 else "high")
        pid = f"RD{str(i+1).zfill(4)}"
        last = (datetime.now() - timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d %H:%M")
        c.execute("""INSERT INTO patient(patient_id,company_id,disease,medication,adherence_score,risk_level,last_interaction)
                     VALUES(?,?,?,?,?,?,?)""", (pid, cid, d[0], d[1], score, risk, last))

    contents = [
        ("庞贝病用药指导", "medication", "庞贝病", "阿糖苷酶α每两周静脉输注一次，请提前预约输注中心。"),
        ("法布雷病日常管理", "lifestyle", "法布雷病", "避免剧烈运动，保持规律作息，定期监测肾功能。"),
        ("SMA康复训练", "rehab", "脊髓性肌萎缩症", "每日进行30分钟物理治疗，重点关注呼吸功能训练。"),
        ("药物副作用应对", "side_effects", "通用", "如出现过敏反应，请立即联系主治医师并暂停用药。"),
        ("复查提醒模板", "reminder", "通用", "您的定期复查时间即将到来，请提前预约相关检查。"),
    ]
    for t, cat, dis, txt in contents:
        c.execute("INSERT INTO education_content(title,category,disease,content_text,company_id) VALUES(?,?,?,?,1)", (t, cat, dis, txt))

    for i in range(50):
        pid = f"RD{str(i+1).zfill(4)}"
        for d in range(30):
            date = (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
            took = 1 if random.random() > 0.2 else 0
            se = random.choice(["无", "轻微头痛", "疲劳", "注射部位红肿", "无", "无"])
            delta = round(random.uniform(-2, 3), 1) if took else round(random.uniform(-5, -1), 1)
            c.execute("INSERT INTO adherence_record(patient_id,date,took_medication,side_effects,score_delta) VALUES(?,?,?,?,?)",
                      (pid, date, took, se, delta))

    conn.commit()
    conn.close()
    print("Demo data seeded: 3 companies, 50 patients, 1500+ records")
