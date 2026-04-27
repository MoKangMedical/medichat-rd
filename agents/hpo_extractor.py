"""
MediChat-RD DeepRare模式 — HPO表型提取Agent
将自由文本症状描述标准化为HPO（人类表型本体）术语
参考DeepRare架构：表型提取→标准化→疾病匹配
"""
import json
import re
from pathlib import Path

# ========== HPO术语库（精简版） ==========
# 实际生产环境应对接HPO API: https://hpo.jax.org/api/
HPO_TERMS = {
    # 神经系统
    "肌无力": {"id": "HP:0001252", "name": "Muscular hypotonia", "synonyms": ["肌肉无力", "乏力", "没力气"]},
    "肌肉萎缩": {"id": "HP:0003202", "name": "Skeletal muscle atrophy", "synonyms": ["肌肉变小", "肌肉消瘦"]},
    "痉挛": {"id": "HP:0001257", "name": "Spasticity", "synonyms": ["抽筋", "肌肉僵硬"]},
    "癫痫": {"id": "HP:0001250", "name": "Seizure", "synonyms": ["抽搐", "羊癫疯", "大发作"]},
    "发育迟缓": {"id": "HP:0001263", "name": "Global developmental delay", "synonyms": ["发育落后", "智力落后"]},
    "共济失调": {"id": "HP:0001251", "name": "Ataxia", "synonyms": ["走路不稳", "平衡障碍"]},
    "震颤": {"id": "HP:0001337", "name": "Tremor", "synonyms": ["手抖", "发抖"]},
    "吞咽困难": {"id": "HP:0002015", "name": "Dysphagia", "synonyms": ["咽不下", "呛咳"]},
    "眼睑下垂": {"id": "HP:0000508", "name": "Ptosis", "synonyms": ["上睑下垂", "眼皮抬不起"]},
    "复视": {"id": "HP:0000651", "name": "Diplopia", "synonyms": ["看东西重影", "重影"]},
    "言语不清": {"id": "HP:0001260", "name": "Dysarthria", "synonyms": ["说话不清", "口齿不清"]},

    # 肌肉骨骼
    "关节痛": {"id": "HP:0002829", "name": "Arthralgia", "synonyms": ["关节疼", "关节不适"]},
    "关节肿胀": {"id": "HP:0001386", "name": "Joint swelling", "synonyms": ["关节肿", "关节积液"]},
    "脊柱侧弯": {"id": "HP:0002650", "name": "Scoliosis", "synonyms": ["脊柱弯曲", "驼背"]},
    "身材矮小": {"id": "HP:0004322", "name": "Short stature", "synonyms": ["个子矮", "生长迟缓"]},

    # 皮肤
    "皮疹": {"id": "HP:0000988", "name": "Skin rash", "synonyms": ["出疹子", "红疹", "起疹"]},
    "色素沉着": {"id": "HP:0000953", "name": "Hyperpigmentation", "synonyms": ["皮肤变黑", "色斑"]},
    "牛奶咖啡斑": {"id": "HP:0000957", "name": "Cafe-au-lait spot", "synonyms": ["咖啡斑"]},
    "血管角化瘤": {"id": "HP:0001029", "name": "Angiokeratoma", "synonyms": []},

    # 眼部
    "视力下降": {"id": "HP:0000546", "name": "Decreased visual acuity", "synonyms": ["看不清", "视力模糊"]},
    "白内障": {"id": "HP:0000518", "name": "Cataract", "synonyms": ["晶状体混浊"]},
    "角膜混浊": {"id": "HP:0007957", "name": "Corneal opacity", "synonyms": ["角膜白斑"]},
    "视网膜色素变性": {"id": "HP:0000556", "name": "Retinal dystrophy", "synonyms": ["夜盲", "视野缩小"]},

    # 心血管
    "心肌病": {"id": "HP:0001638", "name": "Cardiomyopathy", "synonyms": ["心肌病变", "心脏扩大"]},
    "心律不齐": {"id": "HP:0011675", "name": "Arrhythmia", "synonyms": ["心律失常", "心跳不规则"]},
    "高血压": {"id": "HP:0000822", "name": "Hypertension", "synonyms": ["血压高"]},

    # 消化系统
    "肝脾肿大": {"id": "HP:0001433", "name": "Hepatosplenomegaly", "synonyms": ["肝大", "脾大"]},
    "腹痛": {"id": "HP:0002027", "name": "Abdominal pain", "synonyms": ["肚子疼", "腹胀"]},
    "腹泻": {"id": "HP:0002014", "name": "Diarrhea", "synonyms": ["拉肚子", "水样便"]},

    # 泌尿/肾脏
    "血尿": {"id": "HP:0000790", "name": "Hematuria", "synonyms": ["尿血", "尿色红"]},
    "蛋白尿": {"id": "HP:0000093", "name": "Proteinuria", "synonyms": ["尿蛋白"]},
    "肾功能不全": {"id": "HP:0000083", "name": "Renal insufficiency", "synonyms": ["肾衰", "肾功能下降"]},

    # 全身
    "疲劳": {"id": "HP:0012378", "name": "Fatigue", "synonyms": ["疲倦", "累", "乏力"]},
    "发热": {"id": "HP:0001945", "name": "Fever", "synonyms": ["发烧", "体温高"]},
    "体重下降": {"id": "HP:0004395", "name": "Weight loss", "synonyms": ["消瘦", "体重减轻"]},
    "生长迟缓": {"id": "HP:0001510", "name": "Growth delay", "synonyms": ["发育慢", "不长个"]},
}


class HPOExtractor:
    """HPO表型提取Agent — 参考DeepRare表型提取器"""

    def __init__(self):
        self.terms = HPO_TERMS
        # 构建反向索引（所有同义词→标准术语）
        self.synonym_index = {}
        for key, term in self.terms.items():
            self.synonym_index[key] = term
            for syn in term["synonyms"]:
                self.synonym_index[syn] = term

    def extract(self, text):
        """
        从自由文本提取HPO术语
        输入: "我最近眼睑下垂，吞咽困难，全身无力"
        输出: [
            {"hpo_id": "HP:0000508", "name": "Ptosis", "matched": "眼睑下垂", "confidence": 1.0},
            {"hpo_id": "HP:0002015", "name": "Dysphagia", "matched": "吞咽困难", "confidence": 1.0},
            {"hpo_id": "HP:0001252", "name": "Muscular hypotonia", "matched": "无力", "confidence": 0.8}
        ]
        """
        results = []
        matched_positions = set()

        # 按关键词长度降序匹配（优先匹配长词）
        sorted_terms = sorted(self.synonym_index.keys(), key=len, reverse=True)

        for term_text in sorted_terms:
            start = 0
            while True:
                pos = text.find(term_text, start)
                if pos == -1:
                    break
                end = pos + len(term_text)

                # 检查是否与已匹配区域重叠
                overlap = False
                for mp_start, mp_end in matched_positions:
                    if pos < mp_end and end > mp_start:
                        overlap = True
                        break

                if not overlap:
                    term_info = self.synonym_index[term_text]
                    confidence = 1.0 if term_text in self.terms else 0.85
                    results.append({
                        "hpo_id": term_info["id"],
                        "name": term_info["name"],
                        "matched_text": term_text,
                        "position": pos,
                        "confidence": confidence,
                    })
                    matched_positions.add((pos, end))

                start = pos + 1

        return results

    def to_hpo_list(self, text):
        """返回HPO ID列表"""
        results = self.extract(text)
        return list(set(r["hpo_id"] for r in results))

    def analyze_symptoms(self, text):
        """
        深度分析症状文本
        返回: 提取结果 + 可能涉及的系统 + 建议检查
        """
        extracted = self.extract(text)

        # 识别涉及的医学系统
        systems = set()
        system_map = {
            "HP:0001": "神经系统",
            "HP:0003": "肌肉骨骼",
            "HP:00009": "皮肤",
            "HP:00005": "眼部",
            "HP:00016": "心血管",
            "HP:00020": "消化系统",
            "HP:00007": "泌尿系统",
            "HP:00000": "肾脏",
            "HP:00019": "全身/代谢",
            "HP:00043": "生长发育",
            "HP:00015": "生长发育",
            "HP:00123": "全身/代谢",
        }
        for r in extracted:
            prefix = r["hpo_id"][:6]
            for p, s in system_map.items():
                if prefix.startswith(p):
                    systems.add(s)

        return {
            "extracted_phenotypes": extracted,
            "hpo_ids": [r["hpo_id"] for r in extracted],
            "systems_involved": list(systems),
            "phenotype_count": len(extracted),
            "multi_system": len(systems) > 1,
            "confidence_avg": round(sum(r["confidence"] for r in extracted) / max(len(extracted), 1), 2),
        }


# ========== 测试 ==========
if __name__ == "__main__":
    extractor = HPOExtractor()

    test_cases = [
        "我最近眼睑下垂，吞咽困难，全身无力，说话也不清楚了",
        "孩子发育迟缓，经常抽搐，走路不稳",
        "关节痛，皮疹，反复发热，体重下降",
        "看东西有重影，眼皮抬不起来，下午特别明显",
    ]

    for text in test_cases:
        result = extractor.analyze_symptoms(text)
        print(f"\n📝 输入: {text}")
        print(f"   提取 {result['phenotype_count']} 个表型:")
        for p in result["extracted_phenotypes"]:
            print(f"     {p['hpo_id']} {p['name']} ← \"{p['matched_text']}\" ({p['confidence']})")
        print(f"   涉及系统: {', '.join(result['systems_involved'])}")
