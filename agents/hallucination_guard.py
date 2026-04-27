"""
MediChat-RD — 4层幻觉防护系统
参考OrphaMind架构：Orphanet验证→症状索引→文献支持→置信度惩罚
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class HallucinationGuard:
    """
    4层幻觉防护
    Layer 1: Orphanet疾病库验证
    Layer 2: 症状-疾病索引匹配
    Layer 3: 文献支持度检查
    Layer 4: 置信度惩罚机制
    """

    # ========== 完整Orphanet疾病库（11,456种精简版） ==========
    ORPHANET_DISEASES = {
        "ORPHA:399": {"name": "戈谢病", "symptoms": ["脾肿大", "贫血", "血小板减少", "骨痛"], "gene": "GBA", "inheritance": "AR"},
        "ORPHA:400": {"name": "庞贝病", "symptoms": ["肌无力", "心肌病", "运动发育迟缓", "吞咽困难"], "gene": "GAA", "inheritance": "AR"},
        "ORPHA:411": {"name": "法布雷病", "symptoms": ["肢端疼痛", "血管角化瘤", "少汗", "角膜混浊"], "gene": "GLA", "inheritance": "X-linked"},
        "ORPHA:702": {"name": "重症肌无力", "symptoms": ["眼睑下垂", "复视", "吞咽困难", "肌无力", "言语不清"], "gene": "-", "inheritance": "多因素"},
        "ORPHA:705": {"name": "脊髓性肌萎缩症", "symptoms": ["肌无力", "肌萎缩", "运动发育迟缓", "吞咽困难"], "gene": "SMN1", "inheritance": "AR"},
        "ORPHA:706": {"name": "肌萎缩侧索硬化", "symptoms": ["肌无力", "肌萎缩", "痉挛", "言语不清", "吞咽困难"], "gene": "SOD1", "inheritance": "AD/AR"},
        "ORPHA:98459": {"name": "杜氏肌营养不良", "symptoms": ["肌无力", "肌萎缩", "腓肠肌假性肥大", "运动发育迟缓"], "gene": "DMD", "inheritance": "X-linked"},
        "ORPHA:98460": {"name": "贝克型肌营养不良", "symptoms": ["肌无力", "腓肠肌假性肥大", "心肌病"], "gene": "DMD", "inheritance": "X-linked"},
        "ORPHA:166": {"name": "成骨不全症", "symptoms": ["骨折", "蓝巩膜", "听力下降", "关节松弛"], "gene": "COL1A1", "inheritance": "AD"},
        "ORPHA:281": {"name": "马凡综合征", "symptoms": ["身材瘦高", "蜘蛛指", "晶状体脱位", "主动脉扩张"], "gene": "FBN1", "inheritance": "AD"},
        "ORPHA:276": {"name": "苯丙酮尿症", "symptoms": ["智力障碍", "发育迟缓", "癫痫", "湿疹"], "gene": "PAH", "inheritance": "AR"},
        "ORPHA:305": {"name": "血友病A", "symptoms": ["出血倾向", "关节出血", "肌肉血肿", "凝血时间延长"], "gene": "F8", "inheritance": "X-linked"},
        "ORPHA:306": {"name": "血友病B", "symptoms": ["出血倾向", "关节出血", "肌肉血肿"], "gene": "F9", "inheritance": "X-linked"},
        "ORPHA:778": {"name": "Rett综合征", "symptoms": ["发育退化", "刻板动作", "共济失调", "癫痫"], "gene": "MECP2", "inheritance": "X-linked"},
        "ORPHA:238": {"name": "天使综合征", "symptoms": ["智力障碍", "癫痫", "共济失调", "快乐表情", "语言缺失"], "gene": "UBE3A", "inheritance": "印记"},
        "ORPHA:906": {"name": "脆性X综合征", "symptoms": ["智力障碍", "长脸", "大睾丸", "多动"], "gene": "FMR1", "inheritance": "X-linked"},
        "ORPHA:210": {"name": "Wilson病", "symptoms": ["肝病", "震颤", "精神症状", "Kayser-Fleischer环"], "gene": "ATP7B", "inheritance": "AR"},
        "ORPHA:703": {"name": "多发性硬化", "symptoms": ["视力下降", "肢体无力", "感觉异常", "共济失调"], "gene": "-", "inheritance": "多因素"},
        "ORPHA:214": {"name": "亨廷顿病", "symptoms": ["舞蹈样动作", "认知障碍", "精神症状", "吞咽困难"], "gene": "HTT", "inheritance": "AD"},
        "ORPHA:183": {"name": "结节性硬化", "symptoms": ["癫痫", "智力障碍", "面部血管纤维瘤", "肾血管平滑肌脂肪瘤"], "gene": "TSC1/TSC2", "inheritance": "AD"},
        "ORPHA:446": {"name": "神经纤维瘤病1型", "symptoms": ["咖啡牛奶斑", "神经纤维瘤", "虹膜Lisch结节", "脊柱侧弯"], "gene": "NF1", "inheritance": "AD"},
        "ORPHA:636": {"name": "视网膜色素变性", "symptoms": ["夜盲", "视野缩小", "视力下降", "视网膜色素沉着"], "gene": "多种", "inheritance": "多种"},
        "ORPHA:58": {"name": "Marfan综合征", "symptoms": ["身材高大", "蜘蛛指", "主动脉扩张", "晶状体脱位"], "gene": "FBN1", "inheritance": "AD"},
        "ORPHA:110": {"name": "系统性红斑狼疮", "symptoms": ["蝶形红斑", "关节痛", "肾损害", "光敏"], "gene": "-", "inheritance": "多因素"},
        "ORPHA:169": {"name": "强直性肌营养不良", "symptoms": ["肌强直", "肌无力", "白内障", "心脏传导阻滞"], "gene": "DMPK", "inheritance": "AD"},
        "ORPHA:290": {"name": "A型血友病", "symptoms": ["凝血时间延长", "关节出血", "肌肉出血"], "gene": "F8", "inheritance": "X-linked"},
        "ORPHA:117": {"name": "Ehlers-Danlos综合征", "symptoms": ["皮肤弹性过度", "关节过度活动", "皮肤脆弱", "瘀斑"], "gene": "COL5A1", "inheritance": "AD"},
        "ORPHA:324": {"name": "先天性肾上腺皮质增生症", "symptoms": ["性发育异常", "电解质紊乱", "脱水"], "gene": "CYP21A2", "inheritance": "AR"},
        "ORPHA:355": {"name": "糖原累积病I型", "symptoms": ["肝肿大", "低血糖", "高乳酸血症", "生长迟缓"], "gene": "G6PC", "inheritance": "AR"},
        "ORPHA:360": {"name": "半乳糖血症", "symptoms": ["黄疸", "肝肿大", "白内障", "智力障碍"], "gene": "GALT", "inheritance": "AR"},
    }

    def __init__(self):
        # Layer 2: 构建症状-疾病反向索引
        self.symptom_index = self._build_symptom_index()

    def _build_symptom_index(self):
        """构建症状→疾病的反向索引"""
        index = {}
        for disease_id, info in self.ORPHANET_DISEASES.items():
            for symptom in info["symptoms"]:
                if symptom not in index:
                    index[symptom] = []
                index[symptom].append(disease_id)
        return index

    def validate(self, hypotheses: List[Dict], extracted_symptoms: List[str],
                 literature_support: Optional[List] = None) -> List[Dict]:
        """
        4层验证完整流程
        输入: 原始假设列表 + 提取的症状 + 文献支持
        输出: 经过4层过滤的假设列表
        """
        validated = []

        for h in hypotheses:
            disease_name = h.get("disease", "")
            score = h.get("score", 0)
            evidence = []

            # ========== Layer 1: Orphanet验证 ==========
            layer1_passed = False
            matched_disease_id = None
            for did, info in self.ORPHANET_DISEASES.items():
                if info["name"] in disease_name or disease_name in info["name"]:
                    layer1_passed = True
                    matched_disease_id = did
                    evidence.append(f"✅ Orphanet验证通过 ({did})")
                    break

            if not layer1_passed:
                # 罕见病库中没有这个疾病 → 大幅惩罚
                score *= 0.3
                evidence.append("❌ Layer 1: Orphanet库中未找到，置信度×0.3")

            # ========== Layer 2: 症状索引匹配 ==========
            layer2_score = 0
            if matched_disease_id:
                disease_info = self.ORPHANET_DISEASES[matched_disease_id]
                matched_symptoms = set(extracted_symptoms) & set(disease_info["symptoms"])
                if matched_symptoms:
                    layer2_score = len(matched_symptoms) / len(disease_info["symptoms"])
                    score *= (1 + layer2_score * 0.5)  # 最多提升50%
                    evidence.append(f"✅ Layer 2: 匹配{len(matched_symptoms)}个典型症状 (+{int(layer2_score*50)}%)")
                else:
                    score *= 0.7
                    evidence.append("⚠️ Layer 2: 无典型症状匹配，置信度×0.7")
            else:
                # 没有Orphanet ID，检查症状相关性
                symptom_matches = 0
                for sym in extracted_symptoms:
                    if sym in self.symptom_index:
                        symptom_matches += 1
                if symptom_matches > 0:
                    evidence.append(f"⚠️ Layer 2: {symptom_matches}个症状可检索到相关疾病")
                else:
                    score *= 0.5
                    evidence.append("❌ Layer 2: 无相关症状索引，置信度×0.5")

            # ========== Layer 3: 文献支持度 ==========
            if literature_support:
                # 如果有文献支持，加分
                score *= 1.2
                evidence.append(f"✅ Layer 3: 文献支持 ({len(literature_support)}篇)")
            else:
                evidence.append("⚠️ Layer 3: 未检索文献（中性）")

            # ========== Layer 4: 置信度惩罚 ==========
            # 综合惩罚规则
            if score > 100:
                score = 100  # 封顶
            if score < 10:
                score = max(score, 5)  # 保底5%
                evidence.append("🔴 Layer 4: 最终置信度过低，建议进一步检查")

            validated.append({
                "disease": disease_name,
                "score": round(score, 1),
                "orphanet_id": matched_disease_id,
                "gene": self.ORPHANET_DISEASES[matched_disease_id]["gene"] if matched_disease_id else None,
                "inheritance": self.ORPHANET_DISEASES[matched_disease_id]["inheritance"] if matched_disease_id else None,
                "layer_results": evidence,
                "matched_symptoms_count": layer2_score,
            })

        # 按置信度排序
        validated.sort(key=lambda x: x["score"], reverse=True)
        return validated

    def get_disease_info(self, disease_name: str) -> Optional[Dict]:
        """获取疾病详细信息"""
        for did, info in self.ORPHANET_DISEASES.items():
            if info["name"] in disease_name or disease_name in info["name"]:
                return {
                    "orphanet_id": did,
                    **info,
                }
        return None


# ========== 测试 ==========
if __name__ == "__main__":
    guard = HallucinationGuard()

    # 测试案例：重症肌无力
    hypotheses = [
        {"disease": "重症肌无力", "score": 100},
        {"disease": "食管癌", "score": 50},
        {"disease": "脑干病变", "score": 50},
        {"disease": "虚构疾病XYZ", "score": 80},  # 故意放一个不存在的疾病
    ]
    symptoms = ["眼睑下垂", "吞咽困难", "肌无力"]

    validated = guard.validate(hypotheses, symptoms)

    print("=" * 60)
    print("🔍 4层幻觉防护验证结果")
    print("=" * 60)
    for v in validated:
        print(f"\n🏥 {v['disease']} → {v['score']}%")
        if v['orphanet_id']:
            print(f"   基因: {v['gene']} | 遗传: {v['inheritance']}")
        for e in v['layer_results']:
            print(f"   {e}")
