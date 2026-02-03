"""
可视化积水排放策略对比：累计通过量和平均速度
"""

import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 从报告中提取的数据
batches = [0, 1, 2, 3]  # 排放批次
drained = [0, 3, 6, 9]  # 已排放的涝点数

# Best策略数据
best_throughput = [373, 681, 932, 1043]  # 通过量（辆/200秒）
best_queue = [970.79, 814.36, 685.82, 553.68]  # 平均排队长度
best_speed = [1.236, 1.967, 3.552, 4.615]  # 平均速度(m/s)

# Random策略数据
random_throughput = [373, 502, 777, 1043]  # 通过量（辆/200秒）
random_queue = [970.79, 836.75, 709.51, 553.68]  # 平均排队长度
random_speed = [1.236, 1.566, 3.065, 4.615]  # 平均速度(m/s)

# 创建图表
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 创建图表
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ============ 图1: 通过量对比（柱状图）============
ax1 = axes[0]
x = np.arange(len(drained))
width = 0.35

bars1 = ax1.bar(x - width/2, best_throughput, width, 
               label='最优策略 (best)', color='#FF6B6B', alpha=0.8)
bars2 = ax1.bar(x + width/2, random_throughput, width, 
               label='随机策略 (random)', color='#4ECDC4', alpha=0.8)

ax1.set_xlabel('已排放涝点数', fontsize=12)
ax1.set_ylabel('通过量 (辆/200秒)', fontsize=12)
ax1.set_title('200秒内通过量对比', fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(drained)
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3, axis='y')

# 在柱子上标注数值
for bar in bars1:
    height = bar.get_height()
    ax1.annotate(f'{int(height)}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9, fontweight='bold')
for bar in bars2:
    height = bar.get_height()
    ax1.annotate(f'{int(height)}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

# ============ 图2: 平均速度对比 ============
ax2 = axes[1]
ax2.plot(drained, best_speed, marker='o', linewidth=2.5, 
         label='最优策略 (best)', color='#FF6B6B', markersize=8)
ax2.plot(drained, random_speed, marker='s', linewidth=2.5, 
         label='随机策略 (random)', color='#4ECDC4', markersize=8)
ax2.set_xlabel('已排放涝点数', fontsize=12)
ax2.set_ylabel('平均速度 (m/s)', fontsize=12)
ax2.set_title('积水区域平均速度变化', fontsize=14, fontweight='bold')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)

# 在图上标注数值
for i, (x, y) in enumerate(zip(drained, best_speed)):
    if i > 0:
        ax2.annotate(f'{y:.2f}', (x, y), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9, color='#FF6B6B')
for i, (x, y) in enumerate(zip(drained, random_speed)):
    if i > 0:
        ax2.annotate(f'{y:.2f}', (x, y), textcoords="offset points", 
                    xytext=(0,-15), ha='center', fontsize=9, color='#4ECDC4')

plt.tight_layout()

# 保存图表
output_path = 'results/comparison_final/metrics_visualization.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✓ 可视化图表已保存: {output_path}")

pdf_path = 'results/comparison_final/metrics_visualization.pdf'
plt.savefig(pdf_path, bbox_inches='tight')
print(f"✓ PDF版本已保存: {pdf_path}")

plt.show()

print("\n" + "="*80)
print("指标说明:")
print("="*80)
print("""
1. 通过量 (Throughput per 200s):
   - 定义: 在单次仿真的200秒内，成功离开积水区域的车辆总数
   - 意义: 反映在该排放条件下的通行能力
   - 注意: 每个batch都是独立仿真，数值不能跨batch累加
   - 用柱状图: 因为每个batch是独立的测量值，不是连续变化
   
2. 平均速度 (Avg Speed):
   - 定义: 积水区域内所有车辆的平均行驶速度
   - 意义: 反映交通流畅度，速度越高说明拥堵越轻
   - 单位: 米/秒 (m/s)
   - 用折线图: 因为速度随排放增加而连续提升
   
3. 关系解读:
   - 随着排放涝点增加，积水消退，车辆速度上升
   - 速度上升使得更多车辆能在相同时间内通过积水区
   - 最优策略通过优先排放关键涝点，同时提升速度和通过量
""")
print("="*80)
