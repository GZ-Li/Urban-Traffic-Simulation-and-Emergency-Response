"""
完整流程：从路网到优化结果（包含SUMO仿真）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.path_planning import sumo_net_to_networkx
from src.sumo_simulation import measure_hospital_accident_pairs
from src.optimization import solve_optimal_assignment, solve_greedy_assignment
from src.visualization import visualize_comparison
import pandas as pd
import numpy as np
import json

def run_complete_pipeline(sumo_net_file, hospital_file, sumo_config_file,
                          accident_spots, k_paths=5, use_gui=False):
    """
    完整流程：路网→路径生成→仿真→优化
    
    Args:
        sumo_net_file: SUMO路网文件
        hospital_file: 医院位置CSV文件
        sumo_config_file: SUMO仿真配置文件
        accident_spots: 事故点edge ID列表
        k_paths: 每对计算的路径数
        use_gui: 是否使用SUMO GUI
    """
    os.makedirs('results', exist_ok=True)
    
    print("="*60)
    print("🏥 Emergency Response Optimization - 完整流程")
    print("="*60)
    
    # ========== 步骤1: 加载路网 ==========
    print("\n【步骤1/5】加载SUMO路网")
    print("-"*60)
    
    if not os.path.exists(sumo_net_file):
        print(f"❌ 路网文件不存在: {sumo_net_file}")
        print("\n请配置:")
        print("1. 将SUMO路网文件放入data/目录")
        print("2. 修改src/config.py中的SUMO_NET_FILE")
        return
    
    print(f"加载路网: {sumo_net_file}")
    G = sumo_net_to_networkx(sumo_net_file)
    print(f"✅ 成功加载")
    print(f"   节点数: {G.number_of_nodes()}")
    print(f"   边数: {G.number_of_edges()}")
    
    # ========== 步骤2: 加载医院配置 ==========
    print("\n【步骤2/5】加载医院配置")
    print("-"*60)
    
    if not os.path.exists(hospital_file):
        print(f"❌ 医院文件不存在: {hospital_file}")
        return
    
    hospital_df = pd.read_csv(hospital_file)
    hospitals = {}
    for i, row in hospital_df.iterrows():
        hospitals[row['name']] = str(row['road_id'])
    
    print(f"✅ 加载 {len(hospitals)} 个医院:")
    for name, edge in list(hospitals.items())[:5]:
        print(f"   {name}: {edge}")
    if len(hospitals) > 5:
        print(f"   ... 共{len(hospitals)}个")
    
    print(f"\n✅ 配置 {len(accident_spots)} 个事故点:")
    for i, spot in enumerate(accident_spots[:5], 1):
        print(f"   事故点{i}: {spot}")
    if len(accident_spots) > 5:
        print(f"   ... 共{len(accident_spots)}个")
    
    # ========== 步骤3: 路径生成和仿真测量 ==========
    print("\n【步骤3/5】路径生成 + SUMO仿真测量")
    print("-"*60)
    
    routes_info, time_matrix = measure_hospital_accident_pairs(
        G, hospitals, accident_spots, 
        k_paths=k_paths,
        sumo_config_file=sumo_config_file,
        use_gui=use_gui
    )
    
    if time_matrix is None:
        print("❌ 未能生成时间矩阵")
        return
    
    # 保存路径信息
    with open('results/routes_info.json', 'w', encoding='utf-8') as f:
        # 转换为可序列化格式
        routes_export = []
        for route in routes_info:
            routes_export.append({
                'route_id': int(route['route_id']),
                'hospital_idx': int(route['hospital_idx']),
                'hospital_name': route['hospital_name'],
                'accident_idx': int(route['accident_idx']),
                'path_idx': int(route['path_idx']),
                'time': float(route['time']),
                'edges': route['edges'][:10]  # 只保存前10条边作为示例
            })
        json.dump(routes_export, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 路径信息已保存: results/routes_info.json")
    
    # 保存时间矩阵
    time_df = pd.DataFrame(
        time_matrix,
        index=[name for name in hospitals.keys()],
        columns=[f"事故点{i+1}" for i in range(len(accident_spots))]
    )
    time_df.to_csv('results/time_matrix.csv')
    print(f"✅ 时间矩阵已保存: results/time_matrix.csv")
    
    print("\n时间矩阵预览:")
    print(time_df)
    
    # ========== 步骤4: 运行优化算法 ==========
    print("\n【步骤4/5】运行优化算法")
    print("-"*60)
    
    optimal_time, optimal_assign = solve_optimal_assignment(time_matrix)
    greedy_time, greedy_assign, hospital_workload = solve_greedy_assignment(time_matrix)
    
    improvement = (greedy_time - optimal_time) / greedy_time * 100
    
    print(f"\n最优算法: {optimal_time:.0f}秒")
    print(f"贪心算法: {greedy_time:.0f}秒")
    print(f"性能提升: {improvement:.1f}%")
    
    # ========== 步骤5: 生成结果报告 ==========
    print("\n【步骤5/5】生成结果报告")
    print("-"*60)
    
    # 准备可视化数据（串行）
    hospital_list = list(hospitals.keys())
    
    # 贪心算法可视化数据
    hospital_tasks_greedy = {i: [] for i in range(len(hospitals))}
    hospital_cumulative_time = {i: 0 for i in range(len(hospitals))}
    
    for acc_idx, hosp_idx, time in sorted(greedy_assign):
        start_time = hospital_cumulative_time[hosp_idx]
        end_time = start_time + time
        hospital_tasks_greedy[hosp_idx].append((f"事故点{acc_idx+1}", start_time, end_time))
        hospital_cumulative_time[hosp_idx] = end_time
    
    active_hospitals_greedy = [(hospital_list[i], tasks) 
                               for i, tasks in hospital_tasks_greedy.items() 
                               if tasks]
    greedy_data = {
        'hospitals': [h for h, _ in active_hospitals_greedy],
        'tasks': [t for _, t in active_hospitals_greedy],
        'max_time': greedy_time
    }
    
    # 最优算法可视化数据
    hospital_tasks_optimal = {i: [] for i in range(len(hospitals))}
    hospital_cumulative_time_opt = {i: 0 for i in range(len(hospitals))}
    
    for acc_idx, hosp_idx, time in sorted(optimal_assign):
        start_time = hospital_cumulative_time_opt[hosp_idx]
        end_time = start_time + time
        hospital_tasks_optimal[hosp_idx].append((f"事故点{acc_idx+1}", start_time, end_time))
        hospital_cumulative_time_opt[hosp_idx] = end_time
    
    active_hospitals_optimal = [(hospital_list[i], tasks) 
                                for i, tasks in hospital_tasks_optimal.items() 
                                if tasks]
    optimal_data = {
        'hospitals': [h for h, _ in active_hospitals_optimal],
        'tasks': [t for _, t in active_hospitals_optimal],
        'max_time': optimal_time
    }
    
    # 生成可视化
    visualize_comparison(greedy_data, optimal_data, "results/final_result.png")
    print("✅ 可视化已保存: results/final_result.png")
    
    # 生成详细报告（包含路径）
    with open('results/final_result.txt', 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("应急响应优化完整流程结果\n")
        f.write("="*60 + "\n\n")
        
        f.write("【配置信息】\n")
        f.write(f"医院数量: {len(hospitals)}\n")
        f.write(f"事故点数量: {len(accident_spots)}\n")
        f.write(f"每对路径数: {k_paths}\n")
        f.write(f"总路径数: {len(routes_info)}\n\n")
        
        f.write("【时间矩阵】\n")
        f.write(time_df.to_string())
        f.write("\n\n")
        
        f.write("="*60 + "\n")
        f.write("【优化结果】\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"最优算法: {optimal_time:.0f}秒\n")
        f.write(f"贪心算法: {greedy_time:.0f}秒\n")
        f.write(f"性能提升: {improvement:.1f}%\n\n")
        
        f.write("-"*60 + "\n")
        f.write("【最优分配方案】（推荐）\n")
        f.write("-"*60 + "\n")
        
        for acc_idx, hosp_idx, time in sorted(optimal_assign):
            hosp_name = hospital_list[hosp_idx]
            f.write(f"\n事故点{acc_idx+1} ← {hosp_name}  ({time:.0f}秒)\n")
            
            # 查找对应的路径
            matching_routes = [r for r in routes_info 
                             if r['hospital_idx'] == hosp_idx 
                             and r['accident_idx'] == acc_idx
                             and abs(r['time'] - time) < 1]
            
            if matching_routes:
                best_route = min(matching_routes, key=lambda x: x['time'])
                edges = best_route['edges']
                if len(edges) <= 8:
                    f.write(f"  路径: {' → '.join(edges)}\n")
                else:
                    f.write(f"  路径: {edges[0]} → ... ({len(edges)}条边) ... → {edges[-1]}\n")
        
        f.write(f"\n最大响应时间: {optimal_time:.0f}秒\n")
        f.write(f"参与医院数: {len(active_hospitals_optimal)}个\n")
    
    print("✅ 详细报告已保存: results/final_result.txt")
    
    print("\n" + "="*60)
    print("✅ 完整流程执行完成！")
    print("="*60)
    print("\n生成的文件:")
    print("  - results/routes_info.json  # 所有路径详情")
    print("  - results/time_matrix.csv   # 时间矩阵")
    print("  - results/final_result.png  # 可视化对比")
    print("  - results/final_result.txt  # 详细报告（含路径）")


if __name__ == "__main__":
    from src.config import SUMO_NET_FILE, HOSPITAL_LOCATION_FILE, SIMULATION_CONFIG
    
    # 检查配置
    print("检查配置文件...")
    
    sumo_config = "data/simulation.sumocfg"  # 需要用户提供
    
    if not os.path.exists(SUMO_NET_FILE):
        print(f"\n❌ 请配置SUMO路网文件:")
        print(f"   当前配置: {SUMO_NET_FILE}")
        print(f"   请将路网文件放入data/目录并修改src/config.py")
    elif not os.path.exists(HOSPITAL_LOCATION_FILE):
        print(f"\n❌ 请配置医院位置文件:")
        print(f"   当前配置: {HOSPITAL_LOCATION_FILE}")
    else:
        print("\n✅ 配置检查通过，开始运行...")
        
        run_complete_pipeline(
            sumo_net_file=SUMO_NET_FILE,
            hospital_file=HOSPITAL_LOCATION_FILE,
            sumo_config_file=sumo_config if os.path.exists(sumo_config) else None,
            accident_spots=SIMULATION_CONFIG["accident_spots"],
            k_paths=SIMULATION_CONFIG["k_paths"],
            use_gui=False
        )
