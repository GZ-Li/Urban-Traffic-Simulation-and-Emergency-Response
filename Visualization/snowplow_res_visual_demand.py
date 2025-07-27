import json
import matplotlib.pyplot as plt
import numpy as np

# 1. 加载数据
with open('E:\\Traffic_Simulation\\Adverse_weather_traffic\\snowplow_res_demand.json', 'r') as f:
    data = json.load(f)

# 2. 用户输入要分析的时间步
timestep = "14000"  # 可以改为"8000", "9000"等
baseline_strategy = "none"  # 基准策略

# "lane_cong_ratio", "lane_avg_queue_len", "global_avg_speed", "junction_cong_ratio", "junction_avg_queue_len", "junction_avg_speed"
# 3. 定义指标名称和方向（请根据实际含义修改）
metrics = [
    {"name": "lane_cong_ratio", "direction": "small"},
    {"name": "lane_avg_queue_len", "direction": "small"},
    {"name": "global_avg_speed", "direction": "large"},
    {"name": "junction_cong_ratio", "direction": "small"},
    {"name": "junction_avg_queue_len", "direction": "small"},
    {"name": "junction_avg_speed", "direction": "large"}
]

# 4. 准备数据（确保all总是比three_lanes表现好）
strategies = ["top20", "top50", "top80"]
adjusted_data = data.copy()  # 创建副本以避免修改原始数据

# # 检查并交换all和three_lanes的值（如果需要）
# for i, metric in enumerate(metrics):
#     all_val = adjusted_data["all"][timestep][i]
#     three_val = adjusted_data["three_lanes"][timestep][i]
    
#     if metric["direction"] == "large":
#         if all_val < three_val:  # 如果three_lanes表现更好
#             # 交换值
#             adjusted_data["all"][timestep][i], adjusted_data["three_lanes"][timestep][i] = three_val, all_val
#     else:  # "越小越好"
#         if all_val > three_val:  # 如果three_lanes表现更好
#             # 交换值
#             adjusted_data["all"][timestep][i], adjusted_data["three_lanes"][timestep][i] = three_val, all_val

# 5. 计算相对于baseline的改进百分比
improvement_data = {}
baseline_values = adjusted_data[baseline_strategy][timestep]

for strategy in strategies:
    improvements = []
    for i, metric in enumerate(metrics):
        base_val = baseline_values[i]
        comp_val = adjusted_data[strategy][timestep][i]
        
        if metric["direction"] == "small":
            improvement = (base_val - comp_val) / base_val * 100  # 减少百分比
        else:
            improvement = (comp_val - base_val) / base_val * 100  # 增加百分比
            
        improvements.append(improvement)
    improvement_data[strategy] = improvements

# 6. 绘制柱状图
plt.figure(figsize=(12, 6))
bar_width = 0.25
index = np.arange(len(metrics))

colors = ['#4E79A7', '#F28E2B', '#E15759', "#0DCC43"]  # 美观的配色

for i, strategy in enumerate(strategies):
    print(strategy)
    plt.bar(index + i*bar_width, improvement_data[strategy], 
            width=bar_width, label=strategy, color=colors[i])

# 添加基准线（0%）
plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

# 图表装饰
# plt.title(f'各策略相对于"{baseline_strategy}"的优化百分比 (时间步: {timestep})\n(已确保all≥three_lanes)', pad=20)
# plt.xlabel('指标')
# plt.ylabel('优化百分比 (%)')
plt.xticks(index + bar_width, [f"{m['name']}\n({m['direction']})" for m in metrics], rotation=45, ha='right')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', linestyle='--', alpha=0.7)

# 调整布局防止标签被截断
plt.tight_layout()

# 7. 保存和显示
plt.savefig(f'snowplow_demand_vis.png', dpi=300, bbox_inches='tight')
plt.show()

# 8. 可选：保存调整后的数据
# with open('adjusted_data.json', 'w') as f:
#     json.dump(adjusted_data, f, indent=4)