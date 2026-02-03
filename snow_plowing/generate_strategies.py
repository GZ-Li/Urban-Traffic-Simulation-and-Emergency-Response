"""
策略生成器 - 独立运行
只负责生成扫雪策略，不运行SUMO模拟
输入：config.json
输出：strategy_*.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from strategies.greedy_strategy import GreedyStrategy
from strategies.random_strategy import RandomStrategy


def load_config(config_path='config.json'):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_strategies(config, output_dir=None, strategies_to_run=None):
    """
    生成扫雪策略
    
    Args:
        config: 配置字典
        output_dir: 输出目录，如果为None则创建时间戳目录
        strategies_to_run: 要运行的策略列表，如['greedy', 'random']，None表示全部
    
    Returns:
        dict: 包含生成结果的字典
    """
    print("="*80)
    print("扫雪策略生成器".center(80))
    print("="*80)
    
    # 创建输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(config['output']['base_dir']) / f"strategies_{timestamp}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {output_dir}")
    
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config_used": {
            "num_trucks": config['snowplow_parameters']['num_trucks'],
            "max_time_minutes": config['snowplow_parameters']['max_time_minutes'],
            "speed_clean": config['snowplow_parameters']['speed_clean'],
            "speed_pass": config['snowplow_parameters']['speed_pass'],
            "unified_start_edge": config['snowplow_parameters']['unified_start_edge']
        },
        "strategies": {}
    }
    
    # 生成贪心策略
    if (strategies_to_run is None or 'greedy' in strategies_to_run) and \
       config['strategies']['greedy']['enabled']:
        print("\n[1] 生成贪心策略...")
        print("-" * 60)
        greedy = GreedyStrategy(config)
        greedy_result = greedy.generate()
        
        greedy_file = output_dir / 'greedy_strategy.json'
        with open(greedy_file, 'w', encoding='utf-8') as f:
            json.dump(greedy_result, f, ensure_ascii=False, indent=2)
        
        results['strategies']['greedy'] = {
            "name": config['strategies']['greedy']['name'],
            "file": str(greedy_file),
            "summary": greedy_result['summary']
        }
        print(f"    保存至: {greedy_file}")
        print(f"    清扫道路: {greedy_result['summary']['total_roads_cleaned']} 条")
        print(f"    用时: {greedy_result['summary']['total_time_minutes']:.1f} 分钟")
    
    # 生成随机策略
    if (strategies_to_run is None or 'random' in strategies_to_run) and \
       config['strategies']['random']['enabled']:
        print("\n[2] 生成随机策略...")
        print("-" * 60)
        random_strat = RandomStrategy(config)
        random_result = random_strat.generate()
        
        random_file = output_dir / 'random_strategy.json'
        with open(random_file, 'w', encoding='utf-8') as f:
            json.dump(random_result, f, ensure_ascii=False, indent=2)
        
        results['strategies']['random'] = {
            "name": config['strategies']['random']['name'],
            "file": str(random_file),
            "summary": random_result['summary']
        }
        print(f"    保存至: {random_file}")
        print(f"    清扫道路: {random_result['summary']['total_roads_cleaned']} 条")
        print(f"    用时: {random_result['summary']['total_time_minutes']:.1f} 分钟")
    
    # 保存元数据
    meta_file = output_dir / 'generation_summary.json'
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("策略生成完成！".center(80))
    print(f"结果目录: {output_dir}".center(80))
    print("="*80)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='生成扫雪策略')
    parser.add_argument('-c', '--config', default='config.json', 
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-o', '--output', default=None,
                       help='输出目录 (默认: 自动创建时间戳目录)')
    parser.add_argument('-s', '--strategies', nargs='+', 
                       choices=['greedy', 'random'],
                       help='指定要生成的策略 (默认: 全部)')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 生成策略
    results = generate_strategies(config, args.output, args.strategies)
    
    return results


if __name__ == '__main__':
    main()
