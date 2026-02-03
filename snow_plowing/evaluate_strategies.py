"""
SUMO模拟评估器 - 独立运行
读取策略JSON文件，运行SUMO模拟评估扫雪效果
输入：config.json + strategy_*.json
输出：evaluation_*.json
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# SUMO环境设置
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("请设置SUMO_HOME环境变量")

import traci
import xml.etree.ElementTree as ET


def load_config(config_path='config.json'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_strategy(strategy_file):
    """加载策略文件"""
    with open(strategy_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def evaluate_strategy(config, strategy_data, output_dir=None):
    """
    在SUMO环境中评估策略
    
    Args:
        config: 配置字典
        strategy_data: 策略数据字典
        output_dir: 输出目录
    
    Returns:
        dict: 评估结果
    """
    print("="*80)
    print(f"SUMO模拟评估: {strategy_data['strategy_name']}".center(80))
    print("="*80)
    
    # 创建输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(config['output']['base_dir']) / f"evaluation_{timestamp}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {output_dir}")
    
    # 提取清扫完成的道路和时间
    cleaned_roads_timeline = {}
    for truck in strategy_data['trucks']:
        for record in truck['cleaning_records']:
            edge_id = record['edge_id']
            end_time = record['end_time']  # 秒
            if edge_id not in cleaned_roads_timeline:
                cleaned_roads_timeline[edge_id] = end_time
            else:
                cleaned_roads_timeline[edge_id] = min(cleaned_roads_timeline[edge_id], end_time)
    
    print(f"\n策略信息:")
    print(f"  总清扫道路: {len(cleaned_roads_timeline)} 条")
    print(f"  评估时间点: {config['sumo_config']['evaluation_hours']}")
    
    # 准备评估结果
    evaluation_results = {
        "strategy_name": strategy_data['strategy_name'],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "sumo_config_file": config['sumo_config']['config_file'],
            "simulation_steps": config['sumo_config']['simulation_steps'],
            "evaluation_hours": config['sumo_config']['evaluation_hours']
        },
        "hourly_results": []
    }
    
    # 对每个时间点进行评估
    for hour in config['sumo_config']['evaluation_hours']:
        print(f"\n[评估] {hour}小时时刻...")
        print("-" * 60)
        
        # 确定在此时刻哪些道路已被清扫
        time_seconds = hour * 3600
        cleaned_at_this_time = [edge_id for edge_id, clean_time 
                               in cleaned_roads_timeline.items() 
                               if clean_time <= time_seconds]
        
        print(f"  已清扫道路: {len(cleaned_at_this_time)} 条")
        
        # 修改路网参数
        net_file_modified = output_dir / f'net_modified_h{hour}.net.xml'
        modify_network_params(config['network']['net_file'], 
                            net_file_modified,
                            cleaned_at_this_time,
                            config['road_parameters'])
        
        # 运行SUMO模拟
        avg_speed, total_vehicles = run_sumo_simulation(
            config['sumo_config']['config_file'],
            net_file_modified,
            config['sumo_config']['simulation_steps']
        )
        
        print(f"  模拟完成: 平均速度={avg_speed:.2f} m/s, 车辆数={total_vehicles}")
        
        evaluation_results['hourly_results'].append({
            "hour": hour,
            "roads_cleaned": len(cleaned_at_this_time),
            "average_speed_ms": round(avg_speed, 3),
            "total_vehicles": total_vehicles
        })
    
    # 保存评估结果
    result_file = output_dir / f"evaluation_{strategy_data['strategy_name']}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("评估完成！".center(80))
    print(f"结果文件: {result_file}".center(80))
    print("="*80)
    
    return evaluation_results


def modify_network_params(original_net_file, output_net_file, cleaned_edges, road_params):
    """修改路网参数"""
    tree = ET.parse(original_net_file)
    root = tree.getroot()
    
    cleaned_params = road_params['cleaned']
    unclean_params = road_params['unclean']
    
    for edge in root.findall('edge'):
        edge_id = edge.get('id')
        if ':' in edge_id:
            continue
        
        # 根据清扫状态设置参数
        if edge_id in cleaned_edges:
            params = cleaned_params
        else:
            params = unclean_params
        
        # 修改车道参数
        for lane in edge.findall('lane'):
            lane.set('speed', str(params['max_speed']))
    
    # 修改type定义
    for edge_type in root.findall('type'):
        type_id = edge_type.get('id')
        # 可以根据需要修改type的默认参数
        pass
    
    tree.write(output_net_file, encoding='utf-8', xml_declaration=True)


def run_sumo_simulation(sumo_config, modified_net_file, num_steps):
    """运行SUMO模拟"""
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
    parser = argparse.ArgumentParser(description='SUMO模拟评估扫雪策略')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-s', '--strategy', required=True,
                       help='策略JSON文件路径')
    parser.add_argument('-o', '--output', default=None,
                       help='输出目录 (默认: 自动创建时间戳目录)')
    
    args = parser.parse_args()
    
    # 加载配置和策略
    config = load_config(args.config)
    strategy_data = load_strategy(args.strategy)
    
    # 运行评估
    results = evaluate_strategy(config, strategy_data, args.output)
    
    return results


if __name__ == '__main__':
    main()
