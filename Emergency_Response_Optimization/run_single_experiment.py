"""
单次实验运行脚本 - 简化版本

适用场景：
- 只有一个时间矩阵，想快速看到优化结果
- 不需要批量对比，只需要单次分析
- 快速验证算法效果
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import pandas as pd
from src.optimization import solve_optimal_assignment, solve_greedy_assignment
from src.visualization import visualize_comparison, print_performance_comparison


def run_single_experiment(time_matrix):
    """
    运行单次实验，对比最优算法和贪心算法
    
    Args:
        time_matrix: 时间矩阵 (医院 × 事故点)
    
    Returns:
        包含优化结果的字典
    """
    print("\n" + "="*60)
    print("🚑 应急响应优化 - 单次实验")
    print("="*60 + "\n")
    
    # 显示输入数据
    print("📊 输入时间矩阵:")
    print(f"   医院数量: {time_matrix.shape[0]}")
    print(f"   事故点数量: {time_matrix.shape[1]}")
    print()
    
    df = pd.DataFrame(
        time_matrix,
        index=[f"医院{i+1}" for i in range(time_matrix.shape[0])],
        columns=[f"事故点{i+1}" for i in range(time_matrix.shape[1])]
    )
    print(df)
    print()
    
    # 运行最优算法
    print("🎯 运行最优算法（匈牙利算法 + 二分搜索）...")
    optimal_time, optimal_assign = solve_optimal_assignment(time_matrix)
    
    # 运行贪心算法
    print("⚡ 运行贪心算法（对比基准）...")
    greedy_time, greedy_assign, hospital_workload = solve_greedy_assignment(time_matrix)
    
    # 显示结果
    print("\n" + "="*60)
    print("📈 实验结果")
    print("="*60 + "\n")
    
    print(f"{'算法':<15} {'最大响应时间':<15} {'状态':<10}")
    print("-" * 60)
    print(f"{'最优算法':<15} {f'{optimal_time:.0f}秒':<15} {'✅ 推荐':<10}")
    print(f"{'贪心算法':<15} {f'{greedy_time:.0f}秒':<15} {'📊 对比':<10}")
    print()
    
    improvement = (greedy_time - optimal_time) / greedy_time * 100
    if improvement > 0:
        print(f"💡 性能提升: {improvement:.1f}% (节省 {greedy_time - optimal_time:.0f}秒)")
    elif improvement < 0:
        print(f"⚠️  贪心算法更优: {abs(improvement):.1f}%")
    else:
        print("ℹ️  两种算法结果相同")
    
    print("\n" + "-"*60)
    print("📋 最优分配方案:")
    print("-"*60)
    for acc_idx, hosp_idx, time in sorted(optimal_assign):
        print(f"   事故点 {acc_idx+1} ← 医院 {hosp_idx+1}  ({time:.0f}秒)")
    
    print("\n" + "-"*60)
    print("📋 贪心分配方案:")
    print("-"*60)
    for acc_idx, hosp_idx, time in sorted(greedy_assign):
        print(f"   事故点 {acc_idx+1} ← 医院 {hosp_idx+1}  ({time:.0f}秒)")
    
    print("\n" + "-"*60)
    print("📊 医院工作负载（贪心算法）:")
    print("-"*60)
    for i, workload in enumerate(hospital_workload):
        bar = "█" * int(workload / 50)
        print(f"   医院{i+1}: {workload:.0f}秒  {bar}")
    
    return {
        'optimal_time': optimal_time,
        'optimal_assign': optimal_assign,
        'greedy_time': greedy_time,
        'greedy_assign': greedy_assign,
        'hospital_workload': hospital_workload,
        'improvement': improvement
    }


def example_with_sample_data():
    """使用示例数据运行"""
    print("\n使用示例数据运行实验...")
    
    # 示例时间矩阵 (6个医院 × 5个事故点)
    time_matrix = np.array([
        [180, 240, 480, 500, 480],  # 医院1
        [320, 350, 620, 700, 550],  # 医院2
        [370, 400, 640, 850, 830],  # 医院3
        [180, 240, 490, 540, 360],  # 医院4
        [480, 480, 490, 640, 750],  # 医院5
        [360, 450, 640, 880, 950],  # 医院6
    ])
    
    result = run_single_experiment(time_matrix)
    
    # 询问是否可视化
    print("\n" + "="*60)
    response = input("📊 是否生成可视化图表？(y/n): ").strip().lower()
    
    if response == 'y':
        print("\n生成可视化中...")
        
        # 准备可视化数据
        greedy_data = prepare_visualization_data(
            result['greedy_assign'], 
            result['greedy_time'],
            time_matrix.shape[0]
        )
        
        optimal_data = prepare_visualization_data(
            result['optimal_assign'], 
            result['optimal_time'],
            time_matrix.shape[0]
        )
        
        from src.visualization import visualize_comparison
        visualize_comparison(greedy_data, optimal_data, "results/single_experiment_result.png")
        print("✅ 可视化已保存到: results/single_experiment_result.png")


def prepare_visualization_data(assignments, max_time, num_hospitals):
    """准备可视化数据"""
    # 按医院分组任务
    hospital_tasks = {i: [] for i in range(num_hospitals)}
    
    for acc_idx, hosp_idx, time in assignments:
        hospital_tasks[hosp_idx].append((f"事故点{acc_idx+1}", 0, time))
    
    # 过滤掉没有任务的医院
    active_hospitals = [(f"医院{i+1}", tasks) 
                       for i, tasks in hospital_tasks.items() 
                       if tasks]
    
    hospitals = [h for h, _ in active_hospitals]
    tasks = [t for _, t in active_hospitals]
    
    return {
        'hospitals': hospitals,
        'tasks': tasks,
        'max_time': max_time
    }


def load_from_csv(csv_path):
    """从CSV文件加载时间矩阵"""
    print(f"\n📂 从CSV文件加载: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # 假设第一列是索引，其余是数据
    if df.columns[0] in ['Unnamed: 0', 'index', '']:
        time_matrix = np.array(df.iloc[:, 1:])
    else:
        time_matrix = np.array(df)
    
    # 处理NaN
    time_matrix = np.nan_to_num(time_matrix, nan=1000)
    
    return time_matrix


def interactive_input():
    """交互式输入时间矩阵"""
    print("\n📝 手动输入时间矩阵")
    print("-"*60)
    
    num_hospitals = int(input("医院数量: "))
    num_accidents = int(input("事故点数量: "))
    
    print(f"\n请输入 {num_hospitals} × {num_accidents} 的时间矩阵（秒）:")
    print("（每行输入一个医院到各事故点的时间，用空格分隔）")
    
    time_matrix = []
    for i in range(num_hospitals):
        row_input = input(f"医院{i+1}: ")
        row = [float(x) for x in row_input.split()]
        if len(row) != num_accidents:
            print(f"❌ 错误：需要{num_accidents}个值，但输入了{len(row)}个")
            return None
        time_matrix.append(row)
    
    return np.array(time_matrix)


def main():
    """主函数"""
    print("="*60)
    print("🚑 Emergency Response Optimization - 单次实验工具")
    print("="*60)
    
    print("\n请选择输入方式:")
    print("  1. 使用示例数据")
    print("  2. 从CSV文件加载")
    print("  3. 手动输入时间矩阵")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    
    if choice == '1':
        example_with_sample_data()
    
    elif choice == '2':
        csv_path = input("请输入CSV文件路径: ").strip()
        if os.path.exists(csv_path):
            time_matrix = load_from_csv(csv_path)
            result = run_single_experiment(time_matrix)
        else:
            print(f"❌ 文件不存在: {csv_path}")
    
    elif choice == '3':
        time_matrix = interactive_input()
        if time_matrix is not None:
            result = run_single_experiment(time_matrix)
    
    else:
        print("❌ 无效选项")
    
    print("\n" + "="*60)
    print("✅ 实验完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
