"""
优化求解模块 - 使用匈牙利算法求解最优分配
"""
from scipy.optimize import linear_sum_assignment
import pandas as pd
import numpy as np
import os
from config import EXPERIMENT_RESULTS_DIR


def solve_optimal_assignment(time_matrix):
    """
    使用二分搜索+匈牙利算法求解最小最大化分配问题
    
    Args:
        time_matrix: 时间矩阵，shape=(num_hospitals, num_accidents)
    
    Returns:
        best_total_time: 最优的最大完成时间
        best_assignment: 最优分配方案 [事故点索引, 医院索引, 时间]
    """
    time_matrix = np.array(time_matrix)
    time_matrix = np.nan_to_num(time_matrix, nan=1000)
    
    num_hospitals, num_accidents = time_matrix.shape
    
    # 二分搜索最大完成时间
    low = np.min(time_matrix)
    high = np.max(time_matrix)
    best_total_time = high
    best_assignment = None
    
    while low <= high:
        mid = (low + high) // 2
        # 构建二分匹配矩阵：医院i能否在mid时间内到达事故点j
        cost_matrix = np.where(time_matrix <= mid, 0, 1e6)
        
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # 检查分配是否可行
        if all(cost_matrix[r, c] < 1e6 for r, c in zip(row_ind, col_ind) if c < num_accidents):
            # 可行，尝试更小的最大完成时间
            best_total_time = mid
            best_assignment = [col_ind.tolist(), row_ind.tolist()]
            high = mid - 1
        else:
            # 不可行，需要更大的时间
            low = mid + 1
    
    # 将最佳分配转换为事故点 -> 医院
    row_ind, col_ind = linear_sum_assignment(
        np.where(time_matrix <= best_total_time, 0, 1e6)
    )
    assignments = []
    for r, c in zip(row_ind, col_ind):
        if c < num_accidents:
            assignments.append((c, r, time_matrix[r, c]))
    
    return best_total_time, assignments


def solve_greedy_assignment(time_matrix):
    """
    贪心算法求解分配问题（对比基准）
    
    Args:
        time_matrix: 时间矩阵，shape=(num_hospitals, num_accidents)
    
    Returns:
        makespan: 并行完成时间（最大医院总用时）
        assignments: 分配方案 [事故点索引, 医院索引, 时间]
        hospital_workload: 每个医院的总工作时间
    """
    time_matrix = np.array(time_matrix)
    num_hospitals, num_accidents = time_matrix.shape
    
    assignments = []
    hospital_workload = [0] * num_hospitals
    
    for acc_idx in range(num_accidents):
        hosp_idx = np.argmin(time_matrix[:, acc_idx])
        t = time_matrix[hosp_idx, acc_idx]
        assignments.append((acc_idx, hosp_idx, t))
        hospital_workload[hosp_idx] += t
    
    makespan = max(hospital_workload)
    
    return makespan, assignments, hospital_workload


def compare_algorithms(exp_results_dir, num_experiments=20):
    """
    比较最优算法和贪心算法的性能
    
    Args:
        exp_results_dir: 实验结果目录
        num_experiments: 实验数量
    
    Returns:
        optimal_results: 最优算法结果列表
        greedy_results: 贪心算法结果列表
    """
    optimal_results = []
    greedy_results = []
    
    for i in range(num_experiments):
        csv_path = os.path.join(exp_results_dir, f'experiment_{i+1}.csv')
        
        if not os.path.exists(csv_path):
            print(f"⚠️ 文件不存在: {csv_path}")
            continue
        
        time_matrix = pd.read_csv(csv_path)
        time_matrix = np.array(time_matrix.iloc[:, 1:])
        time_matrix = np.nan_to_num(time_matrix, nan=1000)
        
        # 最优算法
        best_time, best_assign = solve_optimal_assignment(time_matrix)
        optimal_results.append(best_time)
        
        # 贪心算法
        greedy_time, greedy_assign, _ = solve_greedy_assignment(time_matrix)
        greedy_results.append(greedy_time)
        
        print(f"实验 {i+1}:")
        print(f"  最优算法: {best_time}s")
        print(f"  贪心算法: {greedy_time}s")
        print(f"  改进: {greedy_time - best_time}s ({(greedy_time - best_time) / greedy_time * 100:.2f}%)")
        print()
    
    return optimal_results, greedy_results


def print_comparison_statistics(optimal_results, greedy_results):
    """
    打印对比统计信息
    
    Args:
        optimal_results: 最优算法结果列表
        greedy_results: 贪心算法结果列表
    """
    print("=" * 60)
    print("算法性能对比统计")
    print("=" * 60)
    
    optimal_avg = np.mean(optimal_results)
    greedy_avg = np.mean(greedy_results)
    improvement = (greedy_avg - optimal_avg) / greedy_avg * 100
    
    print(f"最优算法平均时间: {optimal_avg:.2f}s")
    print(f"贪心算法平均时间: {greedy_avg:.2f}s")
    print(f"平均改进: {improvement:.2f}%")
    print()
    
    # 统计有多少次最优算法更好
    better_count = sum(1 for i in range(len(optimal_results)) 
                      if optimal_results[i] < greedy_results[i])
    print(f"最优算法胜出次数: {better_count}/{len(optimal_results)}")
    print("=" * 60)


if __name__ == "__main__":
    # 运行对比实验
    optimal_res, greedy_res = compare_algorithms(
        exp_results_dir=EXPERIMENT_RESULTS_DIR,
        num_experiments=20
    )
    
    # 打印统计信息
    print_comparison_statistics(optimal_res, greedy_res)
