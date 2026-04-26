"""药企定价与ROI模型"""

PLANS = {
    'basic': {'name': '基础版', 'price': 50000, 'drugs': 1, 'patients': 500,
              'features': ['患者教育', '用药提醒', '基础数据报告']},
    'pro': {'name': '专业版', 'price': 150000, 'drugs': 3, 'patients': 2000,
            'features': ['患者教育', '用药提醒', '高级数据分析', '依从性预警', '定制内容']},
    'enterprise': {'name': '企业版', 'price': 500000, 'drugs': float('inf'), 'patients': float('inf'),
                   'features': ['全部功能', 'API接入', '专属客户成功经理', 'SLA保障', '数据合规审计']},
}

def calculate_roi(plan_id, avg_annual_drug_price, current_adherence, patients_count):
    plan = PLANS.get(plan_id, PLANS['basic'])
    expected_improvement = 0.12
    retained = int(patients_count * expected_improvement)
    additional_revenue = retained * avg_annual_drug_price
    roi = ((additional_revenue - plan['price']) / plan['price']) * 100 if plan['price'] else 0
    return {
        'plan': plan['name'], 'plan_cost': plan['price'], 'patients': patients_count,
        'expected_adherence_improvement': '12%', 'retained_patients': retained,
        'additional_revenue': additional_revenue, 'roi_percentage': round(roi, 1),
        'payback_days': round(plan['price'] / (additional_revenue / 365), 0) if additional_revenue else 0
    }
