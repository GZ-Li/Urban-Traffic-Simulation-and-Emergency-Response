"""
策略对比工具
比较不同扫雪策略的性能，生成对比图表和报告
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime


class StrategyComparator:
    """策略对比器"""
    
    def __init__(self, config_path='config.json'):
        """初始化对比器"""
        print("="*80)
        print("扫雪策略对比工具".center(80))
        print("="*80)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.output_dir = Path(self.config['output']['base_dir'])
    
    def load_evaluation_results(self, strategy_name):
        """加载策略评估结果"""
        results_file = self.output_dir / f"sumo_evaluation_{strategy_name}_results.json"
        
        if not results_file.exists():
            print(f"警告: 未找到 {strategy_name} 的评估结果: {results_file}")
            return None
        
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def compare_strategies(self, strategy_names):
        """
        对比多个策略
        
        Args:
            strategy_names: 策略名称列表，如 ['greedy', 'random']
        
        Returns:
            comparison_data: 对比数据字典
        """
        print(f"\n对比策略: {', '.join(strategy_names)}")
        print("-"*80)
        
        # 加载所有策略的结果
        all_results = {}
        for name in strategy_names:
            results = self.load_evaluation_results(name)
            if results:
                all_results[name] = results
                print(f"  ✓ 加载 {name} 策略结果")
            else:
                print(f"  ✗ 跳过 {name} 策略（未找到结果）")
        
        if len(all_results) < 2:
            print("\n错误: 至少需要2个策略的评估结果才能对比")
            return None
        
        # 提取对比数据
        comparison_data = {
            "strategies": {},
            "time_points": []
        }
        
        for name, data in all_results.items():
            strategy_data = {
                "hours": [],
                "speeds_ms": [],
                "speeds_kmh": [],
                "num_cleaned": [],
                "num_vehicles": []
            }
            
            results = data['results']
            for key in sorted(results.keys()):
                hour_data = results[key]
                strategy_data["hours"].append(hour_data['time_hours'])
                strategy_data["speeds_ms"].append(hour_data['global_avg_speed_ms'])
                strategy_data["speeds_kmh"].append(hour_data['global_avg_speed_kmh'])
                strategy_data["num_cleaned"].append(hour_data['num_cleaned_edges'])
                strategy_data["num_vehicles"].append(hour_data['num_vehicles'])
            
            comparison_data["strategies"][name] = strategy_data
            comparison_data["time_points"] = strategy_data["hours"]
        
        return comparison_data
    
    def calculate_metrics(self, comparison_data):
        """计算对比指标"""
        metrics = {}
        
        for name, data in comparison_data["strategies"].items():
            avg_speed = np.mean(data["speeds_ms"])
            max_speed = np.max(data["speeds_ms"])
            min_speed = np.min(data["speeds_ms"])
            
            final_cleaned = data["num_cleaned"][-1] if data["num_cleaned"] else 0
            
            metrics[name] = {
                "avg_speed_ms": avg_speed,
                "avg_speed_kmh": avg_speed * 3.6,
                "max_speed_ms": max_speed,
                "min_speed_ms": min_speed,
                "final_cleaned_roads": final_cleaned,
                "speed_variance": np.var(data["speeds_ms"])
            }
        
        return metrics
    
    def plot_comparison(self, comparison_data):
        """生成对比图表"""
        print("\n生成对比图表...")
        
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        markers = ['o', 's', '^', 'D', 'v']
        
        # 子图1: 平均速度对比 (m/s)
        for idx, (name, data) in enumerate(comparison_data["strategies"].items()):
            ax1.plot(data["hours"], data["speeds_ms"], 
                    marker=markers[idx % len(markers)], 
                    linewidth=2.5, markersize=8,
                    color=colors[idx % len(colors)], 
                    label=f'{name}策略')
        ax1.set_xlabel('时间（小时）', fontsize=12)
        ax1.set_ylabel('全局平均速度 (m/s)', fontsize=12)
        ax1.set_title('策略对比：全局平均速度 (m/s)', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # 子图2: 平均速度对比 (km/h)
        for idx, (name, data) in enumerate(comparison_data["strategies"].items()):
            ax2.plot(data["hours"], data["speeds_kmh"], 
                    marker=markers[idx % len(markers)], 
                    linewidth=2.5, markersize=8,
                    color=colors[idx % len(colors)], 
                    label=f'{name}策略')
        ax2.set_xlabel('时间（小时）', fontsize=12)
        ax2.set_ylabel('全局平均速度 (km/h)', fontsize=12)
        ax2.set_title('策略对比：全局平均速度 (km/h)', fontsize=14, fontweight='bold')
        ax2.legend(fontsize=11)
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # 子图3: 已清扫道路数对比
        x = np.arange(len(comparison_data["time_points"]))
        width = 0.8 / len(comparison_data["strategies"])
        
        for idx, (name, data) in enumerate(comparison_data["strategies"].items()):
            offset = (idx - len(comparison_data["strategies"])/2 + 0.5) * width
            ax3.bar(x + offset, data["num_cleaned"], width,
                   label=f'{name}策略',
                   color=colors[idx % len(colors)], alpha=0.7)
        
        ax3.set_xlabel('时间（小时）', fontsize=12)
        ax3.set_ylabel('已清扫道路数量', fontsize=12)
        ax3.set_title('策略对比：扫雪进度', fontsize=14, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(comparison_data["time_points"])
        ax3.legend(fontsize=11)
        ax3.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # 子图4: 性能指标对比（雷达图风格的柱状图）
        metrics = self.calculate_metrics(comparison_data)
        metric_names = list(comparison_data["strategies"].keys())
        avg_speeds = [metrics[name]["avg_speed_kmh"] for name in metric_names]
        final_cleaned = [metrics[name]["final_cleaned_roads"] for name in metric_names]
        
        x_pos = np.arange(len(metric_names))
        ax4_twin = ax4.twinx()
        
        bars1 = ax4.bar(x_pos - 0.2, avg_speeds, 0.4, 
                       label='平均速度 (km/h)', color='#FF6B6B', alpha=0.7)
        bars2 = ax4_twin.bar(x_pos + 0.2, final_cleaned, 0.4,
                            label='最终清扫道路数', color='#4ECDC4', alpha=0.7)
        
        ax4.set_xlabel('策略', fontsize=12)
        ax4.set_ylabel('平均速度 (km/h)', fontsize=12, color='#FF6B6B')
        ax4_twin.set_ylabel('最终清扫道路数', fontsize=12, color='#4ECDC4')
        ax4.set_title('策略对比：综合性能指标', fontsize=14, fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(metric_names)
        ax4.tick_params(axis='y', labelcolor='#FF6B6B')
        ax4_twin.tick_params(axis='y', labelcolor='#4ECDC4')
        ax4.legend(loc='upper left', fontsize=10)
        ax4_twin.legend(loc='upper right', fontsize=10)
        ax4.grid(True, alpha=0.3, linestyle='--', axis='y')
        
        plt.tight_layout()
        
        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_file = self.output_dir / f'strategy_comparison_{timestamp}.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"  对比图表已保存: {plot_file}")
        plt.close()
        
        return plot_file
    
    def generate_report(self, comparison_data, metrics):
        """生成对比报告"""
        print("\n生成对比报告...")
        
        report = {
            "comparison_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategies_compared": list(comparison_data["strategies"].keys()),
            "metrics": metrics,
            "summary": {}
        }
        
        # 找出最佳策略
        best_avg_speed = max(metrics.items(), key=lambda x: x[1]["avg_speed_ms"])
        best_final_cleaned = max(metrics.items(), key=lambda x: x[1]["final_cleaned_roads"])
        
        report["summary"]["best_avg_speed"] = {
            "strategy": best_avg_speed[0],
            "value": best_avg_speed[1]["avg_speed_kmh"]
        }
        report["summary"]["best_final_cleaned"] = {
            "strategy": best_final_cleaned[0],
            "value": best_final_cleaned[1]["final_cleaned_roads"]
        }
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f'strategy_comparison_report_{timestamp}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  对比报告已保存: {report_file}")
        
        # 打印摘要
        print("\n" + "="*80)
        print("对比摘要".center(80))
        print("="*80)
        for name, metric in metrics.items():
            print(f"\n{name}策略:")
            print(f"  平均速度: {metric['avg_speed_ms']:.2f} m/s ({metric['avg_speed_kmh']:.2f} km/h)")
            print(f"  最终清扫道路数: {metric['final_cleaned_roads']}")
            print(f"  速度方差: {metric['speed_variance']:.4f}")
        
        print(f"\n最佳平均速度: {best_avg_speed[0]}策略 ({best_avg_speed[1]['avg_speed_kmh']:.2f} km/h)")
        print(f"最多清扫道路: {best_final_cleaned[0]}策略 ({best_final_cleaned[1]['final_cleaned_roads']} 条)")
        print("="*80)
        
        return report_file
    
    def run(self, strategy_names):
        """运行完整对比流程"""
        comparison_data = self.compare_strategies(strategy_names)
        
        if comparison_data is None:
            return None
        
        metrics = self.calculate_metrics(comparison_data)
        plot_file = self.plot_comparison(comparison_data)
        report_file = self.generate_report(comparison_data, metrics)
        
        print("\n" + "="*80)
        print("策略对比完成！".center(80))
        print("="*80)
        
        return {
            "plot_file": plot_file,
            "report_file": report_file,
            "metrics": metrics
        }


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='扫雪策略对比工具')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-s', '--strategies', nargs='+', 
                       default=['greedy', 'random'],
                       help='要对比的策略名称列表 (默认: greedy random)')
    args = parser.parse_args()
    
    comparator = StrategyComparator(args.config)
    comparator.run(args.strategies)


if __name__ == "__main__":
    main()
