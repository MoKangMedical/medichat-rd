"""MediChat-RD 药企付费MVP — 主应用"""
from flask import Flask, render_template, jsonify, request
from models import init_db, seed_demo_data, get_db
from adherence_engine import get_dashboard_stats, get_patient_list, get_adherence_trend, calculate_roi
from wechat_handler import simulate_patient_message

app = Flask(__name__)

@app.before_request
def setup():
    if not hasattr(app, '_initialized'):
        init_db()
        seed_demo_data()
        app._initialized = True

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(get_dashboard_stats())

@app.route("/api/patients")
def api_patients():
    risk = request.args.get("risk", "")
    return jsonify(get_patient_list(risk_filter=risk))

@app.route("/api/trend")
def api_trend():
    days = int(request.args.get("days", 30))
    return jsonify(get_adherence_trend(days))

@app.route("/api/roi")
def api_roi():
    return jsonify(calculate_roi())

@app.route("/api/wechat/simulate", methods=["POST"])
def api_wechat_simulate():
    data = request.json
    patient_id = data.get("patient_id", "RD0001")
    message = data.get("message", "我今天忘了吃药怎么办")
    return jsonify(simulate_patient_message(patient_id, message))

@app.route("/api/content")
def api_content():
    conn = get_db()
    rows = conn.execute("SELECT * FROM education_content").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

@app.route("/patient")
def patient():
    return render_template("patient_h5.html")
