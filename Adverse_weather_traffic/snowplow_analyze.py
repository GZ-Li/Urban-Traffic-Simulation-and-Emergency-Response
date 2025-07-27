import json
import numpy as np
from collections import defaultdict

# 1. 加载原始数据
with open("E:\\Traffic_Simulation\\Adverse_weather_traffic\\snowplow_res_lanenum.json", 'r') as f:
    data = json.load(f)

# 2. 定义指标名称（根据你的数据顺序）
metric_names = [
    "lane_cong_ratio", "lane_avg_queue_len", "global_avg_speed", "junction_cong_ratio", "junction_avg_queue_len", "junction_avg_speed"
]

# 3. 处理数据并计算排序和提升百分比
results = defaultdict(dict)

for timestep in ["7000", "8000", "9000", "10000", "11000", "12000", "13000", "14000"]:
    # 获取当前时间步所有策略的数据
    timestep_data = {}
    for strategy in data.keys():
        if timestep in data[strategy]:
            timestep_data[strategy] = data[strategy][timestep]
    
    # 对每个指标进行处理
    for metric_idx in range(6):  # 你的6个指标
        # 获取当前指标的所有策略值
        metric_values = {s: v[metric_idx] for s, v in timestep_data.items()}
        
        # 按值排序（假设所有指标都是越大越好，如果不是需要调整）
        sorted_strategies = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
        
        # 计算提升百分比
        improvements = []
        for i in range(len(sorted_strategies)-1):
            current_val = sorted_strategies[i][1]
            next_val = sorted_strategies[i+1][1]
            
            if next_val != 0:  # 避免除以零
                improvement = ((current_val - next_val) / next_val) * 100
            else:
                improvement = float('inf')  # 无穷大
            
            improvements.append(improvement)
        
        # 存储结果
        results[timestep][metric_names[metric_idx]] = {
            "ranking": [{"strategy": s, "value": v} for s, v in sorted_strategies],
            "improvements": improvements
        }

# 4. 保存结果到新JSON文件
output = {
    "metrics": metric_names,
    "results": dict(results)
}

with open('snowplow_res_lanenum_summary.json', 'w') as f:
    json.dump(output, f, indent=4)