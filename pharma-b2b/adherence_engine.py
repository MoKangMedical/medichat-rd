"""依从性引擎 — 评分/统计/ROI"""
from models import get_db
from datetime import datetime, timedelta

def get_dashboard_stats():
    db = get_db()
    total_patients = db.execute("SELECT COUNT(*) FROM patient").fetchone()[0]
    avg_score = db.execute("SELECT ROUND(AVG(adherence_score),1) FROM patient").fetchone()[0] or 0
    high_risk = db.execute("SELECT COUNT(*) FROM patient WHERE risk_level='high'").fetchone()[0]
    interactions_30d = db.execute(
        "SELECT COUNT(*) FROM interaction_log WHERE created_at > datetime('now','-30 days')"
    ).fetchone()[0]
    coverage = db.execute(
        "SELECT ROUND(100.0*COUNT(DISTINCT patient_id)/(SELECT COUNT(*) FROM patient),1) FROM adherence_record WHERE date > date('now','-7 days')"
    ).fetchone()[0] or 0
    companies = db.execute("SELECT COUNT(*) FROM pharma_company").fetchone()[0]
    db.close()
    return {
        "total_patients": total_patients,
        "avg_adherence": avg_score,
        "high_risk_count": high_risk,
        "interactions_30d": interactions_30d,
        "education_coverage": coverage,
        "active_companies": companies,
        "estimated_revenue_saved": int(total_patients * avg_score * 12.5)
    }

def get_patient_list(risk_filter=""):
    db = get_db()
    if risk_filter:
        rows = db.execute("SELECT * FROM patient WHERE risk_level=? ORDER BY adherence_score", (risk_filter,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM patient ORDER BY adherence_score").fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_adherence_trend(days=30):
    db = get_db()
    rows = db.execute("""
        SELECT date,
               ROUND(AVG(CASE WHEN took_medication=1 THEN 100 ELSE 0 END),1) as take_rate,
               COUNT(*) as records,
               SUM(CASE WHEN took_medication=1 THEN 1 ELSE 0 END) as taken
        FROM adherence_record
        WHERE date > date('now', ? || ' days')
        GROUP BY date ORDER BY date
    """, (f"-{days}",)).fetchall()
    db.close()
    return [dict(r) for r in rows]

def calculate_roi():
    db = get_db()
    patients = db.execute("SELECT COUNT(*) as cnt, AVG(adherence_score) as avg_score FROM patient").fetchone()
    cnt = patients["cnt"] or 50
    avg = patients["avg_score"] or 70
    annual_drug_revenue = 150000
    adherence_improvement = 15
    roi_data = {
        "patient_count": cnt,
        "current_adherence": round(avg, 1),
        "projected_adherence": round(min(avg + adherence_improvement, 98), 1),
        "per_patient_annual_revenue": annual_drug_revenue,
        "improvement_pct": adherence_improvement,
        "additional_revenue": int(cnt * annual_drug_revenue * adherence_improvement / 100),
        "platform_cost": 150000,
        "roi_multiple": round(cnt * annual_drug_revenue * adherence_improvement / 100 / 150000, 1)
    }
    db.close()
    return roi_data
