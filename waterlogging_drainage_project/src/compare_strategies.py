"""
Compare drainage strategies
Generate comparison report and charts
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse

import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False


def load_evaluation_result(eval_file):
    """Load evaluation result"""
    with open(eval_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_results(eval_files, output_dir=None):
    """
    Compare multiple strategy evaluation results
    """
    print("="*80)
    print("Drainage Strategy Comparison".center(80))
    print("="*80)
    
    # Create output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path('results') / f"comparison_{timestamp}"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")
    
    # Load all evaluations
    evaluations = {}
    for eval_file in eval_files:
        eval_data = load_evaluation_result(eval_file)
        strategy_name = eval_data['strategy_name']
        evaluations[strategy_name] = eval_data
        print(f"  Loaded: {strategy_name} - {eval_file}")
    
    # Prepare comparison data
    comparison = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "strategies": list(evaluations.keys()),
        "comparison_data": {}
    }
    
    # Extract evaluation delays
    evaluation_delays = list(evaluations.values())[0]['config'].get('evaluation_delays', [0])
    default_delay = evaluation_delays[-1]  # Use last delay for summary
    
    # Extract data by batch completion
    batch_indices = evaluations[list(evaluations.keys())[0]]['batch_results']
    batch_indices = [b['batch_index'] for b in batch_indices]
    
    for batch_idx in batch_indices:
        comparison['comparison_data'][f"batch_{batch_idx}"] = {}
        for strategy_name, eval_data in evaluations.items():
            batch_data = next(b for b in eval_data['batch_results'] if b['batch_index'] == batch_idx)
            # Get measurement at default delay
            delay_data = next((d for d in batch_data['delay_measurements'] if d['delay_steps'] == default_delay),
                            batch_data['delay_measurements'][-1])
            comparison['comparison_data'][f"batch_{batch_idx}"][strategy_name] = {
                "drained_groups": batch_data['num_drained'],
                "cumulative_throughput": delay_data['cumulative_throughput'],
                "queue_length": delay_data['queue_length'],
                "avg_speed": delay_data['avg_speed']
            }
    
    # Generate comparison charts
    print("\nGenerating comparison charts...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Throughput comparison (higher = better)
    for strategy_name, eval_data in evaluations.items():
        batch_list = [b['batch_index'] for b in eval_data['batch_results']]
        throughput = [next((d for d in b['delay_measurements'] if d['delay_steps'] == default_delay), 
                          b['delay_measurements'][-1])['cumulative_throughput'] 
                     for b in eval_data['batch_results']]
        axes[0, 0].plot(batch_list, throughput, marker='o', linewidth=2, label=strategy_name)
    
    axes[0, 0].set_xlabel('Batches Completed', fontsize=12)
    axes[0, 0].set_ylabel('Cumulative Throughput (vehicles)', fontsize=12)
    axes[0, 0].set_title(f'Cumulative Throughput (at {default_delay}s delay) - Higher=Better', fontsize=13, fontweight='bold')
    axes[0, 0].legend(fontsize=10)
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Queue length comparison (lower = better)
    for strategy_name, eval_data in evaluations.items():
        batch_list = [b['batch_index'] for b in eval_data['batch_results']]
        queue = [next((d for d in b['delay_measurements'] if d['delay_steps'] == default_delay),
                     b['delay_measurements'][-1])['queue_length']
                for b in eval_data['batch_results']]
        axes[0, 1].plot(batch_list, queue, marker='s', linewidth=2, label=strategy_name)
    
    axes[0, 1].set_xlabel('Batches Completed', fontsize=12)
    axes[0, 1].set_ylabel('Queue Length (vehicles)', fontsize=12)
    axes[0, 1].set_title(f'Queue Length (at {default_delay} steps delay) - Lower=Better', fontsize=13, fontweight='bold')
    axes[0, 1].legend(fontsize=10)
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Average speed comparison (higher = better)
    for strategy_name, eval_data in evaluations.items():
        batch_list = [b['batch_index'] for b in eval_data['batch_results']]
        speeds = [next((d for d in b['delay_measurements'] if d['delay_steps'] == default_delay),
                      b['delay_measurements'][-1])['avg_speed']
                 for b in eval_data['batch_results']]
        axes[1, 0].plot(batch_list, speeds, marker='^', linewidth=2, label=strategy_name)
    
    axes[1, 0].set_xlabel('Batches Completed', fontsize=12)
    axes[1, 0].set_ylabel('Avg Speed (m/s)', fontsize=12)
    axes[1, 0].set_title(f'Speed (at {default_delay} steps delay) - Higher=Better', fontsize=13, fontweight='bold')
    axes[1, 0].legend(fontsize=10)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Drained groups progress
    for strategy_name, eval_data in evaluations.items():
        batch_list = [b['batch_index'] for b in eval_data['batch_results']]
        drained = [b['num_drained'] for b in eval_data['batch_results']]
        axes[1, 1].plot(batch_list, drained, marker='d', linewidth=2, label=strategy_name)
    
    axes[1, 1].set_xlabel('Batches Completed', fontsize=12)
    axes[1, 1].set_ylabel('Num Drained Groups', fontsize=12)
    axes[1, 1].set_title('Drainage Progress', fontsize=13, fontweight='bold')
    axes[1, 1].legend(fontsize=10)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    chart_file = output_dir / "comparison_chart.png"
    plt.savefig(chart_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Charts saved: {chart_file}")
    
    # Generate text report
    print("\nGenerating text report...")
    report_lines = []
    report_lines.append("="*100)
    report_lines.append(f"{'Batch':<10}{'Strategy':<15}{'Drained':<12}{'Throughput':<15}{'Queue':<15}{'Speed(m/s)':<15}")
    report_lines.append("-"*100)
    plt.tight_layout()
    chart_file = output_dir / "comparison_chart.png"
    plt.savefig(chart_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Charts saved: {chart_file}")
    
    # Generate text report
    print("\nGenerating text report...")
    report_lines = []
    report_lines.append("="*100)
    report_lines.append("Waterlogging Drainage Strategy Comparison Report".center(100))
    report_lines.append("="*100)
    report_lines.append(f"\nGeneration time: {comparison['timestamp']}")
    report_lines.append(f"Strategies compared: {', '.join(evaluations.keys())}")
    
    # Add strategy descriptions
    report_lines.append("\n" + "-"*100)
    report_lines.append("STRATEGY DESCRIPTIONS:")
    report_lines.append("-"*100)
    for strategy_name, eval_data in evaluations.items():
        batches = eval_data['batch_results'][1]['drained_groups'] if len(eval_data['batch_results']) > 1 else []
        report_lines.append(f"  {strategy_name.upper()}: {batches}")
    
    # Add metrics explanation
    report_lines.append("\n" + "-"*100)
    report_lines.append("METRICS EXPLANATION:")
    report_lines.append("-"*100)
    report_lines.append("  - Cumulative Throughput: Total vehicles LEAVING waterlogging region (higher = better)")
    report_lines.append("  - Queue Length: Average vehicles stuck in waterlogging areas (lower = better)")
    report_lines.append("  - Avg Speed: Average speed in waterlogging areas in m/s (higher = better)")
    report_lines.append(f"  - Measurement Window: {evaluations[list(evaluations.keys())[0]].get('config', {}).get('measurement_window', 200)} seconds")
    report_lines.append(f"  - Evaluation Delays: {evaluations[list(evaluations.keys())[0]].get('config', {}).get('evaluation_delays', [30, 60, 120])} steps")
    
    report_lines.append("\n" + "="*100)
    report_lines.append("DETAILED RESULTS (at default delay = {} steps)".format(default_delay).center(100))
    report_lines.append("="*100)
    report_lines.append(f"{'Batch':<10}{'Strategy':<20}{'Drained':<12}{'Cumulative':<18}{'Queue':<18}{'Speed(m/s)':<18}")
    report_lines.append("-"*100)
    
    for batch_idx in batch_indices:
        batch_key = f"batch_{batch_idx}"
        for strategy_name in evaluations.keys():
            data = comparison['comparison_data'][batch_key][strategy_name]
            report_lines.append(
                f"{batch_idx:<10}{strategy_name:<20}{data['drained_groups']:<12}"
                f"{data['cumulative_throughput']:<18}{data['queue_length']:<18.2f}{data['avg_speed']:<18.3f}"
            )
        report_lines.append("-"*100)
    
    # Add improvement analysis
    report_lines.append("\n" + "="*100)
    report_lines.append("IMPROVEMENT ANALYSIS".center(100))
    report_lines.append("="*100)
    strategies = list(evaluations.keys())
    if len(strategies) == 2:
        strategy1, strategy2 = strategies
        report_lines.append(f"\nComparing '{strategy1}' vs '{strategy2}':\n")
        report_lines.append(f"{'Batch':<10}{'Metric':<25}{'Strategy 1':<20}{'Strategy 2':<20}{'Difference':<20}")
        report_lines.append("-"*100)
        
        for batch_idx in [1, 2]:  # Skip batch 0 and 3 (all flooded/all drained)
            batch_key = f"batch_{batch_idx}"
            if batch_key in comparison['comparison_data']:
                data1 = comparison['comparison_data'][batch_key][strategy1]
                data2 = comparison['comparison_data'][batch_key][strategy2]
                
                # Throughput
                diff_throughput = data1['cumulative_throughput'] - data2['cumulative_throughput']
                pct_throughput = (diff_throughput / data2['cumulative_throughput'] * 100) if data2['cumulative_throughput'] > 0 else 0
                report_lines.append(
                    f"{batch_idx:<10}{'Cumulative Throughput':<25}{data1['cumulative_throughput']:<20}"
                    f"{data2['cumulative_throughput']:<20}{diff_throughput:+.0f} ({pct_throughput:+.1f}%)"
                )
                
                # Queue
                diff_queue = data1['queue_length'] - data2['queue_length']
                pct_queue = (diff_queue / data2['queue_length'] * 100) if data2['queue_length'] > 0 else 0
                report_lines.append(
                    f"{'':<10}{'Queue Length':<25}{data1['queue_length']:<20.2f}"
                    f"{data2['queue_length']:<20.2f}{diff_queue:+.2f} ({pct_queue:+.1f}%)"
                )
                
                # Speed
                diff_speed = data1['avg_speed'] - data2['avg_speed']
                pct_speed = (diff_speed / data2['avg_speed'] * 100) if data2['avg_speed'] > 0 else 0
                report_lines.append(
                    f"{'':<10}{'Avg Speed':<25}{data1['avg_speed']:<20.3f}"
                    f"{data2['avg_speed']:<20.3f}{diff_speed:+.3f} ({pct_speed:+.1f}%)"
                )
                report_lines.append("-"*100)
    
    report_text = '\n'.join(report_lines)
    report_file = output_dir / 'comparison_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n  Text report saved: {report_file}")
    
    # Save JSON result
    json_file = output_dir / 'comparison_report.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    print(f"  JSON report saved: {json_file}")
    
    print("\n" + "="*80)
    print("Comparison completed!".center(80))
    print("="*80)
    
    return comparison


def main():
    parser = argparse.ArgumentParser(description='Compare drainage strategy evaluations')
    parser.add_argument('-e', '--evaluations', nargs='+', required=True,
                       help='Evaluation result JSON files')
    parser.add_argument('-o', '--output', default=None,
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Run comparison
    results = compare_results(args.evaluations, args.output)
    
    return results


if __name__ == '__main__':
    main()
