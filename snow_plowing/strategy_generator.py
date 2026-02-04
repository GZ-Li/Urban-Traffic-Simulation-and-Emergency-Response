"""
扫雪策略生成器 - 基于traffic flow的贪心算法
参考strateg5.py，实现分区域扫雪路径规划
每个区域配备一辆扫雪车，基于交通流量选择最优清扫路径
"""

import xml.etree.ElementTree as ET
import json
import math
import heapq
import networkx as nx
from collections import defaultdict
from pathlib import Path


class SnowplowStrategyGenerator:
    """扫雪策略生成器"""
    
    def __init__(self, config_path='config.json'):
        """初始化生成器"""
        print("="*80)
        print("扫雪策略生成器初始化".center(80))
        print("="*80)
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.net_file = self.config['network']['net_file']
        self.regions_config = self.config['regions']
        self.snowplow_params = self.config['snowplow']
        self.traffic_file = self.config['traffic_data']['route_file']
        
        # 数据结构
        self.edges_info = {}
        self.region_edges = {region: [] for region in self.regions_config.keys()}
        self.traffic_flow = defaultdict(int)
        self.G = nx.DiGraph()
        self.node_positions = {}
        self.edge_data_dict = {}
        
        print(f"\n网络文件: {self.net_file}")
        print(f"交通数据: {self.traffic_file}")
        print(f"区域数量: {len(self.regions_config)}")
        print(f"扫雪车数: {self.snowplow_params['num_trucks']}")
    
    def point_in_rectangle(self, point, rect):
        """判断点是否在矩形区域内"""
        x, y = point
        return (rect.get("min_x", float('-inf')) <= x <= rect.get("max_x", float('inf')) and 
                rect.get("min_y", float('-inf')) <= y <= rect.get("max_y", float('inf')))
    
    def load_network(self):
        """加载路网并分配区域"""
        print("\n[1/5] 加载路网...")
        tree = ET.parse(self.net_file)
        root = tree.getroot()
        
        # 提取边信息并分配区域
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if edge_id.startswith(':'):
                continue
            
            # 获取形状坐标
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
        
        # 打印区域统计
        print("\n区域道路分配统计:")
        total_edges = 0
        for region_name, edges in self.region_edges.items():
            print(f"  {region_name}: {len(edges):4d} 条道路")
            total_edges += len(edges)
        print(f"  合计: {total_edges} 条道路")
    
    def load_traffic_data(self):
        """加载交通流量数据"""
        print("\n[2/5] 加载交通流量数据...")
        tree = ET.parse(self.traffic_file)
        root = tree.getroot()
        
        # 处理vehicle
        for vehicle in root.findall('vehicle'):
            route = vehicle.find('route')
            if route is not None and route.get('edges'):
                edges = route.get('edges').split()
                for edge in edges:
                    if not edge.startswith(':'):
                        self.traffic_flow[edge] += 1
        
        # 处理flow
        for flow in root.findall('flow'):
            route = flow.find('route')
            if route is not None and route.get('edges'):
                edges = route.get('edges').split()
                number = int(flow.get('number', 1))
                for edge in edges:
                    if not edge.startswith(':'):
                        self.traffic_flow[edge] += number
        
        print(f"  已加载 {len(self.traffic_flow)} 条道路的流量数据")
        total_flow = sum(self.traffic_flow.values())
        print(f"  总流量: {total_flow} vehicles")
    
    def build_graph(self):
        """构建网络图"""
        print("\n[3/5] 构建网络图...")
        tree = ET.parse(self.net_file)
        root = tree.getroot()
        
        # 添加所有节点
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
        
        # 添加所有边
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
        
        # 提取节点位置
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
        
        print(f"  节点数: {len(self.G.nodes())}")
        print(f"  边数: {len(self.G.edges())}")
        print(f"  节点位置数: {len(self.node_positions)}")
    
    def prepare_edge_data(self):
        """准备边数据字典"""
        print("\n[4/5] 准备边数据...")
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
        
        # 分配区域信息
        for region, edges in self.region_edges.items():
            for eid in edges:
                if eid in self.edge_data_dict:
                    self.edge_data_dict[eid]["region"] = region
        
        print(f"  边数据字典: {len(self.edge_data_dict)} 条边")
    
    def generate_greedy_strategy(self):
        """生成基于交通流量的贪心扫雪策略"""
        print("\n[5/5] 生成扫雪策略...")
        print("-"*80)
        
        # 初始化每辆车的状态
        car_states = {}
        for region, config in self.regions_config.items():
            start_edge = config['start_edge']
            if start_edge not in self.edge_data_dict:
                print(f"Warning: 起始边 {start_edge} 不在路网中，跳过 {region}")
                continue
            
            car_states[region] = {
                "current_node": self.edge_data_dict[start_edge]["from"],
                "cleaned_edges": set(),
                "cleaning_paths": [],
                "cleaned_length": 0,
                "penalty": 0
            }
        
        consecutive_no_path_dict = {region: 0 for region in self.region_edges.keys()}
        
        # 对每个区域生成路径
        for region in self.region_edges.keys():
            if region not in car_states:
                continue
            
            print(f"\n处理 {region}...")
            cleaned_edges = set()
            state = car_states[region]
            
            # 构建子图
            sub_G = nx.DiGraph()
            for u, v, d in self.G.edges(data=True):
                if d["id"] in self.region_edges[region]:
                    sub_G.add_edge(u, v, **d)
            
            iteration = 0
            max_iterations = 10000
            
            while iteration < max_iterations:
                iteration += 1
                current_node = state["current_node"]
                
                # 查找当前节点的后继边
                uncleaned_successors = []
                for u, v, d in sub_G.out_edges(current_node, data=True):
                    if d["id"] not in cleaned_edges:
                        uncleaned_successors.append((u, v, d))
                
                if len(uncleaned_successors) > 0:
                    # 有未清扫的后继边，选择流量最大的
                    uncleaned_successors.sort(key=lambda x: self.traffic_flow[x[2]["id"]], reverse=True)
                    this_step_start_node, next_node, chosen_edge = uncleaned_successors[0]
                    
                    # 根据车道数决定下一个节点位置
                    if chosen_edge['lane_count'] % 2 == 0:
                        this_step_next_node = this_step_start_node
                    else:
                        this_step_next_node = next_node
                    
                    # 更新状态
                    cleaned_edges.add(chosen_edge["id"])
                    state["cleaned_edges"].add(chosen_edge["id"])
                    state["cleaned_length"] += self.edge_data_dict[chosen_edge["id"]]["length"]
                    state["cleaning_paths"].extend([chosen_edge["id"]] * chosen_edge["lane_count"])
                    state["current_node"] = this_step_next_node
                    consecutive_no_path_dict[region] = 0
                
                else:
                    # 没有未清扫的后继边，需要寻找最近的未清扫边
                    candidates = [eid for eid in self.region_edges[region] 
                                if eid in self.edge_data_dict and eid not in cleaned_edges]
                    
                    if len(candidates) == 0:
                        break
                    
                    # 找到候选节点
                    candidate_nodes = []
                    for eid in candidates:
                        ed = self.edge_data_dict[eid]
                        if ed["from"] != current_node:
                            candidate_nodes.append(ed["from"])
                    candidate_nodes = list(set(candidate_nodes))
                    
                    if not candidate_nodes:
                        break
                    
                    # 按距离排序
                    def node_min_dist(nid):
                        if nid in self.node_positions and current_node in self.node_positions:
                            return math.hypot(
                                self.node_positions[current_node][0] - self.node_positions[nid][0],
                                self.node_positions[current_node][1] - self.node_positions[nid][1]
                            )
                        return float("inf")
                    
                    candidate_node_list = heapq.nsmallest(min(5, len(candidate_nodes)), 
                                                         candidate_nodes, key=node_min_dist)
                    
                    # 尝试找到路径
                    path_found = False
                    for nid in candidate_node_list:
                        try:
                            path_nodes = nx.shortest_path(sub_G, source=current_node, 
                                                         target=nid, weight='length')
                            path_found = True
                            
                            # 沿路径清扫
                            for j in range(len(path_nodes) - 1):
                                u, v = path_nodes[j], path_nodes[j + 1]
                                eid = sub_G[u][v]["id"]
                                if eid not in cleaned_edges:
                                    cleaned_edges.add(eid)
                                    state["cleaned_edges"].add(eid)
                                    state["cleaned_length"] += self.edge_data_dict[eid]["length"]
                                    state["cleaning_paths"].extend([eid] * self.edge_data_dict[eid]["lane_count"])
                                    
                                    if self.edge_data_dict[eid]["lane_count"] % 2 == 0:
                                        this_step_next_node = u
                                    else:
                                        this_step_next_node = v
                                    state["current_node"] = this_step_next_node
                            
                            state["current_node"] = nid
                            consecutive_no_path_dict[region] = 0
                            break
                        except:
                            continue
                    
                    if not path_found:
                        consecutive_no_path_dict[region] += 1
                        if consecutive_no_path_dict[region] >= 10:
                            # 传送到其他未清扫边
                            remaining = [eid for eid in candidates if eid in self.edge_data_dict]
                            if len(remaining) > 0:
                                remaining.sort(key=lambda x: self.traffic_flow.get(x, 0), reverse=True)
                                next_edge_id = remaining[0]
                                state["current_node"] = self.edge_data_dict[next_edge_id]["from"]
                                state["penalty"] += self.config['strategy']['parameters']['penalty_time_minutes']
                                consecutive_no_path_dict[region] = 0
                                print(f"  传送到新区域 (剩余{len(remaining)}条)")
                            else:
                                break
                        else:
                            if candidate_node_list:
                                state["current_node"] = candidate_node_list[0]
            
            print(f"  完成: 清扫 {len(cleaned_edges)}/{len(self.region_edges[region])} 条道路")
        
        return car_states
    
    def calculate_time_records(self, car_states):
        """计算时间步记录"""
        print("\n生成时间步记录...")
        
        time_step_records = {}
        interval_minutes = self.config['output']['time_step_interval_minutes']
        max_hours = max(self.config['sumo_config']['evaluation_hours'])
        time_points = list(range(0, (max_hours + 1) * 60, interval_minutes))
        
        cleaning_rate = self.snowplow_params['cleaning_rate_per_lane']  # 每车道清扫时间
        
        for idx, time_minutes in enumerate(time_points):
            total_cleaned_edges = set()
            regions_info = {}
            
            for region, state in car_states.items():
                paths = state["cleaning_paths"]
                penalty_time = state.get("penalty", 0)
                
                # 计算到当前时间清扫了多少边
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
    
    def save_results(self, car_states, time_step_records):
        """保存结果"""
        print("\n保存结果...")
        
        # 创建输出目录
        output_dir = Path(self.config['output']['base_dir'])
        output_dir.mkdir(exist_ok=True)
        
        # 保存时间步记录
        records_file = output_dir / self.config['output']['strategy_record']
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(time_step_records, f, indent=2, ensure_ascii=False)
        print(f"  时间步记录: {records_file}")
        
        # 保存策略详情
        strategy_details = {
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
        
        details_file = output_dir / "strategy_details.json"
        with open(details_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_details, f, indent=2, ensure_ascii=False)
        print(f"  策略详情: {details_file}")
        
        print("\n" + "="*80)
        print("策略生成完成！".center(80))
        print("="*80)
    
    def run(self):
        """运行完整流程"""
        self.load_network()
        self.load_traffic_data()
        self.build_graph()
        self.prepare_edge_data()
        car_states = self.generate_greedy_strategy()
        time_step_records = self.calculate_time_records(car_states)
        self.save_results(car_states, time_step_records)
        return car_states, time_step_records


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='扫雪策略生成器')
    parser.add_argument('-c', '--config', default='config.json',
                       help='配置文件路径 (默认: config.json)')
    args = parser.parse_args()
    
    generator = SnowplowStrategyGenerator(args.config)
    generator.run()


if __name__ == "__main__":
    main()
