"""
路径规划模块 - 使用A*和K短路算法计算救护车路径
"""
from networkx.algorithms.simple_paths import shortest_simple_paths
import xml.etree.ElementTree as ET
import networkx as nx
import math


def sumo_net_to_networkx(net_file_path):
    """
    将SUMO路网转换为NetworkX有向图
    
    Args:
        net_file_path: SUMO路网文件路径
    
    Returns:
        G: NetworkX有向图对象
    """
    tree = ET.parse(net_file_path)
    root = tree.getroot()
    G = nx.DiGraph()
    junction_positions = {}
    
    # 解析junction节点
    for junction in root.findall("junction"):
        node_id = junction.get("id")
        x = float(junction.get("x"))
        y = float(junction.get("y"))
        junction_positions[node_id] = (x, y)
    
    # 解析边
    edge_info = {}
    for edge in root.findall("edge"):
        edge_id = edge.get("id")
        if edge.get("from") is None or edge.get("to") is None:
            continue
        from_node = f"{edge_id}_out"
        to_node = f"{edge_id}_in"
        lane = edge.find("lane")
        length = float(lane.get("length")) if lane is not None else 0.0
        edge_info[edge_id] = (from_node, to_node, length)
        G.add_edge(from_node, to_node, edge_id=edge_id, length=length)
    
    # 解析连接关系
    for conn in root.findall("connection"):
        from_edge = conn.get("from")
        to_edge = conn.get("to")
        if from_edge in edge_info and to_edge in edge_info:
            G.add_edge(
                f"{from_edge}_in",
                f"{to_edge}_out",
                edge_id=f"{from_edge}_in_{to_edge}_out",
                turn_type=conn.get("dir", "unknown"),
            )
    
    # 添加节点位置信息
    for node in G.nodes():
        if node.endswith("_out"):
            junc_id = node.split("_out")[0]
            if junc_id in junction_positions:
                G.nodes[node]["pos"] = junction_positions[junc_id]
        elif node.endswith("_in"):
            junc_id = node.split("_in")[0]
            if junc_id in junction_positions:
                G.nodes[node]["pos"] = junction_positions[junc_id]
    
    return G


def heuristic(u, v, G):
    """
    A*算法的启发式函数（欧氏距离）
    
    Args:
        u: 起始节点
        v: 目标节点
        G: 图对象
    
    Returns:
        欧氏距离
    """
    pos_u = G.nodes[u].get("pos")
    pos_v = G.nodes[v].get("pos")
    if pos_u is None or pos_v is None:
        return 0
    return math.sqrt((pos_u[0] - pos_v[0])**2 + (pos_u[1] - pos_v[1])**2)


def find_k_shortest_paths(G, start_edge_id, end_edge_id=None, k=5):
    """
    使用Yen's K短路算法找到k条最短路径
    
    Args:
        G: NetworkX图对象
        start_edge_id: 起始edge ID
        end_edge_id: 目标edge ID
        k: 返回的路径数量
    
    Returns:
        路径列表，每条路径是edge ID的列表
    """
    # 获取起始edge对应的节点
    start_from, start_to = None, None
    for u, v, data in G.edges(data=True):
        if data.get("edge_id") == start_edge_id:
            start_from, start_to = u, v
            break
    
    if not start_from:
        raise ValueError(f"Edge ID {start_edge_id} not found!")
    
    if end_edge_id is None:
        return [[start_edge_id]]
    
    # 获取目标edge对应的节点
    end_from, end_to = None, None
    for u, v, data in G.edges(data=True):
        if data.get("edge_id") == end_edge_id:
            end_from, end_to = u, v
            break
    
    if not end_from:
        raise ValueError(f"Edge ID {end_edge_id} not found!")
    
    # 使用K短路算法
    paths = []
    for path_nodes in shortest_simple_paths(G, start_from, end_to, weight="length"):
        path_edges = []
        for i in range(len(path_nodes) - 1):
            u, v = path_nodes[i], path_nodes[i + 1]
            edge_data = G.get_edge_data(u, v)
            if edge_data and "edge_id" in edge_data:
                path_edges.append(edge_data["edge_id"])
        if path_edges:
            paths.append(path_edges)
            if len(paths) >= k:
                break
    
    return paths


def filter_internal_edges(path):
    """
    过滤掉路径中的内部连接边（包含_in_和_out的边）
    
    Args:
        path: edge ID列表
    
    Returns:
        过滤后的edge ID列表
    """
    return [item for item in path if not ("_in_" in item and "_out" in item)]
