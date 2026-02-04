"""
扫雪算法主运行脚本
包含策略生成、评估和对比的完整流程
"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='扫雪算法仿真系统主程序',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整运行（生成greedy策略+评估）
  python main.py --full
  
  # 生成指定策略
  python main.py --generate -s greedy
  python main.py --generate -s random --seed 42
  
  # 评估指定策略
  python main.py --evaluate -s greedy
  
  # 对比多个策略
  python main.py --compare -s greedy random
  
  # 生成并评估baseline
  python main.py --baseline
  
  # 自定义配置文件
  python main.py --full -c my_config.json
        """
    )
    
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-s', '--strategy', default='greedy',
                       help='策略名称 (默认: greedy)')
    parser.add_argument('--seed', type=int, default=None,
                       help='随机种子（仅用于random策略）')
    
    # 操作模式
    parser.add_argument('--full', action='store_true',
                       help='运行完整流程（生成+评估指定策略）')
    parser.add_argument('--generate', action='store_true',
                       help='只生成指定策略')
    parser.add_argument('--evaluate', action='store_true',
                       help='只评估指定策略')
    parser.add_argument('--compare', action='store_true',
                       help='对比多个策略（需配合-s指定多个策略名）')
    parser.add_argument('--baseline', action='store_true',
                       help='生成并评估baseline（所有道路已清扫）')
    
    args = parser.parse_args()
    
    # 检查配置文件
    if not Path(args.config).exists():
        print(f"错误: 配置文件 {args.config} 不存在！")
        return
    
    # 默认运行完整流程
    if not (args.full or args.generate or args.evaluate or args.compare or args.baseline):
        args.full = True
    
    print("="*80)
    print("扫雪算法仿真系统".center(80))
    print("="*80)
    print(f"\n配置文件: {args.config}")
    
    # 生成策略
    if args.full or args.generate:
        print("\n" + "="*80)
        print(f"[步骤 1/2] 生成 {args.strategy} 策略".center(80))
        print("="*80)
        
        from generate_strategies import StrategyGenerator
        generator = StrategyGenerator(args.config)
        
        kwargs = {}
        if args.strategy == 'random' and args.seed is not None:
            kwargs['random_seed'] = args.seed
        
        generator.run(strategy_name=args.strategy, **kwargs)
    
    # 评估策略
    if args.full or args.evaluate:
        print("\n" + "="*80)
        print(f"[步骤 2/2] 评估 {args.strategy} 策略".center(80))
        print("="*80)
        
        # 检查策略记录是否存在
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        output_dir = Path(config['output']['base_dir'])
        records_file = output_dir / f"snowplow_{args.strategy}_time_steps_record.json"
        
        if not records_file.exists():
            print(f"\n错误: 策略记录文件 {records_file} 不存在！")
            print("请先运行策略生成步骤。")
            return
        
        from evaluate_strategies import StrategyEvaluator
        evaluator = StrategyEvaluator(args.config)
        evaluator.run(strategy_name=args.strategy)
    
    # 对比策略
    if args.compare:
        print("\n" + "="*80)
        print("策略对比".center(80))
        print("="*80)
        
        # 解析策略名称（支持空格分隔）
        strategies = args.strategy.split()
        
        if len(strategies) < 2:
            print("\n错误: 对比模式需要至少2个策略名称")
            print("示例: python main.py --compare -s 'greedy random'")
            return
        
        from compare_results import StrategyComparator
        comparator = StrategyComparator(args.config)
        comparator.run(strategies)
    
    # Baseline
    if args.baseline:
        print("\n" + "="*80)
        print("[Baseline] 生成并评估Baseline场景".center(80))
        print("="*80)
        
        print("\n[1/2] 生成Baseline策略记录...")
        import subprocess
        result = subprocess.run(['python', 'generate_baseline_strategy.py', '-c', args.config])
        
        if result.returncode == 0:
            print("\n[2/2] 评估Baseline场景...")
            subprocess.run(['python', 'evaluate_baseline.py', '-c', args.config])
    
    print("\n" + "="*80)
    print("所有任务完成！".center(80))
    print("="*80)


if __name__ == "__main__":
    main()
