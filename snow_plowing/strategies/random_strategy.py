"""
随机策略
随机选择道路进行清扫，用于对比实验

策略描述：
1. 全局分治：将路网划分为5个区域，每个区域分配一辆扫雪车
2. 随机选择：每辆车在其区域内随机选择未清扫道路
3. 路径规划：使用Dijkstra算法寻找最短路径
"""

import math
import random
import heapq
import networkx as nx
from collections import defaultdict


class RandomStrategy:
    """随机扫雪策略"""
    
    def __init__(self, network_data, regions_config, traffic_flow):
        """
        初始化策略
        
        Args:
            network_data: 路网数据字典
            regions_config: 区域配置
            traffic_flow: 交通流量字典（随机策略不使用，保持接口一致）
        """
        self.network_data = network_data
        self.regions_config = regions_config
        self.traffic_flow = traffic_flow  # 保留但不使用
        
        self.G = network_data['graph']
        self.node_positions = network_data['node_positions']
        self.edge_data_dict = network_data['edge_data_dict']
        self.region_edges = network_data['region_edges']
    
    def generate(self, penalty_minutes=5, max_no_path_retries=10, random_seed=None):
        """
        生成随机扫雪策略
        
        Args:
            penalty_minutes: 传送惩罚时间（分钟）
            max_no_path_retries: 最大连续找不到路径次数
            random_seed: 随机种子（用于重现结果）
        
        Returns:
            car_states: 每辆车的状态字典
        """
        if random_seed is not None:
            random.seed(random_seed)
        
        print(f"\n策略: 随机策略")
        print(f"  参数: 传送惩罚={penalty_minutes}分钟, 随机种子={random_seed}")
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
            
            print(f"\n处理 {region} ({self.regions_config[region].get('name', region)})...")
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
                    # 有未清扫的后继边，随机选择一个
                    chosen = random.choice(uncleaned_successors)
                    this_step_start_node, next_node, chosen_edge = chosen
                    
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
                    # 没有未清扫的后继边，随机选择一个未清扫边
                    candidates = [eid for eid in self.region_edges[region] 
                                if eid in self.edge_data_dict and eid not in cleaned_edges]
                    
                    if len(candidates) == 0:
                        break
                    
                    # 随机选择一个候选边
                    random.shuffle(candidates)
                    
                    # 找到候选节点
                    candidate_nodes = []
                    for eid in candidates[:min(10, len(candidates))]:  # 只考虑前10个
                        ed = self.edge_data_dict[eid]
                        if ed["from"] != current_node:
                            candidate_nodes.append(ed["from"])
                    candidate_nodes = list(set(candidate_nodes))
                    
                    if not candidate_nodes:
                        break
                    
                    # 按距离排序（仍需找最短路径）
                    def node_min_dist(nid):
                        if nid in self.node_positions and current_node in self.node_positions:
                            return math.hypot(
                                self.node_positions[current_node][0] - self.node_positions[nid][0],
                                self.node_positions[current_node][1] - self.node_positions[nid][1]
                            )
                        return float("inf")
                    
                    candidate_node_list = heapq.nsmallest(
                        min(5, len(candidate_nodes)), 
                        candidate_nodes, 
                        key=node_min_dist
                    )
                    
                    # 尝试找到路径
                    path_found = False
                    for nid in candidate_node_list:
                        try:
                            path_nodes = nx.shortest_path(
                                sub_G, source=current_node, 
                                target=nid, weight='length'
                            )
                            path_found = True
                            
                            # 沿路径清扫
                            for j in range(len(path_nodes) - 1):
                                u, v = path_nodes[j], path_nodes[j + 1]
                                eid = sub_G[u][v]["id"]
                                if eid not in cleaned_edges:
                                    cleaned_edges.add(eid)
                                    state["cleaned_edges"].add(eid)
                                    state["cleaned_length"] += self.edge_data_dict[eid]["length"]
                                    state["cleaning_paths"].extend(
                                        [eid] * self.edge_data_dict[eid]["lane_count"]
                                    )
                                    
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
                        if consecutive_no_path_dict[region] >= max_no_path_retries:
                            # 传送到随机未清扫边
                            remaining = [eid for eid in candidates if eid in self.edge_data_dict]
                            if len(remaining) > 0:
                                next_edge_id = random.choice(remaining)
                                state["current_node"] = self.edge_data_dict[next_edge_id]["from"]
                                state["penalty"] += penalty_minutes
                                consecutive_no_path_dict[region] = 0
                                print(f"  传送到新区域 (剩余{len(remaining)}条)")
                            else:
                                break
                        else:
                            if candidate_node_list:
                                state["current_node"] = candidate_node_list[0]
            
            coverage = len(cleaned_edges) / len(self.region_edges[region]) * 100 if self.region_edges[region] else 0
            print(f"  完成: 清扫 {len(cleaned_edges)}/{len(self.region_edges[region])} 条道路 ({coverage:.1f}%)")
        
        return car_states
    
    def get_name(self):
        """返回策略名称"""
        return "random"
    
    def get_description(self):
        """返回策略描述"""
        return "随机策略（对比基准）"
