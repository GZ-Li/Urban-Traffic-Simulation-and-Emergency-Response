"""
扫雪策略SUMO评估器
基于策略生成的时间步记录，在SUMO环境中评测不同时间点的交通指标
"""

import json
import traci
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict


class SnowplowStrategyEvaluator:
    """扫雪策略评估器"""
    
    def __init__(self, config_path='config.json'):
        """初始化评估器"""
        print("="*80)
        print("扫雪策略SUMO评估器".center(80))
        print("="*80)
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 配置参数
        self.use_scaled = self.config['sumo_config']['use_scaled']
        if self.use_scaled:
            self.sumo_config = self.config['sumo_config']['config_file_scaled']
            print(f"\n使用配置: 缩减版(10%)")
        else:
            self.sumo_config = self.config['sumo_config']['config_file']
            print(f"\n使用配置: 完整版")
        
        self.simulation_steps = self.config['sumo_config']['simulation_steps']
        self.evaluation_hours = self.config['sumo_config']['evaluation_hours']
        
        # 道路参数
        self.cleaned_params = self.config['road_parameters']['cleaned']
        self.unclean_params = self.config['road_parameters']['unclean']
        
        # 记录文件
        records_file = Path(self.config['output']['base_dir']) / self.config['output']['strategy_record']
        self.strategy_records = self.load_time_step_records(records_file)
        
        print(f"配置文件: {self.sumo_config}")
        print(f"仿真步数: {self.simulation_steps}")
        print(f"评估时间点: {self.evaluation_hours}")
    
    def load_time_step_records(self, json_path):
        """加载时间步清扫记录"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_cleaned_edges_at_time(self, time_minutes):
        """
        获取指定时间（分钟）已清扫的道路集合
        找到小于等于该时间的最近时间步
        """
        time_steps = []
        for key, value in self.strategy_records.items():
            time_steps.append((value['time_minutes'], key))
        
        time_steps.sort()
        
        # 找到小于等于目标时间的最大时间步
        target_key = None
        for t_min, key in time_steps:
            if t_min <= time_minutes:
                target_key = key
            else:
                break
        
        if target_key is None:
            return set()
        
        return set(self.strategy_records[target_key]['total_cleaned_edges'])
    
    def run_evaluation(self):
        """运行SUMO评估"""
        print("\n开始SUMO评估...")
        print("-"*80)
        
        results = {}
        
        for hour in self.evaluation_hours:
            print(f"\n{'='*60}")
            print(f"评估第 {hour} 小时的场景...")
            print(f"{'='*60}")
            
            # 获取该时间点已清扫的道路
            time_minutes = hour * 60
            cleaned_edges = self.get_cleaned_edges_at_time(time_minutes)
            print(f"已清扫道路数量: {len(cleaned_edges)}")
            
            # 启动SUMO
            traci.start(["sumo", "-c", self.sumo_config, "--start",
                        "--no-warnings", "true"])
            
            # 运行仿真
            for step in range(self.simulation_steps):
                traci.simulationStep()
                
                current_vehicles = traci.vehicle.getIDList()
                
                # 为每辆车设置参数
                for veh_id in current_vehicles:
                    current_edge = traci.vehicle.getRoadID(veh_id)
                    
                    # 根据道路是否已清扫设置参数
                    if current_edge in cleaned_edges:
                        params = self.cleaned_params
                    else:
                        params = self.unclean_params
                    
                    traci.vehicle.setAcceleration(veh_id, params["accel"], 1)
                    traci.vehicle.setDecel(veh_id, params["decel"])
                    traci.vehicle.setMaxSpeed(veh_id, params["max_speed"])
                    traci.vehicle.setMinGap(veh_id, params["min_gap"])
                
                # 每50步打印进度
                if (step + 1) % 50 == 0:
                    print(f"  仿真进度: {step + 1}/{self.simulation_steps} 步, "
                          f"当前车辆数: {len(current_vehicles)}")
            
            # 统计最终结果
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
            
            # 关闭SUMO
            traci.close()
            
            # 保存结果
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
    
    def save_results(self, results):
        """保存评估结果"""
        output_dir = Path(self.config['output']['base_dir'])
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / self.config['output']['evaluation_results']
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n评估结果已保存至: {results_file}")
        return results_file
    
    def plot_results(self, results):
        """可视化评估结果"""
        hours = []
        speeds_ms = []
        speeds_kmh = []
        num_cleaned = []
        num_vehicles = []
        
        # 整理数据
        for key in sorted(results.keys()):
            hour_data = results[key]
            hours.append(hour_data['time_hours'])
            speeds_ms.append(hour_data['global_avg_speed_ms'])
            speeds_kmh.append(hour_data['global_avg_speed_kmh'])
            num_cleaned.append(hour_data['num_cleaned_edges'])
            num_vehicles.append(hour_data['num_vehicles'])
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 子图1：平均速度
        color1 = 'tab:blue'
        ax1.set_xlabel('时间（小时）', fontsize=14)
        ax1.set_ylabel('全局平均速度 (m/s)', fontsize=14, color=color1)
        line1 = ax1.plot(hours, speeds_ms, marker='o', linewidth=3, markersize=10,
                        color=color1, label='平均速度')
        ax1.tick_params(axis='y', labelcolor=color1)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # 右Y轴：km/h
        ax1_right = ax1.twinx()
        ax1_right.set_ylabel('全局平均速度 (km/h)', fontsize=14, color='tab:red')
        ax1_right.plot(hours, speeds_kmh, marker='s', linewidth=2, markersize=8,
                      color='tab:red', linestyle='--', alpha=0.6, label='速度(km/h)')
        ax1_right.tick_params(axis='y', labelcolor='tab:red')
        
        ax1.set_title('扫雪策略效果：全局平均速度随时间变化', fontsize=16, fontweight='bold', pad=20)
        ax1.legend(loc='upper left', fontsize=12)
        
        # 子图2：已清扫道路数量
        color2 = 'tab:green'
        ax2.set_xlabel('时间（小时）', fontsize=14)
        ax2.set_ylabel('已清扫道路数量', fontsize=14, color=color2)
        ax2.bar(hours, num_cleaned, color=color2, alpha=0.6, label='已清扫道路')
        ax2.tick_params(axis='y', labelcolor=color2)
        ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
        ax2.set_title('扫雪进度：已清扫道路数量', fontsize=16, fontweight='bold', pad=20)
        ax2.legend(loc='upper left', fontsize=12)
        
        # 保存图表
        plt.tight_layout()
        output_dir = Path(self.config['output']['base_dir'])
        plot_file = output_dir / 'evaluation_plots.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"图表已保存至: {plot_file}")
        plt.close()
    
    def run(self):
        """运行完整评估流程"""
        results = self.run_evaluation()
        self.save_results(results)
        self.plot_results(results)
        
        print("\n" + "="*80)
        print("评估完成！".center(80))
        print("="*80)
        
        return results


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='扫雪策略SUMO评估器')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    args = parser.parse_args()
    
    evaluator = SnowplowStrategyEvaluator(args.config)
    evaluator.run()


if __name__ == "__main__":
    main()
