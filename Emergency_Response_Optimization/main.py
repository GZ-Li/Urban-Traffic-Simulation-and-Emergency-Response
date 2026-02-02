"""
主程序 - 完整的优化流程示例
"""
import os
import sys
import pandas as pd
import numpy as np

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import *
from src.optimization import solve_optimal_assignment, solve_greedy_assignment
from src.visualization import visualize_comparison, print_performance_comparison


def run_single_experiment(time_matrix):
    """
    运行单次实验，对比最优算法和贪心算法
    
    Args:
        time_matrix: 时间矩阵
    
    Returns:
        optimal_result: 最优算法结果
        greedy_result: 贪心算法结果
    """
    # 最优算法
    optimal_time, optimal_assign = solve_optimal_assignment(time_matrix)
    
    # 贪心算法
    greedy_time, greedy_assign, hospital_workload = solve_greedy_assignment(time_matrix)
    
    return {
        'optimal_time': optimal_time,
        'optimal_assign': optimal_assign,
        'greedy_time': greedy_time,
        'greedy_assign': greedy_assign,
        'hospital_workload': hospital_workload
    }


def load_experiment_data(exp_id):
    """
    加载实验数据
    
    Args:
        exp_id: 实验编号（1-based）
    
    Returns:
        time_matrix: 时间矩阵
    """
    csv_path = os.path.join(EXPERIMENT_RESULTS_DIR, f'experiment_{exp_id}.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"实验数据文件不存在: {csv_path}")
    
    df = pd.read_csv(csv_path)
    time_matrix = np.array(df.iloc[:, 1:])
    time_matrix = np.nan_to_num(time_matrix, nan=1000)
    
    return time_matrix


def demo_visualization():
    """
    演示可视化功能（使用示例数据）
    """
    print("\n" + "="*60)
    print("运行可视化演示")
    print("="*60 + "\n")
    
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
    output_file = os.path.join(RESULTS_DIR, "comparison_visualization.png")
    visualize_comparison(greedy_data, optimal_data, output_file)
    
    # 打印对比
    print_performance_comparison(greedy_data['max_time'], optimal_data['max_time'])


def main():
    """主函数"""
    print("="*60)
    print("Emergency Response Optimization System")
    print("交通事故应急响应优化系统")
    print("="*60 + "\n")
    
    # 检查实验数据
    os.makedirs(EXPERIMENT_RESULTS_DIR, exist_ok=True)
    
    # 尝试加载第一个实验数据
    try:
        print("尝试加载实验数据...")
        time_matrix = load_experiment_data(1)
        
        print(f"✅ 成功加载实验数据")
        print(f"   医院数量: {time_matrix.shape[0]}")
        print(f"   事故点数量: {time_matrix.shape[1]}")
        print()
        
        # 运行实验
        print("运行优化算法...")
        result = run_single_experiment(time_matrix)
        
        print("\n" + "="*60)
        print("实验结果")
        print("="*60)
        print(f"最优算法 - 最大响应时间: {result['optimal_time']:.0f}秒")
        print(f"贪心算法 - 最大响应时间: {result['greedy_time']:.0f}秒")
        improvement = (result['greedy_time'] - result['optimal_time']) / result['greedy_time'] * 100
        print(f"性能改进: {improvement:.2f}%")
        print()
        
        print("最优分配方案:")
        for acc_idx, hosp_idx, time in sorted(result['optimal_assign']):
            print(f"  事故点 {acc_idx+1} -> 医院 {hosp_idx+1}, 用时 {time:.0f}秒")
        
    except FileNotFoundError:
        print("⚠️ 未找到实验数据")
        print("   请先运行SUMO仿真生成实验数据，或查看README.md了解如何配置")
        print()
    
    # 运行可视化演示
    demo_visualization()
    
    print("\n" + "="*60)
    print("程序运行完成")
    print("="*60)


if __name__ == "__main__":
    main()
