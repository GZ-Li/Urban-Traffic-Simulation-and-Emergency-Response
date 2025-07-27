import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 微软雅黑
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# Configuration
DATA_PATH = 'E:\\Traffic_Simulation\\Adverse_weather_traffic\\snowplow_res_demand_Parlato.json'
BASELINE_PATH = 'E:\\Traffic_Simulation\\Adverse_weather_traffic\\snowplow_res_demand.json'
METRIC_INDEX = 3  # 0-5
TIMESTEP = "12000"

# Metric metadata
METRICS = [
    {"name": "Lane Congestion Ratio", "unit": "%", "direction": "small"},
    {"name": "Avg Lane Queue Length", "unit": "vehicles", "direction": "small"},
    {"name": "Global Avg Speed", "unit": "m/s", "direction": "large"},
    {"name": "Junction Congestion", "unit": "%", "direction": "small"},
    {"name": "Avg Junction Queue", "unit": "vehicles", "direction": "small"},
    {"name": "Junction Avg Speed", "unit": "m/s", "direction": "large"}
]

# Load data
with open(DATA_PATH, 'r') as f:
    strategy_data = json.load(f)
with open(BASELINE_PATH, 'r') as f:
    none_data = json.load(f)

cleaning_ratios = sorted([float(p) for p in strategy_data.keys()])  # 移除0%
x_values = [r*100 for r in cleaning_ratios]  # Convert to percentage

# Calculate improvement percentages (without 0% point)
baseline_value = none_data['none'][TIMESTEP][METRIC_INDEX]
improvements = []

for ratio in cleaning_ratios:
    current = strategy_data[str(ratio)][TIMESTEP][METRIC_INDEX]
    
    if METRICS[METRIC_INDEX]["direction"] == "large":
        imp = (current - baseline_value) / baseline_value * 100
    else:
        imp = (baseline_value - current) / baseline_value * 100
    improvements.append(imp)

# 手动修正特定值（根据您的需求）
improvements[0] = 5.3
improvements[1] = 15.8
improvements[2] = 23.37  # 对应x_values[2]位置的值

# Create visualization
plt.figure(figsize=(12, 6), dpi=100)
ax = plt.gca()

# Main trend line (starting from first actual data point)
main_line, = plt.plot(x_values, improvements, 
                     color='#3498DB', linewidth=3, 
                     marker='o', markersize=8,
                     markerfacecolor='white',
                     markeredgewidth=2,
                     label='优化趋势')

# Annotate marginal gains
for i in range(1, len(x_values)):
    delta_x = x_values[i] - x_values[i-1]
    delta_y = improvements[i] - improvements[i-1]
    
    mid_x = (x_values[i-1] + x_values[i]) / 2
    mid_y = (improvements[i-1] + improvements[i]) / 2
    
    ax.annotate(f"Δ{delta_y:.1f}%", 
               xy=(mid_x, mid_y),
               xytext=(0, 15), textcoords='offset points',
               ha='center', fontsize=9, 
               bbox=dict(boxstyle='round,pad=0.3', 
                        fc='white', ec='#7F8C8D', lw=0.5))

# Style enhancements
ax.set_facecolor('#F8F9F9')
plt.grid(True, linestyle='--', color='#BDC3C7', alpha=0.7)

# Reference lines
plt.axhline(0, color='#95A5A6', linestyle=':', linewidth=1)

# Labels and titles
plt.title('基于车道数量的优先扫雪策略', 
         pad=20, fontsize=14, fontweight='bold')
plt.xlabel('道路清扫百分比(%)', fontsize=12, labelpad=10)
plt.ylabel('拥堵路口比例改进(%)', fontsize=12, labelpad=10)
ax.yaxis.set_major_formatter(PercentFormatter())

# Adjust x-axis to start from first data point
plt.xlim(min(x_values)-5, 105)

# Legend and layout
legend = plt.legend(loc='upper left', bbox_to_anchor=(1, 1), 
                   frameon=True, framealpha=0.9)
legend.get_frame().set_edgecolor('#D5D8DC')

plt.tight_layout()
plt.show()