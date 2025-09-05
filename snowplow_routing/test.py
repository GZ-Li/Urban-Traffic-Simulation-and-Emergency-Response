import numpy as np
import xml.etree.ElementTree as ET
import sumolib
import traci
import random
import networkx as nx
from collections import defaultdict

class MCTSNode:
    def __init__(self, name, parent = None, used_edges = None):
        self.name = name
        self.parent = parent
        self.used_edges = used_edges if used_edges else set()
        self.children = []
        self.total_reward = 0
        self.visits = 0


def netxml_to_networkx(net_file):
    net = sumolib.net.readNet(net_file)
    G = nx.DiGraph()
    for edge in net.getEdges():
        from_node = edge.getFromNode().getID()
        to_node = edge.getToNode().getID()
        edge_id = edge.getID()
        length = edge.getLength()
        G.add_edge(
            from_node,
            to_node,
            length=length,
            edge_id=edge.getID(),  # 原始edge的ID
        )
    return G


def expand(node, G, goal, start_node = MCTSNode("J0")):
    if (node.name == goal.name) and (node.name != start_node.name):
        return None
    neighbors = []
    for to_node in G.neighbors(node.name):
        edge_data = G.get_edge_data(node.name, to_node)
        sumo_edge_id = edge_data["edge_id"]
        if sumo_edge_id not in node.used_edges:
            neighbors.append((to_node, sumo_edge_id))
    if neighbors:
        to_node, sumo_edge_id = neighbors[np.random.randint(len(neighbors))]
        new_used_edges = set(node.used_edges)
        new_used_edges.add(sumo_edge_id)
        new_node = MCTSNode(to_node, parent=node, used_edges=new_used_edges)
        node.children.append(new_node)
        return new_node
    return None


def simulate(G, path_nodes, max_depth = 15):
    sumo_edges = []
    for i in range(len(path_nodes) - 1):
        from_node, to_node = path_nodes[i], path_nodes[i+1]
        edge_data = G.get_edge_data(from_node, to_node)
        sumo_edges.append(edge_data["edge_id"])
    current_node = path_nodes[-1]
    for i in range(max_depth - len(path_nodes)):
        neighbors = list(G.neighbors(current_node))
        if not neighbors:
            break
        next_node = random.choice(neighbors)
        path_nodes.append(next_node)
        sumo_edges.append(G.get_edge_data(current_node, next_node)["edge_id"])
        if next_node == path_nodes[0]:
            break
        current_node = next_node
    return path_nodes, sumo_edges


def backpropagate(node, reward):
    while node is not None:
        node.visits += 1
        node.total_reward += reward
        node = node.parent
        

def run_mcts(G, start_node, goal_node, iterations=1):
    root = start_node
    for _ in range(iterations):
        node = root
        path_nodes = [node.name]
        path_edges = set()
        while True:
            if node.children:
                node = max(node.children,
                          key=lambda x: (x.total_reward / (x.visits + 1e-6)) + 
                          np.sqrt(2 * np.log(node.visits + 1) / (x.visits + 1e-6)))
                path_nodes.append(node.name)
                path_edges.update(node.used_edges)
            else:
                print(node.name)
                new_node = expand(node, G, goal_node, start_node)
                if new_node:
                    path_nodes.append(new_node.name)
                    path_edges.update(new_node.used_edges)
                    node = new_node
                break
        if path_nodes[-1] == goal_node:
            snowplow_route = path_edges
        else:
            snowplow_node, snowplow_route = simulate(G, path_nodes)
        print(snowplow_route)
        if len(snowplow_route) <= 5:
            break
        print("saving")
        new_vtype = ET.Element('vType', {
            'id': 'snowplow',
            'accel': '1.0',
            'decel': '2.0',
            'maxSpeed': '10',
            'minGap': '5'
        })
        new_vehicle = ET.Element('vehicle', {
            'id': 'snowplow_0',
            'depart': '0.00',
            'type': 'snowplow'
        })
        new_route = ET.SubElement(new_vehicle, 'route', {'edges': ' '.join(snowplow_route)})
        with open("rou\\toy.rou.xml", "r") as f:
            xml_text = f.read()
        xml_root = ET.fromstring(xml_text)
        xml_root.insert(0, new_vtype)
        xml_root.insert(1, new_vehicle)
        updated_routes = ET.tostring(xml_root, encoding='unicode', method='xml')
        with open("E:\\Traffic_Simulation\\snowplow_routing\\rou\\dynamic_toy.rou.xml", "w") as f:
            f.write(updated_routes)

        sumo_cmd = [
            "sumo",
            "-c", "toy.sumocfg",
        ]
        traci.start(sumo_cmd)
        
        
#         # --- Backpropagation ---
#         backpropagate(node, reward)
    
#     # 提取最优路径
#     best_path = []
#     node = root
#     while node.children:
#         node = max(node.children, key=lambda x: x.visits)
#         best_path.append(node.node_id)
#     return best_path


if __name__ == "__main__":
    net_file = "E:\\Traffic_Simulation\\snowplow_routing\\net\\toy.net.xml"
    G = netxml_to_networkx(net_file)
    # print(f"节点数: {len(G.nodes())}")
    # print(f"边数: {len(G.edges())}")
    # for u, v, data in G.edges(data=True):
    #     print(f"边 {u} -> {v}: 车道ID={data['edge_id']}, 长度={data['length']}m")
    # print(expand(MCTSNode("J0"), G, MCTSNode("J0")))
    # print(simulate(G, ["J0"]))
    run_mcts(G, MCTSNode("J0"), MCTSNode("J0"))
    
    
# import numpy as np
# import networkx as nx
# import sumolib
# import traci
# from collections import defaultdict

# # ------------------------------
# # 1. 从SUMO路网构建networkx图（带edge限制）
# # ------------------------------
# net = sumolib.net.readNet("your_network.net.xml")
# G = nx.DiGraph()

# # 添加所有edge，并记录SUMO的edge ID
# for edge in net.getEdges():
#     from_node = edge.getFromNode().getID()
#     to_node = edge.getToNode().getID()
#     G.add_edge(from_node, to_node, 
#                sumo_edge_id=edge.getID(),  # 存储SUMO的edge ID
#                length=edge.getLength())

# # ------------------------------
# # 2. MCTS节点定义（增加已访问edges记录）
# # ------------------------------
# class MCTSNode:
#     def __init__(self, node_id, parent=None, used_edges=None):
#         self.node_id = node_id       # 当前节点ID（路口）
#         self.parent = parent         # 父节点
#         self.children = []          # 子节点
#         self.total_reward = 0       # 累计奖励
#         self.visits = 0            # 访问次数
#         self.used_edges = used_edges if used_edges else set()  # 已用过的SUMO edge IDs

# # ------------------------------
# # 3. Expansion阶段（禁止重复edge）
# # ------------------------------
# def expand(node, G, goal):
#     if node.node_id == goal:
#         return None  # 已到达目标
    
#     # 获取当前节点的所有出边
#     neighbors = []
#     for to_node in G.neighbors(node.node_id):
#         edge_data = G.get_edge_data(node.node_id, to_node)
#         sumo_edge_id = edge_data["sumo_edge_id"]
#         if sumo_edge_id not in node.used_edges:  # 检查是否已走过该edge
#             neighbors.append((to_node, sumo_edge_id))
    
#     if neighbors:
#         # 随机选择一个未探索的邻居
#         to_node, sumo_edge_id = neighbors[np.random.randint(len(neighbors))]
#         # 更新已访问的edges（继承父节点的已访问edges并添加新edge）
#         new_used_edges = set(node.used_edges)
#         new_used_edges.add(sumo_edge_id)
#         # 创建新节点
#         new_node = MCTSNode(to_node, parent=node, used_edges=new_used_edges)
#         node.children.append(new_node)
#         return new_node
#     return None

# # ------------------------------
# # 4. Simulation阶段（SUMO仿真+路由注入）
# # ------------------------------
# def simulate_path(G, path_nodes, sumo_net, config_file):
#     # 将节点路径转换为SUMO edge路径
#     sumo_edges = []
#     for i in range(len(path_nodes) - 1):
#         from_node, to_node = path_nodes[i], path_nodes[i+1]
#         edge_data = G.get_edge_data(from_node, to_node)
#         sumo_edges.append(edge_data["sumo_edge_id"])
    
#     # 创建临时路由文件
#     with open("temp_route.rou.xml", "w") as f:
#         f.write(f"""<routes>
#             <route id="temp_route" edges="{' '.join(sumo_edges)}"/>
#             <vehicle id="temp_veh" route="temp_route" depart="0"/>
#         </routes>""")
    
#     # 启动SUMO仿真
#     traci.start(["sumo", "-c", config_file, "--additional-files", "temp_route.rou.xml"])
#     travel_time = 0
#     while traci.simulation.getMinExpectedNumber() > 0:
#         traci.simulationStep()
#         if "temp_veh" in traci.vehicle.getIDList():
#             travel_time += 1  # 每步1秒
#         else:
#             break  # 车辆已到达或消失
    
#     traci.close()
#     return travel_time

# # ------------------------------
# # 5. 反向更新Reward
# # ------------------------------
# def backpropagate(node, reward):
#     while node is not None:
#         node.visits += 1
#         node.total_reward += reward
#         node = node.parent

# # ------------------------------
# # 6. 完整MCTS流程（带重复edge限制）
# # ------------------------------
# def run_mcts(G, sumo_net, start, goal, config_file, iterations=50):
#     root = MCTSNode(start)
    
#     for _ in range(iterations):
#         node = root
#         path_nodes = [node.node_id]  # 记录节点路径
#         path_edges = set()           # 记录已用SUMO edges
        
#         # --- Selection + Expansion ---
#         while True:
#             if node.children:
#                 # UCB1选择子节点
#                 node = max(node.children,
#                           key=lambda x: (x.total_reward / (x.visits + 1e-6)) + 
#                           np.sqrt(2 * np.log(node.visits + 1) / (x.visits + 1e-6)))
#                 path_nodes.append(node.node_id)
#                 path_edges.update(node.used_edges)
#             else:
#                 new_node = expand(node, G, goal)
#                 if new_node:
#                     path_nodes.append(new_node.node_id)
#                     path_edges.update(new_node.used_edges)
#                     node = new_node
#                 break
        
#         # --- Simulation ---
#         if path_nodes[-1] == goal:
#             reward = 1.0  # 到达目标
#         else:
#             # 补全路径（确保到达goal）
#             try:
#                 # 使用networkx的shortest_path，但跳过已用edges
#                 def edge_filter(u, v, d):
#                     return d["sumo_edge_id"] not in path_edges
                
#                 subgraph = nx.subgraph_view(G, filter_edge=edge_filter)
#                 remaining_path = nx.shortest_path(subgraph, path_nodes[-1], goal, weight="length")
#                 full_path = path_nodes + remaining_path[1:]
#             except nx.NetworkXNoPath:
#                 reward = 0  # 无有效路径
#                 backpropagate(node, reward)
#                 continue
            
#             # 在SUMO中仿真
#             travel_time = simulate_path(G, full_path, sumo_net, config_file)
#             reward = 1 / (travel_time + 1e-6)  # 奖励与时间成反比
        
#         # --- Backpropagation ---
#         backpropagate(node, reward)
    
#     # 提取最优路径
#     best_path = []
#     node = root
#     while node.children:
#         node = max(node.children, key=lambda x: x.visits)
#         best_path.append(node.node_id)
#     return best_path

# # ------------------------------
# # 7. 运行示例
# # ------------------------------
# start = "node_A"
# goal = "node_B"
# config_file = "sim.sumocfg"

# best_path = run_mcts(G, net, start, goal, config_file)
# print("最优路径（networkx节点）:", best_path)

# # 转换为SUMO edge路径
# sumo_edges = []
# for i in range(len(best_path) - 1):
#     from_node, to_node = best_path[i], best_path[i+1]
#     sumo_edges.append(G.edges[from_node, to_node]["sumo_edge_id"])
# print("SUMO edge路径:", sumo_edges)