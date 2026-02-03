"""
扫雪策略生成和评估系统 - 主入口
使用JSON配置文件驱动整个流程
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from strategies.greedy_strategy import GreedyStrategy
from strategies.random_strategy import RandomStrategy


def load_config(config_path='config.json'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    print("="*80)
    print("Snow Plowing Strategy Generation System".center(80))
    print("="*80)
    
    # 1. Load configuration
    print("\n[1/2] Loading configuration...")
    config = load_config()
    print(f"  Project: {config['project_name']}")
    print(f"  Num trucks: {config['snowplow_parameters']['num_trucks']}")
    print(f"  Num regions: {config['snowplow_parameters']['num_regions']}")
    print(f"  Max time: {config['snowplow_parameters']['max_time_minutes']} minutes")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(config['output']['base_dir']) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {output_dir}")
    
    results = {
        "config": {
            "num_trucks": config['snowplow_parameters']['num_trucks'],
            "num_regions": config['snowplow_parameters']['num_regions'],
            "speed_clean": config['snowplow_parameters']['speed_clean'],
            "speed_pass": config['snowplow_parameters']['speed_pass'],
            "max_time_minutes": config['snowplow_parameters']['max_time_minutes']
        },
        "timestamp": timestamp,
        "strategies": {}
    }
    
    # 2. Generate strategies
    print("\n[2/2] Generating snow plowing strategies...")
    
    if config['strategies']['greedy']['enabled']:
        print("  - Generating greedy strategy...")
        greedy = GreedyStrategy(config)
        greedy_result = greedy.generate()
        
        greedy_file = output_dir / 'greedy_strategy.json'
        with open(greedy_file, 'w', encoding='utf-8') as f:
            json.dump(greedy_result, f, ensure_ascii=False, indent=2)
        
        results['strategies']['greedy'] = {
            "file": str(greedy_file),
            "summary": greedy_result['summary']
        }
        print(f"    Saved: {greedy_file}")
    
    if config['strategies']['random']['enabled']:
        print("  - Generating random strategy...")
        random_strat = RandomStrategy(config)
        random_result = random_strat.generate()
        
        random_file = output_dir / 'random_strategy.json'
        with open(random_file, 'w', encoding='utf-8') as f:
            json.dump(random_result, f, ensure_ascii=False, indent=2)
        
        results['strategies']['random'] = {
            "file": str(random_file),
            "summary": random_result['summary']
        }
        print(f"    Saved: {random_file}")
        print("\n[3/5] 生成可视化动画...")
        gif_gen = GIFGenerator(config)
        print(f"    Saved: {random_file}")
    
    # Save summary
    summary_file = output_dir / 'summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("Completed!".center(80))
    print(f"Output directory: {output_dir}".center(80))
    print("="*80)
    
    return results


if __name__ == '__main__':
    main()
