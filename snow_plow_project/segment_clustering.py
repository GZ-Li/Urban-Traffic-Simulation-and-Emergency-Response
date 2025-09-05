import sumolib
from shapely.ops import linemerge
from shapely.geometry import LineString
import geopandas as gpd
import networkx as nx
import xml.etree.ElementTree as ET
from collections import defaultdict
import math

# huanwei_road_id = '200001505'

specific_edge_id = '200001272'
net_file_path = "E:\\Traffic_Simulation\\snow_plow_project\\net\\core_withshape_with_light_changing.net.xml"
rou_file_path = "E:\\Traffic_Simulation\\snow_plow_project\\rou\\mapcore_500m_core_withshape_with_light_test.rou.xml"
net = sumolib.net.readNet(net_file_path)

all_edges = net.getEdges()
edges = [edge for edge in all_edges if not edge.getID().startswith(':')]
print(f"原始edge数量: {len(edges)}")

G = nx.DiGraph()
edge_info = {}
for edge in edges:
    edge_id = edge.getID()
    from_node = edge.getFromNode().getID()
    to_node = edge.getToNode().getID()
    edge_info[edge_id] = {
        'id': edge_id,
        'from_node': from_node,
        'to_node': to_node,
        'length': edge.getLength(),
        'lanes': len(edge.getLanes()),
    }
    G.add_node(from_node)
    G.add_node(to_node)
    G.add_edge(from_node, to_node, edge_id=edge_id)
print(len(G.nodes()))

simple_nodes = []
for node in G.nodes():
    in_degree = G.in_degree(node)  
    out_degree = G.out_degree(node) 
    if in_degree == 1 and out_degree == 1:
        simple_nodes.append(node)
print(f"找到 {len(simple_nodes)} 个简单节点（可以合并的路段连接点）")


used_edges = set()
mapping_dict = {}
path_counter = 0
for start_node in G.nodes():
    if start_node not in simple_nodes:
        for next_node in G.successors(start_node):
            edge_id = G[start_node][next_node]['edge_id']
            if edge_id not in used_edges:
                current_path = [edge_id]
                used_edges.add(edge_id)
                current_node = next_node
                while current_node in simple_nodes:
                    next_nodes = list(G.successors(current_node))
                    if len(next_nodes) == 1:
                        next_node = next_nodes[0]
                        next_edge_id = G[current_node][next_node]['edge_id']
                        if next_edge_id not in used_edges:
                            current_path.append(next_edge_id)
                            used_edges.add(next_edge_id)
                            current_node = next_node
                        else:
                            break 
                    else:
                        break
                if len(current_path) > 1:
                    new_path_id = f"merged_path_{path_counter}"
                    mapping_dict[new_path_id] = current_path
                    path_counter += 1
                else:
                    mapping_dict[edge_id] = [edge_id]
                    
for edge_id in edge_info:
    if edge_id not in used_edges:
        mapping_dict[edge_id] = [edge_id]
        used_edges.add(edge_id)

print(f"处理完成！已处理 {len(used_edges)} 个路段")


# 13. 输出统计信息
original_count = len(edges)
merged_count = len(mapping_dict)
reduction_percent = (1 - merged_count / original_count) * 100

print(f"\n=== 合并结果统计 ===")
print(f"原始路段数量: {original_count}")
print(f"合并后路段数量: {merged_count}")
print(f"压缩比例: {reduction_percent:.1f}%")

# 14. 计算合并情况
merged_paths_count = 0
single_roads_count = 0

for new_id, old_ids in mapping_dict.items():
    if len(old_ids) > 1:
        merged_paths_count += 1
    else:
        single_roads_count += 1

print(f"合并路径数量: {merged_paths_count}")
print(f"单个路段数量: {single_roads_count}")

new_G = nx.DiGraph()
for node in G.nodes():
    new_G.add_node(node)
for new_edge_id, old_edge_ids in mapping_dict.items():
    if len(old_edge_ids) == 1:
        # 单个路段，直接复制
        old_edge_id = old_edge_ids[0]
        from_node = edge_info[old_edge_id]['from_node']
        to_node = edge_info[old_edge_id]['to_node']
        new_G.add_edge(from_node, to_node, edge_id=new_edge_id, original_edges=old_edge_ids)
    else:
        # 合并的路段：from是第一个路段的from，to是最后一个路段的to
        first_edge_id = old_edge_ids[0]
        last_edge_id = old_edge_ids[-1]
        from_node = edge_info[first_edge_id]['from_node']
        to_node = edge_info[last_edge_id]['to_node']
        new_G.add_edge(from_node, to_node, edge_id=new_edge_id, original_edges=old_edge_ids)
        
print(f"新图中添加了 {new_G.number_of_edges()} 条边")

# 24. 验证新旧图的节点数量是否一致
print(f"原图节点数: {G.number_of_nodes()}, 新图节点数: {new_G.number_of_nodes()}")
print(f"原图边数: {G.number_of_edges()}, 新图边数: {new_G.number_of_edges()}")


# 25. 为新的边计算属性
new_edge_attributes = {}

for new_edge_id, old_edge_ids in mapping_dict.items():
    if len(old_edge_ids) == 1:
        # 单个路段，直接复制属性
        old_edge_id = old_edge_ids[0]
        new_edge_attributes[new_edge_id] = {
            'length': edge_info[old_edge_id]['length'],
            'lanes': edge_info[old_edge_id]['lanes'],
            'from_node': edge_info[old_edge_id]['from_node'],
            'to_node': edge_info[old_edge_id]['to_node'],
            'segment_count': 1,
            'merged_edges': [old_edge_id],
            'type': 'single'
        }
    else:
        # 合并的路段，计算总属性
        total_length = 0
        max_lanes = 0
        from_node = edge_info[old_edge_ids[0]]['from_node']
        to_node = edge_info[old_edge_ids[-1]]['to_node']
        
        for old_edge_id in old_edge_ids:
            total_length += edge_info[old_edge_id]['length']
            max_lanes = max(max_lanes, edge_info[old_edge_id]['lanes'])
        
        new_edge_attributes[new_edge_id] = {
            'length': total_length,
            'lanes': max_lanes,
            'from_node': from_node,
            'to_node': to_node,
            'segment_count': len(old_edge_ids),
            'merged_edges': mapping_dict[new_edge_id],
            'type': 'merged'
        }

# 26. 将属性添加到新图的边中
for u, v, data in new_G.edges(data=True):
    edge_id = data['edge_id']
    if edge_id in new_edge_attributes:
        for attr_name, attr_value in new_edge_attributes[edge_id].items():
            new_G[u][v][attr_name] = attr_value


vehicle_counts = defaultdict(int)
tree = ET.parse(rou_file_path)
root = tree.getroot()
for vehicle in root.findall('vehicle'):
    route = vehicle.find('route')
    if route is not None and 'edges' in route.attrib:
        edge_sequence = route.attrib['edges'].split()
        for edge_id in edge_sequence:
            if not edge_id.startswith(':'):  # 过滤内部edge
                vehicle_counts[edge_id] += 1


for old_edge_id in edge_info.keys():
    edge_info[old_edge_id]['traffic_flow'] = vehicle_counts.get(old_edge_id, 0)
    

for new_edge_id, old_edge_ids in mapping_dict.items():
    total_traffic = 0
    for old_edge_id in old_edge_ids:
        total_traffic += edge_info[old_edge_id]['traffic_flow']
    new_edge_attributes[new_edge_id]['traffic_flow'] = total_traffic
    for u, v, data in new_G.edges(data=True):
        if data['edge_id'] == new_edge_id:
            new_G[u][v]['traffic_flow'] = total_traffic
            break
        

node_coordinates = {}
for node in net.getNodes():
    node_id = node.getID()
    x, y = node.getCoord()
    node_coordinates[node_id] = (x, y)
print(f"从net.xml中获取到 {len(node_coordinates)} 个节点的坐标")


for u, v, data in new_G.edges(data=True):
    if specific_edge_id in data['original_edges']:
        print('Found')
        specific_edge_data = data
        print(specific_edge_data)
        break
    
x_specific, y_specific = node_coordinates[specific_edge_data['from_node']]
for u, v, data in new_G.edges(data=True):
    from_node = data['from_node']
    if from_node in node_coordinates:
        x_temp, y_temp = node_coordinates[from_node]
        distance_temp = math.sqrt((x_temp - x_specific) ** 2 + (y_temp - y_specific) ** 2)
        new_G[u][v]['euclidean_distance'] = distance_temp
        

all_distances = []
for u, v, data in new_G.edges(data=True):
    all_distances.append((data['edge_id'], data['euclidean_distance']))

all_distances.sort(key=lambda x: x[1])
total_edges = len(all_distances)
top_20_percent_count = int(total_edges * 0.2)
top_20_edges = [edge_id for edge_id, distance in all_distances[:top_20_percent_count]]

print(f"总边数: {total_edges}")
print(f"前20%的边数量: {top_20_percent_count}")
print(f"前20%的边示例: {top_20_edges[:5]}")


# actual_distances_to_specific = {}
# for edge_id in top_20_edges:
#     edge_from_node = None
#     edge_to_node = None
#     for u, v, data in new_G.edges(data=True):
#         if data['edge_id'] == edge_id:
#             edge_from_node = u
#             edge_to_node = v
#             break
#     if edge_from_node is None:
#         continue
#     try:
#         path = nx.shortest_path(new_G, source=edge_to_node, target=specific_edge_data['from_node'], weight='length')
#         total_length = 0
#         for i in range(len(path) - 1):
#             u, v = path[i], path[i+1]
#             edge_data = new_G[u][v]
#             total_length += edge_data['length']
#         actual_distances_to_specific[edge_id] = {
#             'actual_distance': total_length,
#             'path_length': len(path) - 1,
#             'path_nodes': path
#         }
        
#     except nx.NetworkXNoPath:
#         actual_distances_to_specific[edge_id] = {
#             'actual_distance': float('inf'),
#             'path_length': float('inf'),
#             'path_nodes': []
#         }

# # 按实际距离排序
# sorted_actual_distances = sorted(actual_distances_to_specific.items(), key=lambda x: x[1]['actual_distance'])
# print(f"\n前10个最短实际距离:")
# for edge_id, info in sorted_actual_distances[:10]:
#     print(f"边 {edge_id}: 实际距离={info['actual_distance']:.2f}m, 路径长度={info['path_length']}")

actual_distances_to_specific = {}
for u, v, data in new_G.edges(data=True):
    edge_to_node = v
    try:
        path = nx.shortest_path(new_G, source=edge_to_node, target=specific_edge_data['from_node'], weight='length')
        total_length = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge_data = new_G[u][v]
            total_length += edge_data['length']
        actual_distances_to_specific[edge_id] = {
            'actual_distance': total_length,
            'path_length': len(path) - 1,
            'path_nodes': path
        }
        
    except nx.NetworkXNoPath:
        actual_distances_to_specific[edge_id] = {
            'actual_distance': float('inf'),
            'path_length': float('inf'),
            'path_nodes': []
        }

# 按实际距离排序
sorted_actual_distances = sorted(actual_distances_to_specific.items(), key=lambda x: x[1]['actual_distance'])
print(sorted_actual_distances)
print(f"\n前10个最短实际距离:")
for edge_id, info in sorted_actual_distances[:10]:
    print(f"边 {edge_id}: 实际距离={info['actual_distance']:.2f}m, 路径长度={info['path_length']}")