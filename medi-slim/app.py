"""
MediSlim — 中国版Medvi消费医疗平台
完全复刻Medvi极简架构：只做流量层，医疗合规全外包
技术栈：Python原生HTTP + 微信小程序风格前端
"""
import os
import json
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# ========== 配置 ==========
class Config:
    APP_NAME = "MediSlim 轻健康"
    VERSION = "1.0.0"

    PRODUCTS = {
        "glp1": {
            "name": "GLP-1 科学减重",
            "emoji": "🔥",
            "description": "司美格鲁肽/替尔泊肽，医生指导，科学减重",
            "first_price": 399,
            "renew_price": 599,
            "unit": "月",
            "includes": ["医师评估", "个性化方案", "药品配送", "24h在线支持", "体重管理报告"],
            "requires_prescription": True,
            "category": "减肥",
        },
        "hair": {
            "name": "防脱生发",
            "emoji": "💇",
            "description": "米诺地尔/非那雄胺，专业防脱方案",
            "first_price": 199,
            "renew_price": 299,
            "unit": "月",
            "includes": ["毛囊检测评估", "药物方案", "每月随访", "生发跟踪"],
            "requires_prescription": True,
            "category": "脱发",
        },
        "skin": {
            "name": "皮肤管理",
            "emoji": "🧴",
            "description": "祛痘/美白/抗衰，皮肤科医生在线诊疗",
            "first_price": 299,
            "renew_price": 399,
            "unit": "月",
            "includes": ["皮肤评估", "个性化方案", "药品/护肤品配送", "定期随访"],
            "requires_prescription": False,
            "category": "皮肤",
        },
        "mens": {
            "name": "男性健康",
            "emoji": "💪",
            "description": "精力管理/睾酮/前列腺，专业男性健康",
            "first_price": 399,
            "renew_price": 599,
            "unit": "月",
            "includes": ["健康评估", "检验建议", "药物方案", "隐私配送"],
            "requires_prescription": True,
            "category": "男性",
        },
        "sleep": {
            "name": "助眠调理",
            "emoji": "😴",
            "description": "失眠/焦虑/褪黑素，科学改善睡眠",
            "first_price": 199,
            "renew_price": 299,
            "unit": "月",
            "includes": ["睡眠评估", "行为指导", "必要时药物", "睡眠日记跟踪"],
            "requires_prescription": False,
            "category": "睡眠",
        },
    }

    ASSESSMENT_QUESTIONS = {
        "glp1": [
            {"id": 1, "text": "您的身高是多少(cm)？", "type": "input", "field": "height"},
            {"id": 2, "text": "您的体重是多少(kg)？", "type": "input", "field": "weight"},
            {"id": 3, "text": "您的目标体重是多少(kg)？", "type": "input", "field": "target_weight"},
            {"id": 4, "text": "是否有糖尿病或糖尿病前期？", "type": "choice", "options": ["是", "否", "不确定"]},
            {"id": 5, "text": "是否尝试过其他减肥方法？", "type": "choice", "options": ["节食", "运动", "减肥药", "均未尝试"]},
            {"id": 6, "text": "是否有甲状腺疾病？", "type": "choice", "options": ["是", "否"]},
            {"id": 7, "text": "是否有胰腺炎病史？", "type": "choice", "options": ["是", "否"]},
            {"id": 8, "text": "是否怀孕或备孕中？", "type": "choice", "options": ["是", "否", "不适用"]},
            {"id": 9, "text": "是否有进食障碍史？", "type": "choice", "options": ["是", "否"]},
            {"id": 10, "text": "希望多久达到目标？", "type": "choice", "options": ["3个月", "6个月", "1年", "不急"]},
        ],
        "hair": [
            {"id": 1, "text": "脱发类型？", "type": "choice", "options": ["M型发际线", "头顶稀疏", "整体稀疏", "斑秃"]},
            {"id": 2, "text": "脱发持续多长时间？", "type": "choice", "options": ["不到半年", "半年~2年", "2年以上"]},
            {"id": 3, "text": "家族是否有脱发史？", "type": "choice", "options": ["父亲", "母亲", "双方", "无"]},
            {"id": 4, "text": "是否使用过防脱产品？", "type": "choice", "options": ["米诺地尔", "非那雄胺", "其他", "未使用"]},
            {"id": 5, "text": "是否有药物过敏？", "type": "choice", "options": ["是", "否"]},
            {"id": 6, "text": "是否有肝脏疾病？", "type": "choice", "options": ["是", "否"]},
        ],
        "skin": [
            {"id": 1, "text": "主要皮肤问题？", "type": "choice", "options": ["痘痘/痤疮", "色斑/暗沉", "皱纹/松弛", "敏感/红血丝"]},
            {"id": 2, "text": "皮肤类型？", "type": "choice", "options": ["油性", "干性", "混合", "敏感"]},
            {"id": 3, "text": "问题持续时间？", "type": "choice", "options": ["不到1个月", "1-6个月", "6个月以上"]},
            {"id": 4, "text": "是否使用过处方药？", "type": "choice", "options": ["维A酸", "抗生素", "激素类", "未使用"]},
            {"id": 5, "text": "是否有药物过敏？", "type": "choice", "options": ["是", "否"]},
        ],
        "mens": [
            {"id": 1, "text": "主要困扰？", "type": "choice", "options": ["精力不足", "性功能", "前列腺", "其他"]},
            {"id": 2, "text": "年龄？", "type": "input", "field": "age"},
            {"id": 3, "text": "是否有心血管疾病？", "type": "choice", "options": ["是", "否"]},
            {"id": 4, "text": "是否检测过睾酮水平？", "type": "choice", "options": ["是（偏低）", "是（正常）", "未检测"]},
            {"id": 5, "text": "是否有药物过敏？", "type": "choice", "options": ["是", "否"]},
        ],
        "sleep": [
            {"id": 1, "text": "失眠类型？", "type": "choice", "options": ["入睡困难", "易醒", "早醒", "多梦"]},
            {"id": 2, "text": "失眠持续时间？", "type": "choice", "options": ["不到1周", "1-4周", "1-3个月", "3个月以上"]},
            {"id": 3, "text": "是否伴有焦虑/抑郁？", "type": "choice", "options": ["是", "否", "不确定"]},
            {"id": 4, "text": "是否使用过助眠药物？", "type": "choice", "options": ["褪黑素", "安定类", "中成药", "未使用"]},
            {"id": 5, "text": "每天睡眠时长？", "type": "choice", "options": ["不到4小时", "4-6小时", "6-8小时"]},
        ],
    }

    PARTNER_HOSPITALS = [
        {"id": "p001", "name": "京东健康互联网医院", "specialties": ["全科", "皮肤科", "男科"], "type": "互联网医院"},
        {"id": "p002", "name": "微医互联网医院", "specialties": ["全科", "内分泌", "皮肤科"], "type": "互联网医院"},
        {"id": "p003", "name": "好大夫在线", "specialties": ["全科", "脱发", "减重"], "type": "互联网医院"},
    ]

    PARTNER_PHARMACIES = [
        {"id": "f001", "name": "大参林大药房", "type": "连锁药房", "delivery": "顺丰/京东"},
        {"id": "f002", "name": "益丰大药房", "type": "连锁药房", "delivery": "顺丰"},
    ]

# ========== 数据存储 ==========
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

def load_data(name):
    f = DATA_DIR / f"{name}.json"
    if f.exists():
        return json.loads(f.read_text())
    return {}

def save_data(name, data):
    (DATA_DIR / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))

# ========== AI引擎 ==========
class SlimAIEngine:
    @staticmethod
    def analyze(product_id, answers):
        product = Config.PRODUCTS.get(product_id, {})
        questions = Config.ASSESSMENT_QUESTIONS.get(product_id, [])

        if product_id == "glp1":
            return SlimAIEngine._analyze_glp1(product, answers, questions)
        elif product_id == "hair":
            return SlimAIEngine._analyze_hair(product, answers, questions)
        else:
            return SlimAIEngine._analyze_generic(product, product_id, answers, questions)

    @staticmethod
    def _analyze_glp1(product, answers, questions):
        try:
            height = float(answers.get("1", "170")) / 100
            weight = float(answers.get("2", "80"))
            target = float(answers.get("3", "70"))
        except:
            height, weight, target = 1.70, 80.0, 70.0

        bmi = round(weight / (height ** 2), 1)
        need = round(weight - target, 1)

        # 禁忌症筛查
        contraindications = []
        if answers.get("4") == "是":
            contraindications.append("糖尿病（需医师评估用药方案）")
        if answers.get("6") == "是":
            contraindications.append("甲状腺疾病（需排除MTC风险）")
        if answers.get("7") == "是":
            contraindications.append("胰腺炎病史（GLP-1相对禁忌）")
        if answers.get("8") == "是":
            contraindications.append("怀孕/备孕（禁用GLP-1）")
        if answers.get("9") == "是":
            contraindications.append("进食障碍史（需心理评估）")

        if contraindications:
            return {
                "product": product["name"],
                "eligible": False,
                "reason": "存在用药禁忌，建议线下就诊",
                "contraindications": contraindications,
                "recommendation": "请前往三甲医院内分泌科进行详细评估",
            }

        # BMI评估
        if bmi >= 28:
            urgency = "high"
            plan = "强烈推荐GLP-1治疗 + 饮食运动指导"
        elif bmi >= 24:
            urgency = "medium"
            plan = "推荐GLP-1辅助减重 + 生活方式干预"
        elif bmi >= 18.5:
            urgency = "low"
            plan = "BMI正常，如确有减重需求建议先尝试生活方式干预"
        else:
            return {
                "product": product["name"],
                "eligible": False,
                "reason": f"BMI {bmi} 已偏瘦，不建议药物减重",
                "recommendation": "如有身体形象困扰，建议心理咨询",
            }

        # 估算方案
        months = max(3, min(12, round(need / 3)))  # 每月约减3kg
        est_cost = product["first_price"] + product["renew_price"] * (months - 1)

        return {
            "product": product["name"],
            "eligible": True,
            "bmi": bmi,
            "weight_to_lose": need,
            "urgency": urgency,
            "plan": plan,
            "estimated_months": months,
            "estimated_total_cost": est_cost,
            "first_month_price": product["first_price"],
            "includes": product["includes"],
            "next_step": "order",
        }

    @staticmethod
    def _analyze_hair(product, answers, questions):
        severity_map = {
            "不到半年": "early",
            "半年~2年": "moderate",
            "2年以上": "advanced",
        }
        severity = severity_map.get(answers.get("2", ""), "unknown")

        family_history = answers.get("3", "无") != "无"
        prior_treatment = answers.get("4") not in ["未使用", None]
        has_liver = answers.get("6") == "是"

        if has_liver:
            return {
                "product": product["name"],
                "eligible": False,
                "reason": "肝脏疾病患者不建议使用口服非那雄胺",
                "recommendation": "可考虑外用米诺地尔（无需口服）",
            }

        if severity == "early":
            plan = "外用米诺地尔 + 口服非那雄胺（6个月疗程）"
            months = 6
        elif severity == "moderate":
            plan = "外用米诺地尔 + 口服非那雄胺 + 微针辅助（12个月疗程）"
            months = 12
        else:
            plan = "综合治疗方案（含口服+外用+辅助），12个月起"
            months = 12

        return {
            "product": product["name"],
            "eligible": True,
            "severity": severity,
            "family_history": family_history,
            "prior_treatment": prior_treatment,
            "plan": plan,
            "estimated_months": months,
            "estimated_total_cost": product["first_price"] + product["renew_price"] * (months - 1),
            "first_month_price": product["first_price"],
            "includes": product["includes"],
            "next_step": "order",
        }

    @staticmethod
    def _analyze_generic(product, product_id, answers, questions):
        positive = sum(1 for k, v in answers.items() if v in ["是", "严重", "经常"])
        total = len(questions)
        score = round(positive / max(total, 1) * 100, 1)

        if score >= 60:
            urgency, plan = "high", f"建议立即开始{product.get('name', '治疗')}方案"
        elif score >= 30:
            urgency, plan = "medium", f"推荐{product.get('name', '调理')}方案"
        else:
            urgency, plan = "low", "症状较轻，可先尝试生活方式调整"

        return {
            "product": product.get("name", ""),
            "eligible": True,
            "urgency": urgency,
            "score": score,
            "plan": plan,
            "estimated_months": 3,
            "estimated_total_cost": product.get("first_price", 0) + product.get("renew_price", 0) * 2,
            "first_month_price": product.get("first_price", 0),
            "includes": product.get("includes", []),
            "next_step": "order",
        }

# ========== 订单管理 ==========
class OrderManager:
    @staticmethod
    def create_order(user_id, product_id, assessment_result, name, phone, address):
        products_db = load_data("products")
        product = Config.PRODUCTS.get(product_id, {})

        order = {
            "id": str(uuid.uuid4())[:12],
            "user_id": user_id,
            "product_id": product_id,
            "product_name": product.get("name", ""),
            "status": "pending_payment",
            "price": product.get("first_price", 0),
            "name": name,
            "phone": phone,
            "address": address,
            "assessment": assessment_result,
            "created_at": datetime.now().isoformat(),
            "timeline": [
                {"time": datetime.now().isoformat(), "status": "created", "desc": "订单创建"},
            ],
        }

        products_db[order["id"]] = order
        # 模拟自动支付成功→进入医师审核
        order["status"] = "paid"
        order["timeline"].append({"time": datetime.now().isoformat(), "status": "paid", "desc": "支付成功"})
        order["status"] = "doctor_review"
        order["timeline"].append({"time": datetime.now().isoformat(), "status": "doctor_review", "desc": "已提交医师审核"})
        save_data("products", products_db)
        return order

# ========== HTTP处理器 ==========
class MediSlimHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            self._serve("templates/index.html", "text/html; charset=utf-8")
        elif path.startswith("/static/"):
            ct = "text/css" if path.endswith(".css") else "application/javascript"
            self._serve(path[1:], ct)
        elif path == "/api/products":
            self._json(Config.PRODUCTS)
        elif path == "/api/hospitals":
            self._json(Config.PARTNER_HOSPITALS)
        elif path == "/api/stats":
            users = load_data("users")
            orders = load_data("products")
            self._json({
                "total_users": len(users),
                "total_orders": len(orders),
                "products": len(Config.PRODUCTS),
                "hospitals": len(Config.PARTNER_HOSPITALS),
            })
        else:
            self._json({"error": "Not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(body)
        except:
            data = {}

        path = self.path

        if path == "/api/user/register":
            users = load_data("users")
            uid = str(uuid.uuid4())[:12]
            users[uid] = {
                "id": uid,
                "phone": data.get("phone", ""),
                "name": data.get("name", "用户"),
                "created_at": datetime.now().isoformat(),
                "orders": [],
            }
            save_data("users", users)
            self._json(users[uid])

        elif path == "/api/assessment/start":
            pid = data.get("product_id", "")
            questions = Config.ASSESSMENT_QUESTIONS.get(pid, [])
            product = Config.PRODUCTS.get(pid, {})
            if not questions:
                self._json({"error": "产品不存在"}, 400)
                return
            self._json({
                "product_id": pid,
                "product_name": product.get("name", ""),
                "questions": questions,
                "total": len(questions),
            })

        elif path == "/api/assessment/analyze":
            pid = data.get("product_id", "")
            answers = data.get("answers", {})
            result = SlimAIEngine.analyze(pid, answers)
            self._json(result)

        elif path == "/api/order/create":
            uid = data.get("user_id", "")
            pid = data.get("product_id", "")
            result = data.get("assessment", {})
            order = OrderManager.create_order(
                uid, pid, result,
                data.get("name", ""),
                data.get("phone", ""),
                data.get("address", ""),
            )
            self._json(order)

        elif path == "/api/order/status":
            oid = data.get("order_id", "")
            orders = load_data("products")
            order = orders.get(oid)
            if not order:
                self._json({"error": "订单不存在"}, 404)
                return
            self._json(order)

        else:
            self._json({"error": "Not found"}, 404)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _serve(self, filepath, content_type):
        full = Path(__file__).parent / filepath
        if full.exists():
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(full.read_bytes())
        else:
            self._json({"error": "Not found"}, 404)

    def log_message(self, *a):
        pass

# ========== 启动 ==========
def main():
    port = int(os.environ.get("PORT", 8090))
    server = HTTPServer(("0.0.0.0", port), MediSlimHandler)
    print(f"💰 MediSlim 轻健康平台启动成功")
    print(f"📱 访问: http://localhost:{port}")
    print(f"📊 统计: http://localhost:{port}/api/stats")
    server.serve_forever()

if __name__ == "__main__":
    main()
