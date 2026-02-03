"""
Evaluate Drainage Strategy in SUMO
Similar to snow plowing evaluation - run independent simulation at each time point
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse

# SUMO setup
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please set SUMO_HOME environment variable")

import traci
import sumolib


def load_config(config_path='config.json'):
    """Load configuration"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_strategy(strategy_file):
    """Load drainage strategy"""
    with open(strategy_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_group_lanes(net_file, flood_points):
    """
    Convert edge IDs to lane IDs
    Reuse logic from original strategy_validation_sumo.py
    """
    net = sumolib.net.readNet(net_file)
    group_lanes = {}
    
    for group, edges in flood_points.items():
        lanes = []
        for edge_id in edges:
            edge = net.getEdge(edge_id)
            if edge:
                for lane in edge.getLanes():
                    lanes.append(lane.getID())
        group_lanes[group] = lanes
    
    return group_lanes


def evaluate_strategy(config, strategy_data, output_dir=None):
    """
    Static evaluation: Test each drainage completion state independently
    Evaluate after completing each batch (not continuous time tracking)
    """
    print("="*80)
    print(f"Static Evaluation: {strategy_data['strategy_name']}".center(80))
    print("="*80)
    
    # Create output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(config['output']['base_dir']) / f"evaluation_{timestamp}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")
    
    # Get configuration
    flood_points = config['waterlogging_points']
    drainage_params = config['drainage_parameters']
    batches = strategy_data['batches']
    
    flooded_speed = drainage_params['flooded_speed']
    normal_speed = drainage_params['normal_speed']
    start_step = drainage_params['start_step']
    
    # Convert edges to lanes
    group_lanes = get_group_lanes(config['network']['net_file'], flood_points)
    
    print(f"\nStrategy: {strategy_data['strategy_name']}")
    print(f"Batches: {batches}")
    print(f"Total batches: {len(batches)}")
    
    # Get evaluation delays
    evaluation_delays = config['sumo_config'].get('evaluation_delays', [0])
    
    # Evaluation results
    evaluation_results = {
        "strategy_name": strategy_data['strategy_name'],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "flooded_speed": flooded_speed,
            "normal_speed": normal_speed,
            "evaluation_delays": evaluation_delays
        },
        "batch_results": []
    }
    
    # Evaluate each drainage state (after completing each batch)
    for batch_idx in range(len(batches) + 1):
        print(f"\n[Evaluation] After completing {batch_idx} batches...")
        print("-" * 60)
        
        # Determine which groups are drained
        drained_groups = []
        for i in range(batch_idx):
            drained_groups.extend(batches[i])
        
        print(f"  Drained groups: {drained_groups if drained_groups else 'None (all flooded)'}")
        print(f"  Still flooded: {[g for g in flood_points.keys() if g not in drained_groups]}")
        
        # Evaluate at different time delays to see propagation effect
        delay_results = []
        measurement_window = config['sumo_config'].get('measurement_window', 50)
        
        for delay_steps in evaluation_delays:
            print(f"\n  [Time delay: {delay_steps} steps after drainage]")
            
            # Run SUMO simulation for this drainage state
            throughput_rate, queue_length, avg_speed = run_sumo_with_drainage_state(
                config['sumo_config']['config_file'],
                group_lanes,
                flood_points,
                drained_groups,
                flooded_speed,
                normal_speed,
                start_step + delay_steps,
                config['sumo_config']['simulation_steps'],
                measurement_window
            )
            
            print(f"    Cumulative throughput: {throughput_rate} vehicles (in {measurement_window}s window)")
            print(f"    Queue length: {queue_length:.1f} vehicles")
            print(f"    Avg speed: {avg_speed:.2f} m/s")
            
            delay_results.append({
                "delay_steps": delay_steps,
                "cumulative_throughput": int(throughput_rate),
                "queue_length": round(queue_length, 2),
                "avg_speed": round(avg_speed, 3)
            })
        
        evaluation_results['batch_results'].append({
            "batch_index": batch_idx,
            "drained_batches": batches[:batch_idx] if batch_idx > 0 else [],
            "drained_groups": drained_groups,
            "num_drained": len(drained_groups),
            "delay_measurements": delay_results
        })
    
    # Save evaluation results
    result_file = output_dir / f"evaluation_{strategy_data['strategy_name']}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("Evaluation completed!".center(80))
    print(f"Results saved: {result_file}".center(80))
    print("="*80)
    print("\n" + "="*80)
    print("Evaluation completed!".center(80))
    print(f"Results saved: {result_file}".center(80))
    print("="*80)
    print(f"\n[Metrics Explanation]")
    print(f"  Cumulative Throughput: Total vehicles LEAVING entire waterlogging region (higher = better)")
    print(f"  Counted only when vehicle exits all waterlogging lanes (not internal lane changes)")
    print(f"  Measured in {config['sumo_config'].get('measurement_window', 200)} second window")
    print(f"  Queue Length: Average vehicles stuck in waterlogging areas (lower = better)")
    print(f"  Avg Speed: Speed in waterlogging areas (higher = better)\n")
    
    return evaluation_results


def run_sumo_with_drainage_state(sumo_config, group_lanes, flood_points, 
                                 drained_groups, flooded_speed, normal_speed,
                                 start_step, num_steps, measurement_window=None):
    """
    Run SUMO simulation with specific drainage state
    Returns: (throughput_rate, queue_length, avg_speed) for ALL waterlogging areas
    - throughput_rate: vehicles/second in the measurement window (default: use first 50 steps)
    - queue_length: average number of vehicles in waterlogging areas
    - avg_speed: average speed in waterlogging areas
    """
    if measurement_window is None:
        measurement_window = min(50, num_steps)
    
    sumo_cmd = [
        'sumo',
        '-c', sumo_config,
        '--no-warnings', 'true',
        '--no-step-log', 'true',
        '--duration-log.disable', 'true'
    ]
    
    traci.start(sumo_cmd)
    
    # Track vehicles in waterlogging REGION (not per-lane)
    prev_vehicles_in_region = set()  # Vehicles currently in ANY waterlogging lane
    
    total_throughput = 0
    total_queue_length = 0
    queue_samples = 0
    all_speeds = []
    
    # Initial steps (all flooded)
    for step in range(start_step):
        traci.simulationStep()
        
        for group, lanes in group_lanes.items():
            for lane in lanes:
                try:
                    for veh_id in traci.lane.getLastStepVehicleIDs(lane):
                        traci.vehicle.setSpeed(veh_id, flooded_speed)
                except:
                    continue
    
    # Main simulation steps
    for step in range(num_steps):
        traci.simulationStep()
        
        # Set speed based on drainage state
        for group, lanes in group_lanes.items():
            target_speed = normal_speed if group in drained_groups else flooded_speed
            
            for lane in lanes:
                try:
                    # Set vehicle speed
                    for veh_id in traci.lane.getLastStepVehicleIDs(lane):
                        traci.vehicle.setSpeed(veh_id, target_speed)
                except:
                    continue
        
        # Only collect statistics in measurement window
        if step < measurement_window:
            # Collect all vehicles currently in waterlogging region
            current_vehicles_in_region = set()
            step_queue = 0
            
            for group in flood_points.keys():
                for lane in group_lanes[group]:
                    try:
                        lane_vehs = set(traci.lane.getLastStepVehicleIDs(lane))
                        current_vehicles_in_region.update(lane_vehs)
                        
                        # Queue length: current vehicles in lane
                        step_queue += len(lane_vehs)
                        
                        # Speed: collect from all vehicles
                        for veh_id in lane_vehs:
                            try:
                                speed = traci.vehicle.getSpeed(veh_id)
                                all_speeds.append(speed)
                            except:
                                continue
                    except:
                        continue
            
            # Throughput: vehicles that LEFT the entire waterlogging region
            # (were in region last step, but not in region now)
            vehicles_left_region = prev_vehicles_in_region - current_vehicles_in_region
            total_throughput += len(vehicles_left_region)
            
            prev_vehicles_in_region = current_vehicles_in_region
            total_queue_length += step_queue
            queue_samples += 1
    
    traci.close()
    
    # Calculate averages
    avg_queue = total_queue_length / queue_samples if queue_samples > 0 else 0
    avg_speed = sum(all_speeds) / len(all_speeds) if all_speeds else 0
    # Return cumulative throughput (total vehicles that left the region)
    
    return total_throughput, avg_queue, avg_speed


def main():
    parser = argparse.ArgumentParser(description='Evaluate drainage strategy in SUMO')
    parser.add_argument('-c', '--config', default='config.json',
                       help='Configuration file path')
    parser.add_argument('-s', '--strategy', required=True,
                       help='Strategy JSON file path')
    parser.add_argument('-o', '--output', default=None,
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Load configuration and strategy
    config = load_config(args.config)
    strategy_data = load_strategy(args.strategy)
    
    # Run evaluation
    results = evaluate_strategy(config, strategy_data, args.output)
    
    return results


if __name__ == '__main__':
    main()
