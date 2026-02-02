"""
可视化模块 - 比较不同算法的分配方案
"""
import matplotlib.pyplot as plt
import numpy as np
from config import VISUALIZATION_CONFIG


def setup_chinese_font():
    """设置中文字体"""
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False


def visualize_comparison(greedy_data, optimal_data, output_file=None):
    """
    可视化对比贪心算法和最优算法的分配方案
    
    Args:
        greedy_data: 贪心算法数据字典
            {
                'hospitals': ['医院1', ...],
                'tasks': [[('事故点1', start, end), ...], ...],
                'max_time': 最大完成时间
            }
        optimal_data: 最优算法数据字典（格式同上）
        output_file: 输出图片文件路径
    """
    setup_chinese_font()
    
    # 创建上下排版的图表
    fig, (ax1, ax2) = plt.subplots(
        2, 1, 
        figsize=VISUALIZATION_CONFIG['figsize']
    )
    
    # 自动计算时间轴范围
    time_max = max(greedy_data['max_time'], optimal_data['max_time']) + 200
    
    # 绘制贪心算法分配（上图）
    plot_assignment(
        ax1, 
        greedy_data['hospitals'], 
        greedy_data['tasks'],
        greedy_data['max_time'],
        time_max,
        "贪心算法分配"
    )
    
    # 绘制最优算法分配（下图）
    plot_assignment(
        ax2, 
        optimal_data['hospitals'], 
        optimal_data['tasks'],
        optimal_data['max_time'],
        time_max,
        "全局最优分配"
    )
    
    # 添加统一的时间刻度
    for ax in [ax1, ax2]:
        ax.set_xticks(np.arange(0, time_max + 1, 100))
        ax.set_xlabel('时间 (秒)', fontsize=12)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"可视化结果已保存到 {output_file}")
    
    plt.show()


def plot_assignment(ax, hospitals, tasks, max_time, time_max, title):
    """
    绘制单个分配方案
    
    Args:
        ax: matplotlib axes对象
        hospitals: 医院名称列表
        tasks: 任务列表 [[('事故点', start, end), ...], ...]
        max_time: 最大完成时间
        time_max: 时间轴最大值
        title: 图表标题
    """
    colors = plt.cm.Set3(np.linspace(0, 1, len(hospitals)))
    
    for i, (hospital, task_list) in enumerate(zip(hospitals, tasks)):
        for j, (accident, start, end) in enumerate(task_list):
            duration = end - start
            ax.barh(
                i, duration, left=start, 
                color=colors[i], edgecolor='black', 
                alpha=0.7 + j * 0.1
            )
            ax.text(
                start + duration/2, i, 
                f'{accident}\n{duration:.0f}s',
                ha='center', va='center', 
                fontweight='bold', 
                fontsize=VISUALIZATION_CONFIG['font_size']
            )
    
    ax.set_title(
        f'{title} - 最大响应时间: {max_time:.0f}秒', 
        fontsize=12, fontweight='bold', pad=20
    )
    ax.set_xlim(0, time_max)
    ax.set_ylim(-0.5, len(hospitals) - 0.5)
    ax.set_yticks(range(len(hospitals)))
    ax.set_yticklabels(hospitals)
    ax.axvline(x=max_time, color='red', linestyle='--', alpha=0.7, label=f'最大时间: {max_time:.0f}s')
    ax.grid(True, alpha=0.3, axis='x')
    ax.legend(loc='upper right')


def print_performance_comparison(greedy_max_time, optimal_max_time):
    """
    打印性能对比分析
    
    Args:
        greedy_max_time: 贪心算法的最大完成时间
        optimal_max_time: 最优算法的最大完成时间
    """
    improvement = (greedy_max_time - optimal_max_time) / greedy_max_time * 100
    
    print("=" * 50)
    print("性能对比分析")
    print("=" * 50)
    print(f"{'指标':<20} {'贪心算法':<15} {'全局最优':<15} {'改进幅度':<15}")
    print(f"{'-' * 50}")
    print(f"{'最大响应时间':<20} {f'{greedy_max_time:.0f}秒':<15} {f'{optimal_max_time:.0f}秒':<15} {f'{improvement:.1f}%':<15}")
    print("=" * 50)


if __name__ == "__main__":
    # 示例数据
    greedy_data = {
        'hospitals': ['医院4', '医院5', '医院6'],
        'tasks': [
            [('事故点5', 0, 180), ('事故点2', 180, 420), ('事故点1', 420, 740)],
            [('事故点3', 0, 480)],
            [('事故点4', 0, 360)]
        ],
        'max_time': 740
    }
    
    optimal_data = {
        'hospitals': ['医院1', '医院2', '医院4', '医院5', '医院6'],
        'tasks': [
            [('事故点5', 0, 480)],
            [('事故点1', 0, 500)],
            [('事故点2', 0, 240)],
            [('事故点3', 0, 480)],
            [('事故点4', 0, 360)]
        ],
        'max_time': 500
    }
    
    # 可视化对比
    visualize_comparison(greedy_data, optimal_data)
    
    # 打印对比
    print_performance_comparison(greedy_data['max_time'], optimal_data['max_time'])
