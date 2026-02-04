"""
扫雪策略评估器
统一的SUMO评估接口，支持评估不同策略
"""

import json
import traci
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class StrategyEvaluator:
    """统一的策略评估器"""
    
    def __init__(self, config_path='config.json'):
        """初始化评估器"""
        print("="*80)
        print("扫雪策略SUMO评估器".center(80))
        print("="*80)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.use_scaled = self.config['sumo_config']['use_scaled']
        if self.use_scaled:
            self.sumo_config = self.config['sumo_config']['config_file_scaled']
            print(f"\n使用配置: 缩减版(10%)")
        else:
            self.sumo_config = self.config['sumo_config']['config_file']
            print(f"\n使用配置: 完整版")
        
        self.simulation_steps = self.config['sumo_config']['simulation_steps']
        self.evaluation_hours = self.config['sumo_config']['evaluation_hours']
        
        self.cleaned_params = self.config['road_parameters']['cleaned']
        self.unclean_params = self.config['road_parameters']['unclean']
        
        print(f"配置文件: {self.sumo_config}")
        print(f"仿真步数: {self.simulation_steps}")
        print(f"评估时间点: {self.evaluation_hours}")
    
    def load_strategy_records(self, strategy_name):
        """加载策略记录文件"""
        output_dir = Path(self.config['output']['base_dir'])
        records_file = output_dir / f"snowplow_{strategy_name}_time_steps_record.json"
        
        if not records_file.exists():
            raise FileNotFoundError(f"策略记录文件不存在: {records_file}")
        
        with open(records_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_cleaned_edges_at_time(self, records, time_minutes):
        """获取指定时间已清扫的道路集合"""
        time_steps = []
        for key, value in records.items():
            time_steps.append((value['time_minutes'], key))
        
        time_steps.sort()
        
        target_key = None
        for t_min, key in time_steps:
            if t_min <= time_minutes:
                target_key = key
            else:
                break
        
        if target_key is None:
            return set()
        
        return set(records[target_key]['total_cleaned_edges'])
    
    def evaluate_strategy(self, strategy_name):
        """评估指定策略"""
        print(f"\n{'='*80}")
        print(f"评估策略: {strategy_name}".center(80))
        print(f"{'='*80}")
        
        # 加载策略记录
        try:
            strategy_records = self.load_strategy_records(strategy_name)
        except FileNotFoundError as e:
            print(f"\n错误: {e}")
            return None
        
        results = {}
        
        for hour in self.evaluation_hours:
            print(f"\n{'='*60}")
            print(f"评估第 {hour} 小时的场景...")
            print(f"{'='*60}")
            
            time_minutes = hour * 60
            cleaned_edges = self.get_cleaned_edges_at_time(strategy_records, time_minutes)
            print(f"已清扫道路数量: {len(cleaned_edges)}")
            
            traci.start(["sumo", "-c", self.sumo_config, "--start",
                        "--no-warnings", "true"])
            
            for step in range(self.simulation_steps):
                traci.simulationStep()
                
                current_vehicles = traci.vehicle.getIDList()
                
                for veh_id in current_vehicles:
                    current_edge = traci.vehicle.getRoadID(veh_id)
                    
                    if current_edge in cleaned_edges:
                        params = self.cleaned_params
                    else:
                        params = self.unclean_params
                    
                    traci.vehicle.setAcceleration(veh_id, params["accel"], 1)
                    traci.vehicle.setDecel(veh_id, params["decel"])
                    traci.vehicle.setMaxSpeed(veh_id, params["max_speed"])
                    traci.vehicle.setMinGap(veh_id, params["min_gap"])
                
                if (step + 1) % 50 == 0:
                    print(f"  仿真进度: {step + 1}/{self.simulation_steps} 步, "
                          f"当前车辆数: {len(current_vehicles)}")
            
            current_vehicles = traci.vehicle.getIDList()
            num_vehicles = len(current_vehicles)
            
            if num_vehicles > 0:
                total_speed = sum(traci.vehicle.getSpeed(veh) for veh in current_vehicles)
                global_avg_speed = total_speed / num_vehicles
            else:
                global_avg_speed = 0
            
            print(f"\n  仿真完成 - 第{self.simulation_steps}步统计:")
            print(f"    车辆数: {num_vehicles}")
            print(f"    全局平均速度: {global_avg_speed:.2f} m/s "
                  f"({global_avg_speed * 3.6:.2f} km/h)")
            
            traci.close()
            
            results[f"hour_{hour}"] = {
                "time_hours": hour,
                "time_minutes": time_minutes,
                "num_cleaned_edges": len(cleaned_edges),
                "simulation_steps": self.simulation_steps,
                "num_vehicles": num_vehicles,
                "global_avg_speed_ms": global_avg_speed,
                "global_avg_speed_kmh": global_avg_speed * 3.6
            }
        
        return results
    
    def save_results(self, strategy_name, results):
        """保存评估结果"""
        output_dir = Path(self.config['output']['base_dir'])
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / f"sumo_evaluation_{strategy_name}_results.json"
        
        evaluation_data = {
            "strategy_name": strategy_name,
            "config": {
                "sumo_config_file": self.sumo_config,
                "simulation_steps": self.simulation_steps,
                "use_scaled": self.use_scaled
            },
            "results": results
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n评估结果已保存至: {results_file}")
        return results_file
    
    def plot_results(self, strategy_name, results):
        """可视化评估结果"""
        hours = []
        speeds_ms = []
        speeds_kmh = []
        num_cleaned = []
        
        for key in sorted(results.keys()):
            hour_data = results[key]
            hours.append(hour_data['time_hours'])
            speeds_ms.append(hour_data['global_avg_speed_ms'])
            speeds_kmh.append(hour_data['global_avg_speed_kmh'])
            num_cleaned.append(hour_data['num_cleaned_edges'])
        
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 平均速度
        ax1.plot(hours, speeds_ms, marker='o', linewidth=3, markersize=10,
                color='tab:blue', label=f'{strategy_name}策略 平均速度')
        ax1.set_xlabel('时间（小时）', fontsize=14)
        ax1.set_ylabel('全局平均速度 (m/s)', fontsize=14)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.legend(loc='upper left', fontsize=12)
        ax1.set_title(f'{strategy_name}策略：全局平均速度随时间变化', 
                     fontsize=16, fontweight='bold', pad=20)
        
        # 已清扫道路数
        ax2.bar(hours, num_cleaned, color='tab:green', alpha=0.6, 
               label=f'{strategy_name}策略 已清扫道路')
        ax2.set_xlabel('时间（小时）', fontsize=14)
        ax2.set_ylabel('已清扫道路数量', fontsize=14)
        ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax2.legend(loc='upper left', fontsize=12)
        ax2.set_title(f'{strategy_name}策略：扫雪进度', 
                     fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        output_dir = Path(self.config['output']['base_dir'])
        plot_file = output_dir / f'evaluation_{strategy_name}_plots.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"图表已保存至: {plot_file}")
        plt.close()
    
    def run(self, strategy_name='greedy'):
        """运行完整评估流程"""
        results = self.evaluate_strategy(strategy_name)
        if results:
            self.save_results(strategy_name, results)
            self.plot_results(strategy_name, results)
            
            print("\n" + "="*80)
            print(f"{strategy_name}策略评估完成！".center(80))
            print("="*80)
        
        return results


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='扫雪策略SUMO评估器')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-s', '--strategy', default='greedy',
                       help='策略名称 (默认: greedy)')
    args = parser.parse_args()
    
    evaluator = StrategyEvaluator(args.config)
    evaluator.run(strategy_name=args.strategy)


if __name__ == "__main__":
    main()
