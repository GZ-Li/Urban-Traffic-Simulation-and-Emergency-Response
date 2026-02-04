"""
扫雪策略生成器
统一的策略生成接口，支持多种策略
"""

import xml.etree.ElementTree as ET
import json
import math
import networkx as nx
from pathlib import Path
from collections import defaultdict
from strategies import get_strategy


class StrategyGenerator:
    """统一的策略生成器"""
    
    def __init__(self, config_path='config.json'):
        """初始化生成器"""
        print("="*80)
        print("扫雪策略生成器".center(80))
        print("="*80)
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 加载区域配置
        regions_file = self.config['network'].get('regions_file', 'regions.json')
        with open(regions_file, 'r', encoding='utf-8') as f:
            regions_data = json.load(f)
            self.regions_config = regions_data['regions']
        
        self.net_file = self.config['network']['net_file']
        self.traffic_file = self.config['traffic_data']['route_file']
        
        # 数据结构
        self.edges_info = {}
        self.region_edges = {region: [] for region in self.regions_config.keys()}
        self.traffic_flow = defaultdict(int)
        self.G = nx.DiGraph()
        self.node_positions = {}
        self.edge_data_dict = {}
        
        print(f"\n网络文件: {self.net_file}")
        print(f"区域配置: {regions_file}")
        print(f"交通数据: {self.traffic_file}")
    
    def point_in_rectangle(self, point, rect):
        """判断点是否在矩形区域内"""
        x, y = point
        return (rect.get("min_x", float('-inf')) <= x <= rect.get("max_x", float('inf')) and 
                rect.get("min_y", float('-inf')) <= y <= rect.get("max_y", float('inf')))
    
    def load_network(self):
        """加载路网并分配区域"""
        print("\n[1/4] 加载路网...")
        tree = ET.parse(self.net_file)
        root = tree.getroot()
        
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'):
                continue
            
            shape_attr = edge.get('shape')
            if shape_attr is None:
                lanes = edge.findall('lane')
                if lanes:
                    shape_attr = lanes[0].get('shape')
            
            if shape_attr:
                coords = [tuple(map(float, point.split(','))) for point in shape_attr.split()]
                center_x = sum(coord[0] for coord in coords) / len(coords)
                center_y = sum(coord[1] for coord in coords) / len(coords)
                center_point = (center_x, center_y)
                
                self.edges_info[edge_id] = {
                    'coords': coords,
                    'center': center_point,
                    'region': None
                }
                
                # 分配区域
                assigned = False
                for region_name, rect in self.regions_config.items():
                    if region_name == 'region5':
                        continue
                    if self.point_in_rectangle(center_point, rect):
                        self.region_edges[region_name].append(edge_id)
                        self.edges_info[edge_id]['region'] = region_name
                        assigned = True
                        break
                
                if not assigned:
                    self.region_edges["region5"].append(edge_id)
                    self.edges_info[edge_id]['region'] = "region5"
        
        print("  区域道路分配统计:")
        total_edges = 0
        for region_name, edges in self.region_edges.items():
            print(f"    {region_name}: {len(edges):4d} 条道路")
            total_edges += len(edges)
        print(f"    合计: {total_edges} 条道路")
    
    def load_traffic_data(self):
        """加载交通流量数据"""
        print("\n[2/4] 加载交通流量数据...")
        tree = ET.parse(self.traffic_file)
        root = tree.getroot()
        
        for vehicle in root.findall('vehicle'):
            route = vehicle.find('route')
            if route is not None and route.get('edges'):
                edges = route.get('edges').split()
                for edge in edges:
                    if not edge.startswith(':'):
                        self.traffic_flow[edge] += 1
        
        for flow in root.findall('flow'):
            route = flow.find('route')
            if route is not None and route.get('edges'):
                edges = route.get('edges').split()
                number = int(flow.get('number', 1))
                for edge in edges:
                    if not edge.startswith(':'):
                        self.traffic_flow[edge] += number
        
        print(f"    已加载 {len(self.traffic_flow)} 条道路的流量数据")
        total_flow = sum(self.traffic_flow.values())
        print(f"    总流量: {total_flow} vehicles")
    
    def build_graph(self):
        """构建网络图"""
        print("\n[3/4] 构建网络图...")
        tree = ET.parse(self.net_file)
        root = tree.getroot()
        
        all_nodes = set()
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'):
                continue
            from_node = edge.get('from')
            to_node = edge.get('to')
            if from_node:
                all_nodes.add(from_node)
            if to_node:
                all_nodes.add(to_node)
        
        for node in all_nodes:
            self.G.add_node(node)
        
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'):
                continue
            from_node = edge.get('from')
            to_node = edge.get('to')
            
            if from_node and to_node:
                lanes = edge.findall('lane')
                edge_length = float(lanes[0].get('length')) if lanes else 0
                lane_count = len(lanes) if lanes else 1
                
                self.G.add_edge(from_node, to_node,
                              id=edge_id,
                              length=edge_length,
                              lane_count=lane_count,
                              total_length=edge_length * lane_count)
        
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'):
                continue
            lanes = edge.findall('lane')
            if lanes:
                shape_attr = lanes[0].get('shape')
                if shape_attr:
                    coords = [tuple(map(float, p.split(','))) for p in shape_attr.split()]
                    if len(coords) >= 2:
                        from_node = edge.get("from")
                        to_node = edge.get("to")
                        if from_node in self.G.nodes and from_node not in self.node_positions:
                            self.node_positions[from_node] = coords[0]
                        if to_node in self.G.nodes and to_node not in self.node_positions:
                            self.node_positions[to_node] = coords[-1]
        
        print(f"    节点数: {len(self.G.nodes())}")
        print(f"    边数: {len(self.G.edges())}")
    
    def prepare_network_data(self):
        """准备网络数据"""
        for u, v, d in self.G.edges(data=True):
            eid = d["id"]
            self.edge_data_dict[eid] = {
                "from": u,
                "to": v,
                "single_length": float(d["length"]),
                "lane_count": d["lane_count"],
                "length": float(d["length"]) * d["lane_count"],
                "flow": self.traffic_flow.get(eid, 0),
                "region": None
            }
        
        for region, edges in self.region_edges.items():
            for eid in edges:
                if eid in self.edge_data_dict:
                    self.edge_data_dict[eid]["region"] = region
    
    def generate_strategy(self, strategy_name='greedy', **kwargs):
        """
        生成指定策略
        
        Args:
            strategy_name: 策略名称 ('greedy' 或 'random')
            **kwargs: 策略特定参数
        
        Returns:
            car_states: 每辆车的状态字典
        """
        print(f"\n[4/4] 生成策略...")
        print("-"*80)
        
        # 准备网络数据
        network_data = {
            'graph': self.G,
            'node_positions': self.node_positions,
            'edge_data_dict': self.edge_data_dict,
            'region_edges': self.region_edges
        }
        
        # 获取策略类并实例化
        StrategyClass = get_strategy(strategy_name)
        strategy = StrategyClass(network_data, self.regions_config, self.traffic_flow)
        
        # 生成策略
        car_states = strategy.generate(**kwargs)
        
        return car_states, strategy
    
    def calculate_time_records(self, car_states):
        """计算时间步记录"""
        print("\n生成时间步记录...")
        
        time_step_records = {}
        interval_minutes = self.config['output']['time_step_interval_minutes']
        max_hours = max(self.config['sumo_config']['evaluation_hours'])
        time_points = list(range(0, (max_hours + 1) * 60, interval_minutes))
        
        cleaning_rate = self.config['snowplow']['cleaning_rate_per_lane']
        
        for idx, time_minutes in enumerate(time_points):
            total_cleaned_edges = set()
            regions_info = {}
            
            for region, state in car_states.items():
                paths = state["cleaning_paths"]
                penalty_time = state.get("penalty", 0)
                
                available_time = time_minutes - penalty_time
                if available_time < 0:
                    available_time = 0
                
                lanes_cleaned = int(available_time / cleaning_rate)
                cleaned_count = 0
                cleaned_edges_list = []
                
                for eid in paths[:lanes_cleaned]:
                    if eid not in cleaned_edges_list:
                        cleaned_edges_list.append(eid)
                        total_cleaned_edges.add(eid)
                        cleaned_count += 1
                
                regions_info[region] = {
                    "cleaned_edges": cleaned_edges_list,
                    "num_cleaned": cleaned_count
                }
            
            time_step_records[f"step_{idx}_time_{time_minutes}min"] = {
                "time_seconds": time_minutes * 60,
                "time_minutes": float(time_minutes),
                "total_cleaned_edges": list(total_cleaned_edges),
                "regions": regions_info,
                "num_total_cleaned": len(total_cleaned_edges)
            }
        
        print(f"  生成 {len(time_step_records)} 个时间步记录")
        return time_step_records
    
    def save_results(self, strategy, car_states, time_step_records):
        """保存结果"""
        print("\n保存结果...")
        
        output_dir = Path(self.config['output']['base_dir'])
        output_dir.mkdir(exist_ok=True)
        
        strategy_name = strategy.get_name()
        
        # 保存时间步记录
        records_file = output_dir / f"snowplow_{strategy_name}_time_steps_record.json"
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(time_step_records, f, indent=2, ensure_ascii=False)
        print(f"  时间步记录: {records_file}")
        
        # 保存策略详情
        strategy_details = {
            "strategy_name": strategy_name,
            "strategy_description": strategy.get_description(),
            "config": self.config['strategy'],
            "regions": {}
        }
        
        for region, state in car_states.items():
            strategy_details["regions"][region] = {
                "total_edges": len(self.region_edges[region]),
                "cleaned_edges": len(state["cleaned_edges"]),
                "cleaning_path_length": len(state["cleaning_paths"]),
                "total_length_cleaned": state["cleaned_length"],
                "penalty_minutes": state.get("penalty", 0)
            }
        
        details_file = output_dir / f"strategy_{strategy_name}_details.json"
        with open(details_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_details, f, indent=2, ensure_ascii=False)
        print(f"  策略详情: {details_file}")
        
        print("\n" + "="*80)
        print(f"{strategy.get_description()} 生成完成！".center(80))
        print("="*80)
    
    def run(self, strategy_name='greedy', **kwargs):
        """运行完整流程"""
        self.load_network()
        self.load_traffic_data()
        self.build_graph()
        self.prepare_network_data()
        car_states, strategy = self.generate_strategy(strategy_name, **kwargs)
        time_step_records = self.calculate_time_records(car_states)
        self.save_results(strategy, car_states, time_step_records)
        return car_states, time_step_records


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='扫雪策略生成器')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    parser.add_argument('-s', '--strategy', default='greedy',
                       choices=['greedy', 'random'],
                       help='策略名称 (默认: greedy)')
    parser.add_argument('--seed', type=int, default=None,
                       help='随机种子（仅用于random策略）')
    args = parser.parse_args()
    
    generator = StrategyGenerator(args.config)
    
    # 根据策略传递不同参数
    kwargs = {}
    if args.strategy == 'random' and args.seed is not None:
        kwargs['random_seed'] = args.seed
    
    generator.run(strategy_name=args.strategy, **kwargs)


if __name__ == "__main__":
    main()
