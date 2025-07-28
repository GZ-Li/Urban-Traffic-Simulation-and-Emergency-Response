import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 微软雅黑
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

with open('simulation_results\\snowplow_res_lanenum.json', 'r') as f:
    data = json.load(f)
timestep = "9000"
baseline_strategy = "none"
strategies = ["three_lanes", "two_lanes", "one_lane"]  # 对比策略

metrics = [
    {"name": "缩短平均排队长度", "short": "lane_queue", "unit": "veh", "direction": "small", "original_idx": 1},
    {"name": "提升平均行驶速度", "short": "speed", "unit": "m/s", "direction": "large", "original_idx": 2},
    {"name": "减少路口拥堵比例", "short": "junc_cong", "unit": "%", "direction": "small", "original_idx": 3},
]

improvement_data = {}
baseline_values = data[baseline_strategy][timestep]

for strategy in strategies:
    improvements = []
    for metric in metrics:
        base_val = baseline_values[metric["original_idx"]]
        comp_val = data[strategy][timestep][metric["original_idx"]]
        
        if metric["direction"] == "small":
            imp = (base_val - comp_val) / base_val * 100
        else:
            imp = (comp_val - base_val) / base_val * 100
        improvements.append(imp)
    improvement_data[strategy] = improvements

plt.figure(figsize=(10, 6), dpi=100)
ax = plt.gca()

colors = ["#3498DB", "#2ECC71", "#E74C3C"]
bar_width = 0.2
index = np.arange(len(metrics))
for i, strategy in enumerate(strategies):
    bars = ax.bar(index + i*bar_width, improvement_data[strategy],
                 width=bar_width, color=colors[i],
                 edgecolor='white', linewidth=1,
                  alpha=0.9,
                 label=strategy.replace("_", " ").title())

for i, strategy in enumerate(strategies):
    for j, val in enumerate(improvement_data[strategy]):
        ax.text(index[j] + i*bar_width, 
                val + (0.2 if val >=0 else -0.4), 
                f"{val:.1f}%",
                ha='center', va='bottom' if val >=0 else 'top',
                fontsize=10)

ax.set_xticks(index + bar_width/2)
ax.set_xticklabels([f"{m['name']}" for m in metrics],
                  fontsize=11)

ax.yaxis.set_major_formatter(PercentFormatter())
ax.set_ylabel('百分比', fontsize=12)
ax.set_title(f'对比未清障时的交通效率提升',
             fontsize=14, pad=20, fontweight='bold')

ax.axhline(0, color='gray', linestyle=':', linewidth=1)
ax.grid(axis='y', linestyle='--', alpha=0.6)

ax.legend(loc='upper left', bbox_to_anchor=(1, 1),
          frameon=True, framealpha=0.9)

plt.tight_layout()

output_file = f"key_metrics_comparison_{timestep}.png"
# plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
# print(f"Chart saved to: {output_file}")
plt.show()