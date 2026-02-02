"""
使用test3已生成的救护车配置进行4事故点测试
排除原test3中的事故点4(200002421)，因为该点所有救护车都无法到达
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import json
import numpy as np
import traci
import xml.etree.ElementTree as ET
from datetime import datetime

from optimization import solve_optimal_assignment, solve_greedy_assignment
from visualization import visualize_comparison

# 创建时间戳结果目录
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
result_dir = f'results/test_run_{timestamp}'
os.makedirs(result_dir, exist_ok=True)

print("="*60)
print("应急响应优化测试 - 4事故点配置")
print("="*60)
print(f"结果目录: {result_dir}\n")

# ========== 配置参数 ==========
SUMO_CONFIG = r"E:\Traffic_Simulation\Traffic_accident\response.sumocfg"
ROUTE_FILE = r"E:\Traffic_Simulation\Traffic_accident\full_rou\mapall_addline_response.rou.xml"

# 排除事故点4(200002421)，保留其他4个
accident_spots = ["200042649", "200040849", "200063134", "200040901"]
accident_mapping = [0, 1, 2, 4]  # 映射到test3原始索引
acc_num = 4
hospital_num = 6
path_num = 5  # 每对医院-事故点有5条路径
MAX_SIMULATION_TIME = 1200  # 参照test3

print(f"配置信息:")
print(f"  医院数: {hospital_num}")
print(f"  事故点数: {acc_num} (排除了原第4个事故点)")
print(f"  每对路径数: {path_num}")
print(f"  总救护车数: {hospital_num * acc_num * path_num} 辆")
print(f"  最大模拟时间: {MAX_SIMULATION_TIME}秒\n")

# ========== 读取救护车路径信息（参照test3用DataFrame） ==========
print("读取救护车路径...")
tree = ET.parse(ROUTE_FILE)
root = tree.getroot()

# 构建ambulance_df，参照test3的结构
ambulance_data = []
for vehicle in root.findall('vehicle'):
    vehicle_id = vehicle.get('id')
    if vehicle_id.startswith('ambulance_'):
        amb_id = int(vehicle_id.split('_')[1])
        route = vehicle.find('route')
        if route is not None:
            edges = route.get('edges')  # 保持字符串格式
            ambulance_data.append({
                'ambulance_id': amb_id,
                'path': edges
            })

ambulance_df = pd.DataFrame(ambulance_data)
ambulance_df = ambulance_df.set_index('ambulance_id').sort_index()
print(f"已加载 {len(ambulance_df)} 辆救护车的路径信息\n")

# 辅助函数
def is_vehicle_finished(vehicle_id, edge_id):
    current_road = traci.vehicle.getRoadID(vehicle_id)
    return current_road == edge_id

# ========== SUMO模拟 ==========
print("="*60)
print("开始SUMO模拟...")
print("="*60)

# 确定要测试的救护车ID
test_ambulances = []
for h in range(hospital_num):
    for new_a, orig_a in enumerate(accident_mapping):
        start = (h * 5 + orig_a) * path_num + 1
        end = start + path_num
        test_ambulances.extend(range(start, end))

print(f"测试救护车: {len(test_ambulances)} 辆\n")

# 启动SUMO
traci.start(['sumo', '-c', SUMO_CONFIG, '--no-warnings'])

arrival_time = {}
unfinished_ambulance_lst = list(test_ambulances)
finished_ambulance_lst = []
current_step = 0

print("模拟进行中...")
while current_step < MAX_SIMULATION_TIME:
    # 每100步检查是否可以提前退出
    if current_step % 100 == 0:
        print(f"  步骤 {current_step}: 已完成 {len(finished_ambulance_lst)}, 剩余 {len(unfinished_ambulance_lst)}")
        
        # 检查每组是否至少有一辆完成
        all_groups_have = True
        for h in range(hospital_num):
            for new_a, orig_a in enumerate(accident_mapping):
                start = (h * 5 + orig_a) * path_num + 1
                end = start + path_num
                has_one = any(f"ambulance_{j}" in arrival_time for j in range(start, end))
                if not has_one:
                    all_groups_have = False
                    break
            if not all_groups_have:
                break
        
        if all_groups_have:
            print("  每组都至少有一条路径完成！提前结束。")
            break
    
    traci.simulationStep()
    current_step += 1
    
    # step 101设置速度（参照test3）
    if current_step == 101:
        for amb in test_ambulances:
            try:
                traci.vehicle.setSpeed(f"ambulance_{amb}", 30)
                traci.vehicle.setSpeedMode(f"ambulance_{amb}", 0)
            except:
                pass
    
    # 每10步检查一次（参照test3）
    if current_step >= 101 and current_step % 10 == 0:
        for amb in list(unfinished_ambulance_lst):
            try:
                # 参照test3: ambulance_df['path'][amb - 1].split(" ")[-1]
                # amb是1-based，用.loc[amb]访问
                target_edge = ambulance_df.loc[amb, 'path'].split(" ")[-1]
                
                if is_vehicle_finished(f"ambulance_{amb}", target_edge):
                    arrival_time[f"ambulance_{amb}"] = current_step
                    unfinished_ambulance_lst.remove(amb)
                    finished_ambulance_lst.append(amb)
            except:
                continue

traci.close()

print(f"\n模拟完成!")
print(f"  成功到达: {len(finished_ambulance_lst)} 辆 ({len(finished_ambulance_lst)/len(test_ambulances)*100:.1f}%)")
print(f"  未完成: {len(unfinished_ambulance_lst)} 辆\n")

# 填充超时车辆
for amb in test_ambulances:
    vehicle_id = f"ambulance_{amb}"
    if vehicle_id not in arrival_time:
        arrival_time[vehicle_id] = MAX_SIMULATION_TIME

# ========== 构建时间矩阵 ==========
print("="*60)
print("构建时间矩阵...")
print("="*60)

matrix = np.full((hospital_num, acc_num), np.inf)

for h in range(hospital_num):
    for new_a, orig_a in enumerate(accident_mapping):
        start = (h * 5 + orig_a) * path_num + 1
        end = start + path_num
        
        times = []
        for i in range(start, end):
            vehicle_id = f"ambulance_{i}"
            if vehicle_id in arrival_time:
                times.append(arrival_time[vehicle_id])
        
        if times:
            matrix[h, new_a] = min(times)

# 保存时间矩阵
df_matrix = pd.DataFrame(
    matrix,
    columns=[f"事故点{i+1}" for i in range(acc_num)],
    index=[f"医院{i+1}" for i in range(hospital_num)]
)
df_matrix.to_csv(f'{result_dir}/time_matrix.csv')
print(f"\n时间矩阵:\n{df_matrix}\n")
print(f"时间矩阵已保存: {result_dir}/time_matrix.csv")

# 保存详细到达时间（含完整路径）
arrival_data = []
for vehicle_id in sorted(arrival_time.keys(), key=lambda x: int(x.split('_')[1])):
    amb_id = int(vehicle_id.split('_')[1])
    path_str = ambulance_df.loc[amb_id, 'path'] if amb_id in ambulance_df.index else ""
    path_list = path_str.split(" ") if path_str else []
    
    arrival_data.append({
        'vehicle_id': str(vehicle_id),
        'ambulance_id': int(amb_id),
        'arrival_time': int(arrival_time[vehicle_id]),
        'is_timeout': int(arrival_time[vehicle_id]) >= MAX_SIMULATION_TIME,
        'path': path_list,
        'path_length': int(len(path_list)),
        'target_edge': path_list[-1] if path_list else ""
    })

with open(f'{result_dir}/arrival_times.json', 'w', encoding='utf-8') as f:
    json.dump(arrival_data, f, ensure_ascii=False, indent=2)
print(f"到达时间详情已保存: {result_dir}/arrival_times.json\n")

# ========== 优化求解 ==========
print("="*60)
print("运行优化算法...")
print("="*60)

optimal_time, optimal_assign = solve_optimal_assignment(matrix)
greedy_time, greedy_assign, _ = solve_greedy_assignment(matrix)

improvement = (greedy_time - optimal_time) / greedy_time * 100 if greedy_time > 0 else 0

print(f"\n优化结果:")
print(f"  最优算法: {optimal_time:.0f} 秒")
print(f"  贪心算法: {greedy_time:.0f} 秒")
print(f"  性能提升: {improvement:.1f}% (节省 {greedy_time - optimal_time:.0f} 秒)\n")

# ========== 保存最优分配路径 ==========
optimal_paths = []

for new_acc_idx, hosp_idx, time in sorted(optimal_assign):
    orig_acc_idx = accident_mapping[new_acc_idx]
    start = (hosp_idx * 5 + orig_acc_idx) * path_num + 1
    end = start + path_num
    
    # 找最快的路径
    best_time = float('inf')
    best_amb_id = None
    best_path = None
    
    for i in range(start, end):
        vehicle_id = f"ambulance_{i}"
        t = arrival_time.get(vehicle_id, MAX_SIMULATION_TIME)
        if t < best_time:
            best_time = t
            best_amb_id = i
            if i in ambulance_df.index:
                best_path = ambulance_df.loc[i, 'path'].split(" ")
            else:
                best_path = []
    
    optimal_paths.append({
        'accident_idx': int(new_acc_idx),
        'accident_spot': str(accident_spots[new_acc_idx]),
        'hospital_idx': int(hosp_idx),
        'hospital_name': f"医院{hosp_idx+1}",
        'time': int(time),
        'ambulance_id': int(best_amb_id) if best_amb_id else None,
        'path': [str(e) for e in best_path] if best_path else [],
        'path_length': int(len(best_path)) if best_path else 0
    })

with open(f'{result_dir}/optimal_paths.json', 'w', encoding='utf-8') as f:
    json.dump(optimal_paths, f, ensure_ascii=False, indent=2)
print(f"最优分配路径已保存: {result_dir}/optimal_paths.json\n")

# ========== 生成可视化 ==========
print("="*60)
print("生成可视化...")
print("="*60)

hospital_names = [f"医院{i+1}" for i in range(hospital_num)]

# 贪心分配
hospital_tasks_greedy = {i: [] for i in range(hospital_num)}
hospital_cumulative_time = {i: 0 for i in range(hospital_num)}

for acc_idx, hosp_idx, time in sorted(greedy_assign):
    start_time = hospital_cumulative_time[hosp_idx]
    end_time = start_time + time
    hospital_tasks_greedy[hosp_idx].append((
        f"事故点{acc_idx+1}",
        start_time,
        end_time
    ))
    hospital_cumulative_time[hosp_idx] = end_time

# 最优分配
hospital_tasks_optimal = {i: [] for i in range(hospital_num)}

for acc_idx, hosp_idx, time in sorted(optimal_assign):
    hospital_tasks_optimal[hosp_idx].append((
        f"事故点{acc_idx+1}",
        0,
        time
    ))

# 准备可视化数据
greedy_visualization = {
    'hospitals': hospital_names,
    'tasks': [hospital_tasks_greedy[i] for i in range(hospital_num)],
    'max_time': greedy_time
}

optimal_visualization = {
    'hospitals': hospital_names,
    'tasks': [hospital_tasks_optimal[i] for i in range(hospital_num)],
    'max_time': optimal_time
}

visualize_comparison(
    greedy_visualization,
    optimal_visualization,
    f'{result_dir}/comparison.png'
)
print(f"可视化已保存: {result_dir}/comparison.png\n")

# ========== 生成报告 ==========
print("="*60)
print("生成详细报告...")
print("="*60)

with open(f'{result_dir}/summary.txt', 'w', encoding='utf-8') as f:
    f.write("="*60 + "\n")
    f.write("应急响应优化测试报告\n")
    f.write("="*60 + "\n\n")
    
    f.write("配置信息:\n")
    f.write(f"  测试时间: {timestamp}\n")
    f.write(f"  医院数: {hospital_num}\n")
    f.write(f"  事故点数: {acc_num}\n")
    f.write(f"  测试救护车: {len(test_ambulances)} 辆\n\n")
    
    f.write("事故点列表:\n")
    for i, spot in enumerate(accident_spots):
        f.write(f"  事故点{i+1}: {spot}\n")
    f.write("\n")
    
    # f.write("模拟结果:\n")
    # f.write(f"  成功到达: {arrived_count} 辆 ({arrived_count/len(test_ambulances)*100:.1f}%)\n")
    # f.write(f"  超时未达: {timeout_count} 辆\n\n")
    
    f.write("时间矩阵 (秒):\n")
    f.write(df_matrix.to_string() + "\n\n")
    
    f.write("优化结果:\n")
    f.write(f"  最优算法: {optimal_time:.0f} 秒\n")
    f.write(f"  贪心算法: {greedy_time:.0f} 秒\n")
    f.write(f"  性能提升: {improvement:.1f}%\n\n")
    
    f.write("最优分配方案 (按医院):\n")
    for h in range(hospital_num):
        f.write(f"\n  医院{h+1}:\n")
        hospital_assignments = [x for x in optimal_paths if x['hospital_idx'] == h]
        for item in hospital_assignments:
            f.write(f"    -> 事故点{item['accident_idx']+1}, ")
            f.write(f"时间: {item['time']}秒, ")
            f.write(f"救护车: {item['ambulance_id']}\n")
            f.write(f"       路径({item['path_length']}条边): {' -> '.join(item['path'][:5])}")
            if item['path_length'] > 5:
                f.write(f" ... {' -> '.join(item['path'][-2:])}")
            f.write(f"\n")
    
    f.write("\n贪心分配方案 (按医院):\n")
    for h in range(hospital_num):
        f.write(f"\n  医院{h+1}:\n")
        greedy_hospital = [x for x in greedy_assign if x[1] == h]
        for acc_idx, hosp_idx, time in greedy_hospital:
            f.write(f"    -> 事故点{acc_idx+1}, 时间: {time}秒\n")
    
    f.write("\n\n最优分配方案完整路径:\n")
    for item in optimal_paths:
        f.write(f"\n  【事故点{item['accident_idx']+1} <- {item['hospital_name']}】\n")
        f.write(f"    救护车ID: {item['ambulance_id']}\n")
        f.write(f"    到达时间: {item['time']}秒\n")
        f.write(f"    路径长度: {item['path_length']}条边\n")
        f.write(f"    完整路径:\n")
        for i, edge in enumerate(item['path']):
            if i % 5 == 0:
                f.write(f"      ")
            f.write(f"{edge}")
            if i < len(item['path']) - 1:
                f.write(" -> ")
            if (i + 1) % 5 == 0 and i < len(item['path']) - 1:
                f.write("\n")
        f.write("\n")
    
    f.write("\n" + "="*60 + "\n")
    # 统计每个事故点的到达情况
    f.write("各事故点到达统计:\n")
    for new_a, orig_a in enumerate(accident_mapping):
        start = orig_a * path_num * hospital_num + 1
        total = hospital_num * path_num
        arrived = 0
        for h in range(hospital_num):
            amb_start = (h * 5 + orig_a) * path_num + 1
            amb_end = amb_start + path_num
            for i in range(amb_start, amb_end):
                vehicle_id = f"ambulance_{i}"
                if vehicle_id in arrival_time and arrival_time[vehicle_id] < MAX_SIMULATION_TIME:
                    arrived += 1
        
        f.write(f"  事故点{new_a+1} ({accident_spots[new_a]}): {arrived}/{total} ({arrived/total*100:.1f}%)\n")

print(f"详细报告已保存: {result_dir}/summary.txt\n")

print("="*60)
print("测试完成!")
print("="*60)
print(f"\n所有结果已保存到: {result_dir}/")
print("文件列表:")
print(f"  - time_matrix.csv")
print(f"  - arrival_times.json")
print(f"  - optimal_paths.json")
print(f"  - comparison.png")
print(f"  - summary.txt")
