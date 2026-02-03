"""
Baseline扫雪策略SUMO评测脚本
复刻snow_plow_project/evaluate_snowplow.py的评测逻辑
评测所有道路0时刻就清扫完成的baseline场景
"""

import json
import traci
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

# 配置文件路径
SUMO_CONFIG = "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test.sumocfg"
SUMO_CONFIG_SCALED = "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_0.1.sumocfg"
JSON_RECORD = "snowplow_baseline_time_steps_record.json"
OUTPUT_JSON = "sumo_evaluation_baseline_results.json"

# 清扫道路和未清扫道路的参数（与原脚本完全一致）
CLEANED_PARAMS = {
    "accel": 2.6,
    "decel": 4.5,
    "max_speed": 33,
    "min_gap": 2.5
}

UNCLEAN_PARAMS = {
    "accel": 1.5,
    "decel": 2.5,
    "max_speed": 4,
    "min_gap": 4
}

def load_time_step_records(json_path):
    """加载时间步清扫记录"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_cleaned_edges_at_time(records, time_minutes):
    """
    获取指定时间（分钟）已清扫的道路集合
    找到小于等于该时间的最近时间步
    """
    # 提取所有时间步
    time_steps = []
    for key, value in records.items():
        time_steps.append((value['time_minutes'], key))
    
    time_steps.sort()
    
    # 找到小于等于目标时间的最大时间步
    target_key = None
    for t_min, key in time_steps:
        if t_min <= time_minutes:
            target_key = key
        else:
            break
    
    if target_key is None:
        return set()
    
    return set(records[target_key]['total_cleaned_edges'])

def run_sumo_evaluation(time_points_hours=[0, 1, 2, 3, 4, 5], simulation_steps=200, use_scaled=True):
    """
    在SUMO中运行评测（baseline场景：所有道路已清扫）
    time_points_hours: 需要评测的时间点（小时）
    simulation_steps: 每个场景运行的仿真步数
    use_scaled: 是否使用缩减后的rou文件
    """
    records = load_time_step_records(JSON_RECORD)
    results = {}
    
    # 选择配置文件
    config_file = SUMO_CONFIG_SCALED if use_scaled else SUMO_CONFIG
    config_name = "缩减版(10%)" if use_scaled else "完整版"
    
    print(f"\n使用配置: {config_name}")
    print(f"配置文件: {config_file}")
    
    for hour in time_points_hours:
        print(f"\n{'='*60}")
        print(f"开始评测第 {hour} 小时的Baseline场景...")
        print(f"{'='*60}")
        
        # 获取该时间点已清扫的道路（baseline：所有道路）
        time_minutes = hour * 60
        cleaned_edges = get_cleaned_edges_at_time(records, time_minutes)
        print(f"已清扫道路数量: {len(cleaned_edges)} (baseline: 全部)")
        
        # 启动SUMO
        traci.start(["sumo", "-c", config_file, "--start"])
        
        # 运行指定步数的仿真
        for step in range(simulation_steps):
            traci.simulationStep()
            
            current_vehicles = traci.vehicle.getIDList()
            
            # 为每辆车设置参数（baseline：所有道路都用cleaned参数）
            for veh_id in current_vehicles:
                current_edge = traci.vehicle.getRoadID(veh_id)
                
                # Baseline场景：所有道路都是cleared状态
                traci.vehicle.setAcceleration(veh_id, CLEANED_PARAMS["accel"], 1)
                traci.vehicle.setDecel(veh_id, CLEANED_PARAMS["decel"])
                traci.vehicle.setMaxSpeed(veh_id, CLEANED_PARAMS["max_speed"])
                traci.vehicle.setMinGap(veh_id, CLEANED_PARAMS["min_gap"])
            
            # 每50步打印一次进度
            if (step + 1) % 50 == 0:
                print(f"  仿真进度: {step + 1}/{simulation_steps} 步, 当前车辆数: {len(current_vehicles)}")
        
        # 在第200步统计全局平均速度
        current_vehicles = traci.vehicle.getIDList()
        num_vehicles = len(current_vehicles)
        
        if num_vehicles > 0:
            total_speed = sum(traci.vehicle.getSpeed(veh) for veh in current_vehicles)
            global_avg_speed = total_speed / num_vehicles
        else:
            global_avg_speed = 0
        
        print(f"\n  仿真完成 - 第{simulation_steps}步统计:")
        print(f"    车辆数: {num_vehicles}")
        print(f"    全局平均速度: {global_avg_speed:.2f} m/s ({global_avg_speed * 3.6:.2f} km/h)")
        
        # 关闭SUMO
        traci.close()
        
        # 保存结果
        results[f"hour_{hour}"] = {
            "time_hours": hour,
            "time_minutes": time_minutes,
            "num_cleaned_edges": len(cleaned_edges),
            "simulation_steps": simulation_steps,
            "num_vehicles": num_vehicles,
            "global_avg_speed": global_avg_speed
        }
        
        print(f"第 {hour} 小时baseline评测完成")
    
    return results

def save_results(results, output_path):
    """保存评测结果到JSON文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n评测结果已保存至: {output_path}")

def plot_results(results):
    """可视化评测结果"""
    hours = []
    speeds = []
    num_cleaned = []
    num_vehicles = []
    
    # 整理数据
    for key in sorted(results.keys()):
        hour_data = results[key]
        hours.append(hour_data['time_hours'])
        speeds.append(hour_data['global_avg_speed'])
        num_cleaned.append(hour_data['num_cleaned_edges'])
        num_vehicles.append(hour_data['num_vehicles'])
    
    # 创建图表
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # 左Y轴：全局平均速度
    color = 'tab:blue'
    ax1.set_xlabel('时间（小时）', fontsize=14)
    ax1.set_ylabel('全局平均速度 (m/s)', fontsize=14, color=color)
    line1 = ax1.plot(hours, speeds, marker='o', linewidth=3, markersize=10,
                     color=color, label='Baseline平均速度')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 添加标题
    plt.title('Baseline场景（所有道路已清扫）的全局平均速度', fontsize=16, fontweight='bold', pad=20)
    
    # 图例
    ax1.legend(loc='upper left', fontsize=12)
    
    # 保存图表
    plt.tight_layout()
    plt.savefig('sumo_evaluation_baseline_speed_plot.png', dpi=100, bbox_inches='tight')
    print(f"图表已保存至: sumo_evaluation_baseline_speed_plot.png")
    plt.close()

if __name__ == "__main__":
    print("="*70)
    print("Baseline扫雪策略SUMO评测".center(70))
    print("="*70)
    
    # 运行评测
    results = run_sumo_evaluation(time_points_hours=[0, 1, 2, 3, 4, 5], simulation_steps=200, use_scaled=True)
    
    # 保存结果
    save_results(results, OUTPUT_JSON)
    
    # 绘图
    plot_results(results)
    
    print("\n" + "="*70)
    print("Baseline评测完成！".center(70))
    print("="*70)
