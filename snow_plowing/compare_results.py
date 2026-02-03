"""
策略对比分析器
读取多个评估结果，生成对比报告和可视化
输入：evaluation_*.json
输出：comparison_report.json + 图表
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False


def load_evaluation_result(eval_file):
    """加载评估结果"""
    with open(eval_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_results(eval_files, output_dir=None):
    """
    对比多个策略的评估结果
    
    Args:
        eval_files: 评估结果文件列表
        output_dir: 输出目录
    
    Returns:
        dict: 对比结果
    """
    print("="*80)
    print("策略对比分析".center(80))
    print("="*80)
    
    # 创建输出目录
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('results') / f"comparison_{timestamp}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {output_dir}")
    
    # 加载所有评估结果
    evaluations = {}
    for eval_file in eval_files:
        eval_data = load_evaluation_result(eval_file)
        strategy_name = eval_data['strategy_name']
        evaluations[strategy_name] = eval_data
        print(f"  加载: {strategy_name} - {eval_file}")
    
    # 准备对比数据
    comparison = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "strategies": list(evaluations.keys()),
        "comparison_data": {}
    }
    
    # 提取每个时间点的数据
    hours = evaluations[list(evaluations.keys())[0]]['hourly_results']
    hours = [h['hour'] for h in hours]
    
    for hour in hours:
        comparison['comparison_data'][f"hour_{hour}"] = {}
        for strategy_name, eval_data in evaluations.items():
            hourly_data = next(h for h in eval_data['hourly_results'] if h['hour'] == hour)
            comparison['comparison_data'][f"hour_{hour}"][strategy_name] = {
                "roads_cleaned": hourly_data['roads_cleaned'],
                "average_speed_ms": hourly_data['average_speed_ms'],
                "total_vehicles": hourly_data['total_vehicles']
            }
    
    # 生成对比图表
    print("\n生成对比图表...")
    
    # 1. 平均速度对比
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    for strategy_name, eval_data in evaluations.items():
        hours_list = [h['hour'] for h in eval_data['hourly_results']]
        speeds = [h['average_speed_ms'] for h in eval_data['hourly_results']]
        ax1.plot(hours_list, speeds, marker='o', linewidth=2, label=strategy_name)
    
    ax1.set_xlabel('时间 (小时)', fontsize=12)
    ax1.set_ylabel('平均速度 (m/s)', fontsize=12)
    ax1.set_title('不同策略下的平均车速变化', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 2. 清扫道路数对比
    for strategy_name, eval_data in evaluations.items():
        hours_list = [h['hour'] for h in eval_data['hourly_results']]
        roads = [h['roads_cleaned'] for h in eval_data['hourly_results']]
        ax2.plot(hours_list, roads, marker='s', linewidth=2, label=strategy_name)
    
    ax2.set_xlabel('时间 (小时)', fontsize=12)
    ax2.set_ylabel('已清扫道路数', fontsize=12)
    ax2.set_title('清扫道路数随时间变化', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_file = output_dir / 'comparison_chart.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    plt.savefig(output_dir / 'comparison_chart.pdf', bbox_inches='tight')
    plt.close()
    
    print(f"  图表保存至: {chart_file}")
    
    # 生成文本报告
    print("\n生成文本报告...")
    report_lines = []
    report_lines.append("="*80)
    report_lines.append("策略对比报告".center(80))
    report_lines.append("="*80)
    report_lines.append(f"\n生成时间: {comparison['timestamp']}")
    report_lines.append(f"对比策略: {', '.join(evaluations.keys())}\n")
    
    report_lines.append("-"*80)
    report_lines.append(f"{'时间(h)':<10}{'策略':<15}{'清扫道路':<15}{'平均速度(m/s)':<20}{'车辆数':<15}")
    report_lines.append("-"*80)
    
    for hour in hours:
        hour_key = f"hour_{hour}"
        for strategy_name in evaluations.keys():
            data = comparison['comparison_data'][hour_key][strategy_name]
            report_lines.append(
                f"{hour:<10}{strategy_name:<15}{data['roads_cleaned']:<15}"
                f"{data['average_speed_ms']:<20.3f}{data['total_vehicles']:<15}"
            )
        report_lines.append("-"*80)
    
    report_text = '\n'.join(report_lines)
    report_file = output_dir / 'comparison_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n  文本报告保存至: {report_file}")
    
    # 保存JSON结果
    json_file = output_dir / 'comparison_report.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    print(f"  JSON报告保存至: {json_file}")
    
    print("\n" + "="*80)
    print("对比分析完成！".center(80))
    print("="*80)
    
    return comparison


def main():
    parser = argparse.ArgumentParser(description='对比分析多个策略的评估结果')
    parser.add_argument('-e', '--evaluations', nargs='+', required=True,
                       help='评估结果JSON文件列表')
    parser.add_argument('-o', '--output', default=None,
                       help='输出目录 (默认: 自动创建时间戳目录)')
    
    args = parser.parse_args()
    
    # 运行对比分析
    results = compare_results(args.evaluations, args.output)
    
    return results


if __name__ == '__main__':
    main()
