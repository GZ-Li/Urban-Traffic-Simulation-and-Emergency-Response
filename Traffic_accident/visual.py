import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建上下排版的图表
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# 设置统一的时间轴范围
time_max = 800  # 以贪心算法的最大时间740s为基准，留一些余量

# 贪心算法分配（上图）
greedy_hospitals = ['医院4', '医院5', '医院6']
greedy_tasks = [
    [('事故点5', 0, 180), ('事故点2', 180, 420), ('事故点1', 420, 740)],  # 医院4
    [('事故点3', 0, 480)],  # 医院5
    [('事故点4', 0, 360)]   # 医院6
]

greedy_colors = ['lightcoral', 'lightblue', 'lightgreen']

for i, (hospital, tasks) in enumerate(zip(greedy_hospitals, greedy_tasks)):
    for j, (accident, start, end) in enumerate(tasks):
        duration = end - start
        ax1.barh(hospital, duration, left=start, color=greedy_colors[i], 
                edgecolor='black', alpha=0.7 + j*0.1)
        ax1.text(start + duration/2, i, f'{accident}\n{duration}s', 
                ha='center', va='center', fontweight='bold', fontsize=10)

# ax1.set_xlabel('时间 (秒)')
# ax1.set_title('贪心算法分配 - 最大响应时间: 740秒', fontsize=12, fontweight='bold', pad=20)
ax1.set_xlim(0, time_max)
ax1.set_ylim(-0.5, len(greedy_hospitals)-0.5)
ax1.axvline(x=740, color='red', linestyle='--', alpha=0.7)
ax1.grid(True, alpha=0.3, axis='x')
ax1.legend()

# 全局最优分配（下图）
optimal_hospitals = ['医院1', '医院2', '医院4', '医院5', '医院6']
optimal_tasks = [
    [('事故点5', 0, 480)],  # 医院1
    [('事故点1', 0, 500)],  # 医院2
    [('事故点2', 0, 240)],  # 医院4
    [('事故点3', 0, 480)],  # 医院5
    [('事故点4', 0, 360)]   # 医院6
]

optimal_colors = ['gold', 'lavender', 'lightcoral', 'lightblue', 'lightgreen']

for i, (hospital, tasks) in enumerate(zip(optimal_hospitals, optimal_tasks)):
    for accident, start, end in tasks:
        duration = end - start
        ax2.barh(hospital, duration, left=start, color=optimal_colors[i], 
                edgecolor='black', alpha=0.8)
        ax2.text(start + duration/2, i, f'{accident}\n{duration}s', 
                ha='center', va='center', fontweight='bold', fontsize=10)

# ax2.set_xlabel('时间 (秒)')
# ax2.set_title('全局最优分配 - 最大响应时间: 500秒', fontsize=12, fontweight='bold', pad=20)
ax2.set_xlim(0, time_max)
ax2.set_ylim(-0.5, len(optimal_hospitals)-0.5)
ax2.axvline(x=500, color='red', linestyle='--', alpha=0.7)
ax2.grid(True, alpha=0.3, axis='x')
ax2.legend()

# 添加统一的时间刻度
for ax in [ax1, ax2]:
    ax.set_xticks(np.arange(0, time_max + 1, 100))
    ax.set_xticklabels([f'{int(x)}' for x in np.arange(0, time_max + 1, 100)])

plt.tight_layout()
plt.show()

# 打印统计信息
print("=" * 50)
print("性能对比分析")
print("=" * 50)
print(f"{'指标':<15} {'贪心算法':<12} {'全局最优':<12} {'改进幅度':<12}")
print(f"{'-'*50}")
print(f"{'最大响应时间':<15} {'740秒':<12} {'500秒':<12} {'-32.4%':<12}")
print(f"{'总响应时间':<15} {'1580秒':<12} {'2060秒':<12} {'+30.4%':<12}")
print(f"{'平均响应时间':<15} {'316秒':<12} {'412秒':<12} {'+30.4%':<12}")
print(f"{'涉及医院数':<15} {'3个':<12} {'5个':<12} {'+2个':<12}")
print(f"{'资源利用率':<15} {'高':<12} {'中等':<12} {'-':<12}")