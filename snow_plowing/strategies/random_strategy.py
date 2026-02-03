"""
随机策略生成器
按地理区域随机选择清扫道路
"""
import json
import random
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict
import networkx as nx


class RandomStrategy:
    def __init__(self, config):
        self.config = config
        self.net_file = config['network']['net_file']
        self.route_file = config['network']['route_file']
        self.num_trucks = config['snowplow_parameters']['num_trucks']
        self.speed_clean = config['snowplow_parameters']['speed_clean']
        self.speed_pass = config['snowplow_parameters']['speed_pass']
        self.max_time_minutes = config['snowplow_parameters']['max_time_minutes']
        self.unified_start = config['snowplow_parameters']['unified_start_edge']
        
        # 从外部文件加载区域配置
        regions_file = Path(__file__).parent.parent / config['snowplow_parameters']['regions_file']
        with open(regions_file, 'r', encoding='utf-8') as f:
            regions_data = json.load(f)
        self.regions = regions_data['regions']
        
        # 初始化
        self.graph = None
        self.edge_data = {}
        
    def load_network(self):
        """加载SUMO路网"""
        print(f"    加载路网: {self.net_file}")
        tree = ET.parse(self.net_file)
        root = tree.getroot()
        
        self.graph = nx.DiGraph()
        
        for edge in root.findall('edge'):
            edge_id = edge.get('id')
            if ':' in edge_id:
                continue
                
            from_node = edge.get('from')
            to_node = edge.get('to')
            
            lanes = edge.findall('lane')
            lane_count = len(lanes)
            
            if lane_count > 0:
                length = float(lanes[0].get('length', 0))
                shape = lanes[0].get('shape', '')
                
                self.edge_data[edge_id] = {
                    'from': from_node,
                    'to': to_node,
                    'length': length,
                    'lane_count': lane_count,
                    'shape': shape
                }
                
                self.graph.add_edge(from_node, to_node, 
                                  edge_id=edge_id, 
                                  length=length,
                                  lane_count=lane_count)
        
        print(f"    路网加载完成: {len(self.edge_data)} 条道路")
    
    def assign_region_by_location(self, x, y):
        """根据地理位置分配区域"""
        for region in self.regions:
            bounds = region['bounds']
            if (bounds['x_min'] <= x < bounds['x_max'] and 
                bounds['y_min'] <= y < bounds['y_max']):
                return region['id']
        return 'region1'  # 默认
    
    def get_edge_center(self, edge_id):
        """获取道路中心点坐标"""
        shape_str = self.edge_data[edge_id]['shape']
        points = shape_str.split()
        
        if len(points) == 0:
            return (0, 0)
        
        mid_point = points[len(points)//2]
        x, y = map(float, mid_point.split(','))
        return (x, y)
    
    def generate(self):
        """生成随机策略"""
        print("    [随机策略] 开始生成...")
        
        # 加载数据
        self.load_network()
        
        # 设置随机种子（可从配置中读取）
        seed = self.config['strategies']['random'].get('seed', 42)
        random.seed(seed)
        
        # 初始化每个扫雪车的状态
        truck_states = {}
        for i in range(1, self.num_trucks + 1):
            region_id = f'region{i}'
            truck_states[region_id] = {
                'truck_id': region_id,
                'current_edge': None,
                'current_node': self.unified_start,
                'time_elapsed': 0.0,
                'cleaned_roads': [],
                'path_records': []
            }
        
        # 未清扫道路集合（按区域）
        uncleaned_by_region = {f'region{i}': [] for i in range(1, self.num_trucks+1)}
        for edge_id in self.edge_data:
            x, y = self.get_edge_center(edge_id)
            region = self.assign_region_by_location(x, y)
            if region in uncleaned_by_region:
                uncleaned_by_region[region].append(edge_id)
        
        # 打乱每个区域的道路顺序
        for region in uncleaned_by_region:
            random.shuffle(uncleaned_by_region[region])
        
        # 随机主循环
        max_time_seconds = self.max_time_minutes * 60
        consecutive_no_path = {region: 0 for region in truck_states}
        
        while any(state['time_elapsed'] < max_time_seconds for state in truck_states.values()):
            for region, state in truck_states.items():
                if state['time_elapsed'] >= max_time_seconds:
                    continue
                
                # 从当前区域随机选择一条未清扫道路
                if not uncleaned_by_region[region]:
                    break
                
                target_edge_id = uncleaned_by_region[region][0]
                
                # 计算路径
                target_edge = self.edge_data[target_edge_id]
                target_start = target_edge['from']
                
                try:
                    if state['current_node'] == target_start:
                        path = []
                    else:
                        path = nx.shortest_path(self.graph, 
                                              state['current_node'], 
                                              target_start, 
                                              weight='length')
                    
                    # 经过路径（不清扫）
                    travel_time = 0
                    if len(path) > 1:
                        for i in range(len(path)-1):
                            u, v = path[i], path[i+1]
                            edge_data = self.graph[u][v]
                            travel_time += edge_data['length'] / self.speed_pass
                    
                    # 清扫目标道路
                    clean_time = target_edge['length'] / self.speed_clean
                    
                    # 判断终点
                    if target_edge['lane_count'] % 2 == 0:
                        end_node = target_edge['from']  # 需要U-turn
                    else:
                        end_node = target_edge['to']
                    
                    # 更新状态
                    state['time_elapsed'] += (travel_time + clean_time)
                    state['current_node'] = end_node
                    state['cleaned_roads'].append(target_edge_id)
                    state['path_records'].append({
                        'edge_id': target_edge_id,
                        'start_time': state['time_elapsed'] - clean_time,
                        'end_time': state['time_elapsed'],
                        'travel_time': travel_time,
                        'clean_time': clean_time
                    })
                    
                    uncleaned_by_region[region].pop(0)
                    consecutive_no_path[region] = 0
                    
                except nx.NetworkXNoPath:
                    # 路径不可达，尝试teleport
                    consecutive_no_path[region] += 1
                    if consecutive_no_path[region] >= 10:
                        # 传送到下一个未清扫道路的起点
                        if uncleaned_by_region[region]:
                            uncleaned_by_region[region].pop(0)
                            if uncleaned_by_region[region]:
                                next_edge = uncleaned_by_region[region][0]
                                state['current_node'] = self.edge_data[next_edge]['from']
                            consecutive_no_path[region] = 0
                            print(f"    {region} teleport (skip unreachable)")
        
        # 构建输出结果
        result = {
            'strategy_name': 'random',
            'description': '随机策略：按地理区域随机选择清扫道路',
            'config': {
                'num_trucks': self.num_trucks,
                'max_time_minutes': self.max_time_minutes,
                'speed_clean': self.speed_clean,
                'speed_pass': self.speed_pass,
                'unified_start_edge': self.unified_start,
                'random_seed': seed
            },
            'regions': [r['id'] for r in self.regions],
            'trucks': []
        }
        
        total_cleaned = 0
        for region, state in truck_states.items():
            total_cleaned += len(state['cleaned_roads'])
            result['trucks'].append({
                'truck_id': state['truck_id'],
                'region': region,
                'time_used_minutes': state['time_elapsed'] / 60,
                'roads_cleaned': len(state['cleaned_roads']),
                'cleaning_records': state['path_records']
            })
        
        result['summary'] = {
            'total_roads_cleaned': total_cleaned,
            'total_time_minutes': max(s['time_elapsed'] for s in truck_states.values()) / 60,
            'roads_by_region': {r: len(truck_states[r]['cleaned_roads']) 
                               for r in truck_states}
        }
        
        print(f"    [随机策略] 完成: 共清扫 {total_cleaned} 条道路")
        return result
    
    def save_result(self, output_path):
        """保存结果"""
        pass
