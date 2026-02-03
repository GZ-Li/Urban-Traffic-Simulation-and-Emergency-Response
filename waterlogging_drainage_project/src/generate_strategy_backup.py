"""
Generate Drainage Strategy
Reuse logic from sort_points.py to rank waterlogging points by traffic flow
"""
import json
import xml.etree.ElementTree as ET
from collections import defaultdict, OrderedDict
from pathlib import Path


def load_config(config_path='config.json'):
    """Load configuration"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_traffic_flow(route_file, flood_points):
    """
    Calculate traffic flow through each waterlogging group
    Reuse logic from original sort_points.py
    """
    print(f"  Loading route file: {route_file}")
    
    flow_counts = {}
    tree = ET.parse(route_file)
    root = tree.getroot()
    
    # Initialize counters
    for group in flood_points:
        flow_counts[group] = 0
    
    # Count vehicles passing through each group
    for veh in root.findall('vehicle'):
        route = veh.find('route')
        if route is not None:
            edges = route.attrib['edges'].split()
            for group, lanes in flood_points.items():
                for lane in lanes:
                    if lane in edges:
                        flow_counts[group] += 1
                        break
    
    print(f"  Total vehicles analyzed: {len(root.findall('vehicle'))}")
    return flow_counts


def generate_best_strategy(config, output_path):
    """
    Generate best drainage strategy (sorted by traffic flow)
    """
    print("\n[BEST STRATEGY] Generating...")
    print("-" * 60)
    
    flood_points = config['waterlogging_points']
    route_file = config['network']['route_file']
    
    # Calculate traffic flow
    flow_counts = calculate_traffic_flow(route_file, flood_points)
    
    # Sort by traffic flow (descending)
    sorted_groups = sorted(flow_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("\n  Traffic flow ranking:")
    for group, count in sorted_groups:
        print(f"    {group}: {count} vehicles")
    
    # Create batches
    max_clean_at_once = config['drainage_parameters']['max_clean_at_once']
    sorted_points = [group for group, _ in sorted_groups]
    
    batches = []
    for i in range(0, len(sorted_points), max_clean_at_once):
        batch = sorted_points[i:i+max_clean_at_once]
        batches.append(batch)
    
    print(f"\n  Drainage batches: {batches}")
    
    # Build result
    result = {
        "strategy_name": "best",
        "description": "Drainage order sorted by traffic flow (high to low)",
        "config": {
            "max_clean_at_once": max_clean_at_once,
            "steps_to_clean_one": config['drainage_parameters']['steps_to_clean_one']
        },
        "traffic_flow": {group: count for group, count in sorted_groups},
        "batches": batches,
        "drainage_order": sorted_points
    }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n  Saved to: {output_path}")
    print(f"  Total groups: {len(sorted_points)}")
    print(f"  Total batches: {len(batches)}")
    
    return result


def generate_worst_strategy(config, output_path):
    """
    Generate worst drainage strategy (low traffic flow to high - opposite of best)
    """
    print("\n[WORST STRATEGY] Generating...")
    print("-" * 60)
    
    # Calculate traffic flow (same as best strategy)
    route_file = config['network']['route_file']
    flood_points = config['waterlogging_points']
    
    print(f"  Loading route file: {route_file}")
    traffic_flow = calculate_traffic_flow(route_file, flood_points)
    
    print(f"  Total vehicles analyzed: {sum(traffic_flow.values())}")
    
    # Sort by traffic flow ASCENDING (low to high - worst strategy)
    sorted_groups = sorted(traffic_flow.items(), key=lambda x: x[1])
    sorted_points = [group for group, _ in sorted_groups]
    
    print(f"\n  Traffic flow ranking (low to high - worst order):")
    for group, count in sorted_groups:
        print(f"    {group}: {count} vehicles")
    
    # Create batches
    max_clean_at_once = config['drainage_parameters']['max_clean_at_once']
    batches = [sorted_points[i:i+max_clean_at_once] 
               for i in range(0, len(sorted_points), max_clean_at_once)]
    
    print(f"\n  Drainage batches: {batches}")
    
    result = {
        "strategy_name": "worst",
        "description": "Drainage order sorted by traffic flow (low to high - worst case)",
        "config": {
            "max_clean_at_once": max_clean_at_once,
            "steps_to_clean_one": config['drainage_parameters']['steps_to_clean_one']
        },
        "traffic_flow": {group: count for group, count in sorted_groups},
        "batches": batches,
        "drainage_order": sorted_points
    }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n  Saved to: {output_path}")
    print(f"  Total groups: {len(sorted_points)}")
    print(f"  Total batches: {len(batches)}")
    
    return result


def generate_random_strategy(config, output_path):
    """
    Generate random drainage strategy (kept for reference, but now using worst strategy)
    """
    import random
    
    print("\n[RANDOM STRATEGY] Generating...")
    print("-" * 60)
    
    flood_points = config['waterlogging_points']
    seed = config['strategies']['random'].get('seed', 42)
    random.seed(seed)
    
    # Shuffle groups
    groups = list(flood_points.keys())
    random.shuffle(groups)
    
    print(f"\n  Random order (seed={seed}): {groups}")
    
    # Create batches
    max_clean_at_once = config['drainage_parameters']['max_clean_at_once']
    batches = []
    for i in range(0, len(groups), max_clean_at_once):
        batch = groups[i:i+max_clean_at_once]
        batches.append(batch)
    
    print(f"  Drainage batches: {batches}")
    
    # Build result
    result = {
        "strategy_name": "random",
        "description": "Random drainage order",
        "config": {
            "max_clean_at_once": max_clean_at_once,
            "steps_to_clean_one": config['drainage_parameters']['steps_to_clean_one'],
            "random_seed": seed
        },
        "batches": batches,
        "drainage_order": groups
    }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n  Saved to: {output_path}")
    print(f"  Total groups: {len(groups)}")
    print(f"  Total batches: {len(batches)}")
    
    return result


def main():
    print("="*80)
    print("Waterlogging Drainage Strategy Generation".center(80))
    print("="*80)
    
    # Load config
    config = load_config()
    
    # Create output directory
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(config['output']['base_dir']) / f"strategies_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nOutput directory: {output_dir}")
    
    results = {}
    
    # Generate best strategy
    if config['strategies']['best']['enabled']:
        best_file = output_dir / 'best_strategy.json'
        best_result = generate_best_strategy(config, best_file)
        results['best'] = best_result
    
    # Generate worst strategy (instead of random)
    if config['strategies']['random']['enabled']:
        worst_file = output_dir / 'worst_strategy.json'
        worst_result = generate_worst_strategy(config, worst_file)
        results['worst'] = worst_result
    
    # Save summary
    summary_file = output_dir / 'summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "strategies": list(results.keys())
        }, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("Strategy generation completed!".center(80))
    print("="*80)
    
    return results


if __name__ == '__main__':
    main()
