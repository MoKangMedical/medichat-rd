"""
MediChat-RD — 实验室检验值解析器
参考OrphaMind：自动提取检验值、异常标记、临界值警报
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class LabResult:
    """单个检验结果"""
    name: str
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    status: str = "normal"  # normal / high / low / critical_high / critical_low
    fold_change: Optional[float] = None  # 超出参考值的倍数


# ========== 检验参考值数据库 ==========
REFERENCE_RANGES = {
    # 血常规
    "白细胞": {"low": 4.0, "high": 10.0, "unit": "×10⁹/L", "critical_low": 2.0, "critical_high": 30.0},
    "WBC": {"low": 4.0, "high": 10.0, "unit": "×10⁹/L", "critical_low": 2.0, "critical_high": 30.0},
    "红细胞": {"low": 3.5, "high": 5.5, "unit": "×10¹²/L"},
    "RBC": {"low": 3.5, "high": 5.5, "unit": "×10¹²/L"},
    "血红蛋白": {"low": 110, "high": 160, "unit": "g/L", "critical_low": 60, "critical_high": 200},
    "Hb": {"low": 110, "high": 160, "unit": "g/L", "critical_low": 60, "critical_high": 200},
    "HGB": {"low": 110, "high": 160, "unit": "g/L", "critical_low": 60, "critical_high": 200},
    "血小板": {"low": 100, "high": 300, "unit": "×10⁹/L", "critical_low": 20, "critical_high": 1000},
    "PLT": {"low": 100, "high": 300, "unit": "×10⁹/L", "critical_low": 20, "critical_high": 1000},

    # 肝功能
    "ALT": {"low": 0, "high": 40, "unit": "U/L", "critical_high": 300},
    "谷丙转氨酶": {"low": 0, "high": 40, "unit": "U/L", "critical_high": 300},
    "AST": {"low": 0, "high": 40, "unit": "U/L", "critical_high": 300},
    "谷草转氨酶": {"low": 0, "high": 40, "unit": "U/L", "critical_high": 300},
    "总胆红素": {"low": 3.4, "high": 17.1, "unit": "μmol/L"},
    "TBIL": {"low": 3.4, "high": 17.1, "unit": "μmol/L"},
    "白蛋白": {"low": 35, "high": 55, "unit": "g/L"},
    "ALB": {"low": 35, "high": 55, "unit": "g/L"},

    # 肾功能
    "肌酐": {"low": 44, "high": 133, "unit": "μmol/L", "critical_high": 500},
    "Cr": {"low": 44, "high": 133, "unit": "μmol/L", "critical_high": 500},
    "CRE": {"low": 44, "high": 133, "unit": "μmol/L", "critical_high": 500},
    "尿素氮": {"low": 2.9, "high": 8.2, "unit": "mmol/L"},
    "BUN": {"low": 2.9, "high": 8.2, "unit": "mmol/L"},
    "尿酸": {"low": 149, "high": 416, "unit": "μmol/L"},
    "UA": {"low": 149, "high": 416, "unit": "μmol/L"},

    # 血糖
    "血糖": {"low": 3.9, "high": 6.1, "unit": "mmol/L", "critical_low": 2.2, "critical_high": 22.0},
    "GLU": {"low": 3.9, "high": 6.1, "unit": "mmol/L", "critical_low": 2.2, "critical_high": 22.0},
    "空腹血糖": {"low": 3.9, "high": 6.1, "unit": "mmol/L", "critical_low": 2.2, "critical_high": 22.0},
    "糖化血红蛋白": {"low": 4.0, "high": 6.0, "unit": "%"},
    "HbA1c": {"low": 4.0, "high": 6.0, "unit": "%"},

    # 血脂
    "总胆固醇": {"low": 0, "high": 5.2, "unit": "mmol/L"},
    "TC": {"low": 0, "high": 5.2, "unit": "mmol/L"},
    "甘油三酯": {"low": 0, "high": 1.7, "unit": "mmol/L"},
    "TG": {"low": 0, "high": 1.7, "unit": "mmol/L"},
    "低密度脂蛋白": {"low": 0, "high": 3.4, "unit": "mmol/L"},
    "LDL": {"low": 0, "high": 3.4, "unit": "mmol/L"},
    "高密度脂蛋白": {"low": 1.0, "high": 999, "unit": "mmol/L"},
    "HDL": {"low": 1.0, "high": 999, "unit": "mmol/L"},

    # 电解质
    "钾": {"low": 3.5, "high": 5.5, "unit": "mmol/L", "critical_low": 2.5, "critical_high": 6.5},
    "K": {"low": 3.5, "high": 5.5, "unit": "mmol/L", "critical_low": 2.5, "critical_high": 6.5},
    "钠": {"low": 136, "high": 145, "unit": "mmol/L", "critical_low": 120, "critical_high": 160},
    "Na": {"low": 136, "high": 145, "unit": "mmol/L", "critical_low": 120, "critical_high": 160},
    "氯": {"low": 96, "high": 106, "unit": "mmol/L"},
    "Cl": {"low": 96, "high": 106, "unit": "mmol/L"},
    "钙": {"low": 2.1, "high": 2.6, "unit": "mmol/L"},
    "Ca": {"low": 2.1, "high": 2.6, "unit": "mmol/L"},

    # 心肌标志物
    "肌钙蛋白": {"low": 0, "high": 0.04, "unit": "ng/mL", "critical_high": 0.5},
    "cTnI": {"low": 0, "high": 0.04, "unit": "ng/mL", "critical_high": 0.5},
    "BNP": {"low": 0, "high": 100, "unit": "pg/mL", "critical_high": 900},

    # 凝血
    "PT": {"low": 11, "high": 13, "unit": "秒"},
    "INR": {"low": 0.8, "high": 1.2, "unit": "", "critical_high": 3.0},
    "APTT": {"low": 25, "high": 37, "unit": "秒"},

    # 炎症
    "CRP": {"low": 0, "high": 10, "unit": "mg/L", "critical_high": 100},
    "C反应蛋白": {"low": 0, "high": 10, "unit": "mg/L", "critical_high": 100},
    "ESR": {"low": 0, "high": 20, "unit": "mm/h"},
    "血沉": {"low": 0, "high": 20, "unit": "mm/h"},

    # 肌酶谱（罕见病重要指标）
    "CK": {"low": 26, "high": 196, "unit": "U/L", "critical_high": 1000},
    "肌酸激酶": {"low": 26, "high": 196, "unit": "U/L", "critical_high": 1000},
    "CK-MB": {"low": 0, "high": 24, "unit": "U/L"},
    "LDH": {"low": 120, "high": 250, "unit": "U/L", "critical_high": 500},
    "乳酸脱氢酶": {"low": 120, "high": 250, "unit": "U/L", "critical_high": 500},

    # 甲状腺
    "TSH": {"low": 0.27, "high": 4.2, "unit": "mIU/L"},
    "FT3": {"low": 3.1, "high": 6.8, "unit": "pmol/L"},
    "FT4": {"low": 12, "high": 22, "unit": "pmol/L"},

    # 特殊指标
    "苯丙氨酸": {"low": 0, "high": 120, "unit": "μmol/L"},  # PKU筛查
    "Phe": {"low": 0, "high": 120, "unit": "μmol/L"},
    "α-半乳糖苷酶": {"low": 2.4, "high": 16.0, "unit": "nmol/h/mg"},  # Fabry病
    "GCase": {"low": 2.4, "high": 16.0, "unit": "nmol/h/mg"},  # 戈谢病
}


class LabAnalyzer:
    """实验室检验值解析器"""

    def __init__(self):
        self.ref = REFERENCE_RANGES

    def parse_text(self, text: str) -> List[LabResult]:
        """
        从自由文本中提取检验值
        支持格式：
        - "白细胞 5.2×10⁹/L"
        - "WBC: 12.5 10^9/L"
        - "肌酐135μmol/L"
        - "ALT 80 U/L (参考: 0-40)"
        - "血糖6.5mmol/L"
        """
        results = []

        # 模式1: 检验名 数值 单位
        pattern1 = r'([A-Za-z\u4e00-\u9fa5]{2,10})\s*[：:为是]?\s*(\d+\.?\d*)\s*([×\*]?\s*10[⁰-⁹\^0-9]*\s*/?\s*[a-zA-Zμ]+/?(?:[a-zA-Zμ/]+)?)'
        # 模式2: 带参考值
        pattern2 = r'([A-Za-z\u4e00-\u9fa5]{2,10})\s*[：:为是]?\s*(\d+\.?\d*)\s*([a-zA-Zμ×\^⁰-⁹/]+)\s*[\(（]?\s*参考.*?(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)'

        # 先尝试带参考值的模式
        for match in re.finditer(pattern2, text):
            name, value, unit, ref_low, ref_high = match.groups()
            result = self._analyze(name.strip(), float(value), unit.strip(),
                                   float(ref_low), float(ref_high))
            if result:
                results.append(result)

        # 再尝试简单模式
        for match in re.finditer(pattern1, text):
            name, value, unit = match.groups()
            name = name.strip()
            # 跳过已经匹配过的
            if any(r.name == name for r in results):
                continue
            result = self._analyze(name.strip(), float(value), unit.strip())
            if result:
                results.append(result)

        return results

    def _analyze(self, name: str, value: float, unit: str,
                 ref_low: Optional[float] = None,
                 ref_high: Optional[float] = None) -> Optional[LabResult]:
        """分析单个检验值"""

        # 查找参考值
        ref = self.ref.get(name)
        if ref:
            low = ref_low or ref["low"]
            high = ref_high or ref["high"]
            unit = unit or ref.get("unit", "")
            critical_low = ref.get("critical_low")
            critical_high = ref.get("critical_high")
        else:
            if ref_low is None and ref_high is None:
                return None  # 无法判断，跳过
            low = ref_low or 0
            high = ref_high or float('inf')
            critical_low = None
            critical_high = None

        # 判断状态
        status = "normal"
        fold_change = None

        if value < low:
            status = "low"
            fold_change = (low - value) / low if low > 0 else None
            if critical_low and value <= critical_low:
                status = "critical_low"
        elif value > high:
            status = "high"
            fold_change = (value - high) / high if high > 0 else None
            if critical_high and value >= critical_high:
                status = "critical_high"

        return LabResult(
            name=name,
            value=value,
            unit=unit,
            reference_low=low,
            reference_high=high,
            status=status,
            fold_change=round(fold_change, 2) if fold_change else None,
        )

    def analyze_clinical_note(self, text: str) -> Dict:
        """
        分析完整临床笔记
        返回: 检验结果 + 异常标记 + 临床建议
        """
        results = self.parse_text(text)

        critical = [r for r in results if "critical" in r.status]
        abnormal = [r for r in results if r.status != "normal"]
        normal = [r for r in results if r.status == "normal"]

        return {
            "total": len(results),
            "results": [self._result_to_dict(r) for r in results],
            "critical": [self._result_to_dict(r) for r in critical],
            "abnormal_count": len(abnormal),
            "normal_count": len(normal),
            "clinical_alerts": self._generate_alerts(critical, abnormal),
        }

    def _result_to_dict(self, r: LabResult) -> Dict:
        return {
            "name": r.name,
            "value": r.value,
            "unit": r.unit,
            "reference": f"{r.reference_low}-{r.reference_high}",
            "status": r.status,
            "status_text": {
                "normal": "✅正常",
                "high": "⚠️偏高",
                "low": "⚠️偏低",
                "critical_high": "🔴危急高值",
                "critical_low": "🔴危急低值",
            }.get(r.status, r.status),
            "fold_change": r.fold_change,
        }

    def _generate_alerts(self, critical: List, abnormal: List) -> List[str]:
        """生成临床警报"""
        alerts = []
        if critical:
            for r in critical:
                alerts.append(f"🔴 危急值: {r.name} = {r.value}{r.unit} (参考: {r.reference_low}-{r.reference_high})")
        if abnormal:
            names = [r.name for r in abnormal[:5]]
            alerts.append(f"⚠️ 异常指标: {', '.join(names)}")
        return alerts


# ========== 测试 ==========
if __name__ == "__main__":
    analyzer = LabAnalyzer()

    test_note = """
    患者女性，35岁，主诉眼睑下垂、吞咽困难3个月。
    查体：双眼睑下垂，下午加重；四肢肌力4级。
    
    实验室检查：
    - 乙酰胆碱受体抗体 阳性（1.2nmol/L，参考<0.5）
    - CK 850 U/L (参考: 26-196)
    - ALT 45 U/L (参考: 0-40)
    - WBC 5.2×10⁹/L
    - 血红蛋白 125g/L
    - 肌酐 68μmol/L
    - 钾 4.2mmol/L
    - TSH 2.5mIU/L
    - 肌钙蛋白 0.8ng/mL (参考: 0-0.04)
    """

    result = analyzer.analyze_clinical_note(test_note)

    print("=" * 60)
    print("🔬 实验室检验解析结果")
    print("=" * 60)
    print(f"共解析 {result['total']} 项检验")
    print(f"异常: {result['abnormal_count']} 项")

    for alert in result['clinical_alerts']:
        print(f"\n{alert}")

    print("\n📊 详细结果:")
    for r in result['results']:
        print(f"  {r['status_text']} {r['name']}: {r['value']} {r['unit']} (参考: {r['reference']})")
