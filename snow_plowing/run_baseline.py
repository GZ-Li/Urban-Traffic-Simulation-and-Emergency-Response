"""
Baseline仿真评估器 - 参考evaluate_strategies.py
评估无积雪情况（所有道路已清扫）的交通指标
与扫雪策略评估保持一致的设定和思路
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse
import xml.etree.ElementTree as ET

# SUMO环境设置
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("请设置SUMO_HOME环境变量")

import traci


def load_config(config_path='config.json'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_baseline(config, output_dir=None):
    """
    评估baseline场景（无积雪/全部清扫完成）
    参考evaluate_strategies.py的评估思路
    
    Args:
        config: 配置字典
        output_dir: 输出目录
    
    Returns:
        dict: 评估结果
    """
    print("="*80)
    print("SUMO模拟评估: Baseline (无积雪场景)".center(80))
    print("="*80)
    
    # 创建输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(config['output']['base_dir']) / f"evaluation_{timestamp}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {output_dir}")
    
    print(f"\n策略信息:")
    print(f"  场景: 无积雪（所有道路已清扫）")
    print(f"  评估时间点: {config['sumo_config']['evaluation_hours']}")
    
    # 准备评估结果
    evaluation_results = {
        "strategy_name": "baseline_no_snow",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "sumo_config_file": config['sumo_config']['config_file'],
            "simulation_steps": config['sumo_config']['simulation_steps'],
            "evaluation_hours": config['sumo_config']['evaluation_hours']
        },
        "hourly_results": []
    }
    
    # 对每个时间点进行评估（与evaluate_strategies.py保持一致）
    for hour in config['sumo_config']['evaluation_hours']:
        print(f"\n[评估] {hour}小时时刻...")
        print("-" * 60)
        
        # 修改路网参数：所有道路使用cleaned参数
        net_file_modified = output_dir / f'net_baseline_h{hour}.net.xml'
        modify_network_for_baseline(config['network']['net_file'], 
                                    net_file_modified,
                                    config['road_parameters']['cleaned'])
        
        # 运行SUMO模拟（与evaluate_strategies.py相同）
        avg_speed, total_vehicles = run_sumo_simulation(
            config['sumo_config']['config_file'],
            net_file_modified,
            config['sumo_config']['simulation_steps']
        )
        
        print(f"  模拟完成: 平均速度={avg_speed:.2f} m/s, 车辆数={total_vehicles}")
        
        evaluation_results['hourly_results'].append({
            "hour": hour,
            "roads_cleaned": "all",
            "average_speed_ms": round(avg_speed, 3),
            "total_vehicles": total_vehicles
        })
    
    # 保存评估结果
    result_file = output_dir / "evaluation_baseline.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("评估完成！".center(80))
    print(f"结果文件: {result_file}".center(80))
    print("="*80)
    
    return evaluation_results


def modify_network_for_baseline(original_net_file, output_net_file, cleaned_params):
    """
    修改路网参数为baseline（所有道路已清扫）
    参考evaluate_strategies.py的modify_network_params()
    """
    tree = ET.parse(original_net_file)
    root = tree.getroot()
    
    for edge in root.findall('edge'):
        edge_id = edge.get('id')
        if ':' in edge_id:  # 跳过交叉口内部边
            continue
        
        # 所有道路使用cleaned参数
        for lane in edge.findall('lane'):
            lane.set('speed', str(cleaned_params['max_speed']))
    
    tree.write(output_net_file, encoding='utf-8', xml_declaration=True)


def run_sumo_simulation(sumo_config, modified_net_file, num_steps):
    """
    运行SUMO模拟
    与evaluate_strategies.py的run_sumo_simulation()完全一致
    """
    sumo_cmd = [
        'sumo',
        '-c', sumo_config,
        '--net-file', str(modified_net_file),
        '--no-warnings', 'true',
        '--no-step-log', 'true',
        '--duration-log.disable', 'true'
    ]
    
    traci.start(sumo_cmd)
    
    speeds = []
    vehicle_count = 0
    
    for step in range(num_steps):
        traci.simulationStep()
        
        vehicle_ids = traci.vehicle.getIDList()
        vehicle_count = max(vehicle_count, len(vehicle_ids))
        
        for veh_id in vehicle_ids:
            speed = traci.vehicle.getSpeed(veh_id)
            speeds.append(speed)
    
    traci.close()
    
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    return avg_speed, vehicle_count


def main():
    parser = argparse.ArgumentParser(description='SUMO模拟评估Baseline（无积雪场景）')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-o', '--output', default=None,
                       help='输出目录 (默认: 自动创建时间戳目录)')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 运行评估
    results = evaluate_baseline(config, args.output)
    
    return results


if __name__ == '__main__':
    main()
