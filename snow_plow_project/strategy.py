import sumolib
import networkx as nx
import xml.etree.ElementTree as ET
from collections import defaultdict
import math
import numpy as np

# huanwei_road_id = '200001505'
specific_edge_id = '200001272'
net_file_path = "E:\\Traffic_Simulation\\snow_plow_project\\net\\core_withshape_with_light_changing.net.xml"
rou_file_path = "E:\\Traffic_Simulation\\snow_plow_project\\rou\\mapcore_500m_core_withshape_with_light_test.rou.xml"
net = sumolib.net.readNet(net_file_path)


# Detect the Simple Nodes, and the mapping relationship between the original edges and the merged edges;
all_edges = net.getEdges()
edges = [edge for edge in all_edges if not edge.getID().startswith(':')]
G = nx.DiGraph()
origin_edge_info = {}
for edge in edges:
    edge_id = edge.getID()
    from_node = edge.getFromNode().getID()
    to_node = edge.getToNode().getID()
    origin_edge_info[edge_id] = {
        'id': edge_id,
        'from_node': from_node,
        'to_node': to_node,
        'length': edge.getLength(),
        'lanes': len(edge.getLanes()),
    }
    G.add_node(from_node)
    G.add_node(to_node)
    G.add_edge(from_node, to_node, edge_id=edge_id)

simple_nodes = []
for node in G.nodes():
    in_degree = G.in_degree(node)  
    out_degree = G.out_degree(node) 
    if in_degree == 1 and out_degree == 1:
        simple_nodes.append(node)

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
                    
for edge_id in origin_edge_info:
    if edge_id not in used_edges:
        mapping_dict[edge_id] = [edge_id]
        used_edges.add(edge_id)

new_G = nx.DiGraph()
for node in G.nodes():
    new_G.add_node(node)
for new_edge_id, old_edge_ids in mapping_dict.items():
    if len(old_edge_ids) == 1:
        from_node = origin_edge_info[old_edge_ids[0]]['from_node']
        to_node = origin_edge_info[old_edge_ids[0]]['to_node']
        new_G.add_edge(from_node, to_node, edge_id=new_edge_id, original_edges=old_edge_ids)
    else:
        from_node = origin_edge_info[old_edge_ids[0]]['from_node']
        to_node = origin_edge_info[old_edge_ids[-1]]['to_node']
        new_G.add_edge(from_node, to_node, edge_id=new_edge_id, original_edges=old_edge_ids)
        
new_edge_info = {}
for new_edge_id, old_edge_ids in mapping_dict.items():
    if len(old_edge_ids) == 1:
        new_edge_info[new_edge_id] = {
            'length': origin_edge_info[old_edge_ids[0]]['length'],
            'lanes': origin_edge_info[old_edge_ids[0]]['lanes'],
            'from_node': origin_edge_info[old_edge_ids[0]]['from_node'],
            'to_node': origin_edge_info[old_edge_ids[0]]['to_node'],
            'segment_count': 1,
            'merged_edges': [old_edge_ids[0]],
            'type': 'single'
        }
    else:
        total_length = 0
        max_lanes = 0
        from_node = origin_edge_info[old_edge_ids[0]]['from_node']
        to_node = origin_edge_info[old_edge_ids[-1]]['to_node']
        for old_edge_id in old_edge_ids:
            total_length += origin_edge_info[old_edge_id]['length']
            max_lanes = max(max_lanes, origin_edge_info[old_edge_id]['lanes'])
        new_edge_info[new_edge_id] = {
            'length': total_length,
            'lanes': max_lanes,
            'from_node': from_node,
            'to_node': to_node,
            'segment_count': len(old_edge_ids),
            'merged_edges': mapping_dict[new_edge_id],
            'type': 'merged'
        }

for u, v, data in new_G.edges(data=True):
    edge_id = data['edge_id']
    if edge_id in new_edge_info:
        for attr_name, attr_value in new_edge_info[edge_id].items():
            new_G[u][v][attr_name] = attr_value
            
           

            
# def get_distance(target_nodes, source_nodes, new_G): # target_nodes:[], source_nodes:[]
#     min_distance_lst = []
#     overall_distance_lst = []
#     for target_node in target_nodes:
#         temp_lst = []
#         for source_node in source_nodes:
#             try:
#                 total_length = 0
#                 path = nx.shortest_path(new_G, source=source_node, target=target_node, weight='length')
#                 for i in range(len(path) - 1):
#                     u, v = path[i], path[i+1]
#                     edge_data = new_G[u][v]
#                     total_length += edge_data['length']
#                     temp_lst.append(total_length)
#             except:
#                 temp_lst.append(float('inf'))
#         overall_distance_lst.append(temp_lst)
#     for i in range(len(overall_distance_lst)):
#         min_distance_lst.append(min([lst[i] for lst in overall_distance_lst]))
#     return overall_distance_lst, min_distance_lst

# source_nodes = []
# for new_edge, _ in mapping_dict.items():
#     source_nodes.append(new_G[new_edge]['from_node'])
# print(source_nodes)
# specific_nodes = ['300001100']
# print(get_distance(specific_nodes, source_nodes, new_G))
            