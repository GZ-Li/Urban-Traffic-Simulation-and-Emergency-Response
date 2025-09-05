import sumolib
import networkx as nx
import xml.etree.ElementTree as ET
from collections import defaultdict
import math

from sumolib.route import euclidean
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


# huanwei_road_id = '200001505'
specific_edge_id = '200001272'
specific_edge_from_node = '300001100'
truck_num = 5
net_file_path = "E:\\Traffic_Simulation\\snow_plow_project\\net\\core_withshape_with_light_changing.net.xml"
rou_file_path = "E:\\Traffic_Simulation\\snow_plow_project\\rou\\mapcore_500m_core_withshape_with_light_test.rou.xml"
net = sumolib.net.readNet(net_file_path)
cleared_edges = []
euclidean_filter_ratio = 0.2
update_step_ratio = 0.05


all_edges = net.getEdges()
edges = [edge for edge in all_edges if not edge.getID().startswith(':')]
G = nx.DiGraph()
origin_edge_info = {}
origin_node_info = {}
summary_clear_edge_dict = {}
summary_truck_location_dict = {}
summary_total_clear_edge_dict = {}
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
    G.add_edge(from_node, to_node, edge_id=edge_id, length=origin_edge_info[edge_id]['length'])
edge_id_list = list(origin_edge_info.keys())
edge_num = len(edge_id_list)


for node_id in G.nodes():
    node_obj = net.getNode(node_id)
    origin_node_info[node_id] = {
        'id': node_id,
        'x': node_obj.getCoord()[0],
        'y': node_obj.getCoord()[1],
    }
    

edge_traffic_flow_dict = defaultdict(int)
tree = ET.parse(rou_file_path)
root = tree.getroot()
for vehicle in root.findall('.//vehicle'):
    route = vehicle.find('route')
    if route is not None and 'edges' in route.attrib:
        edges = route.attrib['edges'].split()
        for edge_id in edges:
            edge_traffic_flow_dict[edge_id] += 1
    

def get_euclidean_distance(node_id1, node_id2):
    x1, y1 = origin_node_info[node_id1]['x'], origin_node_info[node_id1]['y']
    x2, y2 = origin_node_info[node_id2]['x'], origin_node_info[node_id2]['y']
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def get_euclidean_distance_from_center(center, node_id):
    x, y = origin_node_info[node_id]['x'], origin_node_info[node_id]['y']
    return math.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)

def get_path_distance(node_id1, node_id2):
    path = nx.shortest_path(G, source=node_id1, target=node_id2, weight='length')
    return sum([G.get_edge_data(path[i], path[i+1])['length'] for i in range(len(path) - 1)]), path

def get_traffic_flow(edge_id):
    return edge_traffic_flow_dict[edge_id]

def get_score(cleared_distance, uncleared_distance, length, num_lane, traffic_flow, alpha1 = 1, v1 = 2, v2 = 1): # score = traffic_flow / (alpha1 * (length * num_lane) + alpha2 * (cleared_distance / v1 + uncleared_distance / v2))
    return traffic_flow / (alpha1 * (length * num_lane) + (cleared_distance / v1 + uncleared_distance / v2))
    

coor_dict = {}
for edge in list(origin_edge_info.keys()):
    coor_dict[edge] = (origin_node_info[origin_edge_info[edge]['from_node']]['x'], origin_node_info[origin_edge_info[edge]['from_node']]['y'])
edge_ids = list(coor_dict.keys())
coor_array = np.array([coor_dict[eid] for eid in edge_ids])
kmeans = KMeans(n_clusters=truck_num, init='k-means++', n_init=1, random_state=42)
kmeans.fit(coor_array)
labels = kmeans.labels_
clusters = {i: [] for i in range(5)}
for eid, label in zip(edge_ids, labels):
    clusters[label].append(eid)
cluster_centers = kmeans.cluster_centers_
# 可视化分块
# plt.figure(figsize=(8, 6))
# for eid in edge_ids:
#     x, y = coor_dict[eid]
#     length = origin_edge_info[eid]['length']
#     cluster = labels[edge_ids.index(eid)]
#     plt.plot(x, y, 'o', markersize=4, color=f"C{cluster}")
# plt.scatter(cluster_centers[:, 0], cluster_centers[:, 1], 
#             c="black", marker="x", s=100, label="Cluster Centers")
# plt.xlabel("X")
# plt.ylabel("Y")
# plt.legend()
# plt.show()


def get_truck_locations(clusters, origin_edge_info, origin_node_info, cleared_edges, recent_cleared_edges = [], prev_truck_locations = [], specific_edge_from_node = specific_edge_from_node, truck_num = truck_num):
    truck_locations = {}
    if len(cleared_edges) == 0:
        for i in range(truck_num):
            truck_locations[i] = specific_edge_from_node
    if len(cleared_edges) != 0:
        for cid, edge_list in clusters.items():
            relevant_edges = [eid for eid in recent_cleared_edges if eid in edge_list]
            if relevant_edges:  
                prev_loc = prev_truck_locations[cid]
                farthest_edge = max(
                    relevant_edges,
                    key=lambda e: get_euclidean_distance(prev_loc,
                                                        origin_edge_info[e]['from_node'])
                )
                new_loc = origin_edge_info[farthest_edge]['from_node']
                truck_locations[cid] = new_loc
            else:
                center = cluster_centers[cid]
                print(center)
                nearest_edge = min(
                    recent_cleared_edges,
                    key=lambda e: get_euclidean_distance_from_center(center,
                                                        origin_edge_info[e]['from_node'])
                )
                new_loc = origin_edge_info[nearest_edge]['from_node']
                truck_locations[cid] = new_loc
    return truck_locations


for i in range(20):
    print(i)
    euclidean_distance_dict = {}
    euclidean_pair_dict = {}
    path_distance_dict = {}
    path_dict = {}
    length_dict = {}
    lane_dict = {}
    traffic_flow_dict = {}
    cleared_distance_dict = {}
    uncleared_distance_dict = {}
    score_dict = {}
    uncleared_edges = [edge for edge in edge_id_list if edge not in cleared_edges]
    # recent_cleared_edges = summary_clear_edge_dict[i]
    # prev_truck_locations = summary_truck_location_dict[i]
    if len(cleared_edges) == 0:
        truck_locations_dict = get_truck_locations(clusters, origin_edge_info, origin_node_info, cleared_edges)
        summary_truck_location_dict[(i)*update_step_ratio] = truck_locations_dict
    else:
        recent_cleared_edges = summary_clear_edge_dict[(i-1)*update_step_ratio]
        prev_truck_locations = summary_truck_location_dict[(i-1)*update_step_ratio]
        truck_locations_dict = get_truck_locations(clusters, origin_edge_info, origin_node_info, cleared_edges, recent_cleared_edges, prev_truck_locations)
        summary_truck_location_dict[(i)*update_step_ratio] = truck_locations_dict
    for edge in uncleared_edges:
        distance_truck_pairs = [(get_euclidean_distance(origin_edge_info[edge]['from_node'], truck_location), truck_location) for truck_location in list(truck_locations_dict.values())]
        min_dist, nearest_truck = min(distance_truck_pairs, key=lambda x: x[0])
        euclidean_distance_dict[edge] = min_dist
        euclidean_pair_dict[edge] = nearest_truck
    sorted_euclidean_distance_lst = sorted(euclidean_distance_dict.items(), key=lambda x: x[1])
    euclidean_selected_edges = [eid for eid, dist in sorted_euclidean_distance_lst[:int(edge_num * euclidean_filter_ratio)]]
    for edge in euclidean_selected_edges:
        try:
            path_distance_dict[edge], path_dict[edge] = get_path_distance(origin_edge_info[edge]['from_node'], euclidean_pair_dict[edge])
            cleared_distance_dict[edge] = 0
            uncleared_distance_dict[edge] = 0
            for road in path_dict[edge]:
                if road in cleared_edges:
                    cleared_distance_dict[edge] += origin_edge_info[road]['length']
                else:
                    uncleared_distance_dict[edge] += origin_edge_info[road]['length']
        except:
            continue
    for edge in list(path_dict.keys()):
        length_dict[edge] = origin_edge_info[edge]['length']
        lane_dict[edge] = origin_edge_info[edge]['lanes']
        traffic_flow_dict[edge] = get_traffic_flow(edge)
        score_dict[edge] = get_score(cleared_distance_dict[edge], uncleared_distance_dict[edge], length_dict[edge], lane_dict[edge], traffic_flow_dict[edge])
    sorted_score_lst = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    final_selected_edges = [eid for eid, score in sorted_score_lst[:int(edge_num * update_step_ratio)]]
    for edge in final_selected_edges:
        cleared_edges.append(edge)
    summary_clear_edge_dict[(i)*update_step_ratio] = final_selected_edges
    summary_total_clear_edge_dict[(i)*update_step_ratio] = cleared_edges
    
print(summary_clear_edge_dict)
print(summary_truck_location_dict)


# import matplotlib.pyplot as plt
# import matplotlib.animation as animation

# def visualize_snowplow(origin_edge_info, origin_node_info, cleared_edges_per_step):
#     # 准备 figure
#     fig, ax = plt.subplots(figsize=(10, 10))
    
#     # 画背景路网（灰色）
#     for edge_id, info in origin_edge_info.items():
#         from_node = info['from_node']
#         to_node = info['to_node']
#         x1, y1 = origin_node_info[from_node]['x'], origin_node_info[from_node]['y']
#         x2, y2 = origin_node_info[to_node]['x'], origin_node_info[to_node]['y']
#         ax.plot([x1, x2], [y1, y2], color='lightgray', linewidth=0.8, zorder=1)

#     # 动态更新函数
#     def update(frame):
#         ax.clear()
#         # 重新画背景路网
#         for edge_id, info in origin_edge_info.items():
#             from_node = info['from_node']
#             to_node = info['to_node']
#             x1, y1 = origin_node_info[from_node]['x'], origin_node_info[from_node]['y']
#             x2, y2 = origin_node_info[to_node]['x'], origin_node_info[to_node]['y']
#             ax.plot([x1, x2], [y1, y2], color='lightgray', linewidth=0.8, zorder=1)

#         # 画当前时间步及之前清扫过的路段
#         cleared_edges = []
#         for t in sorted(cleared_edges_per_step.keys()):
#             if t <= frame:
#                 cleared_edges.extend(cleared_edges_per_step[t])
#         for edge_id in cleared_edges:
#             info = origin_edge_info[edge_id]
#             from_node = info['from_node']
#             to_node = info['to_node']
#             x1, y1 = origin_node_info[from_node]['x'], origin_node_info[from_node]['y']
#             x2, y2 = origin_node_info[to_node]['x'], origin_node_info[to_node]['y']
#             ax.plot([x1, x2], [y1, y2], color='red', linewidth=2, zorder=2)

#         ax.set_title(f"Time step: {frame}")
#         ax.axis("equal")
#         ax.axis("off")

#     # 动画
#     frames = sorted(cleared_edges_per_step.keys())
#     ani = animation.FuncAnimation(fig, update, frames=frames, repeat=False, interval=1000)
#     plt.show()
#     return ani

# ani = visualize_snowplow(origin_edge_info, origin_node_info, summary_clear_edge_dict)



import matplotlib.pyplot as plt
import matplotlib.animation as animation

def visualize_snowplow_with_trucks(origin_edge_info, origin_node_info, cleared_edges_per_step, truck_positions_dict):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    truck_colors = ['red', 'blue', 'green', 'orange', 'purple']  # 五辆车颜色

    # 动态更新函数
    def update(frame):
        ax.clear()
        # 画背景路网
        for edge_id, info in origin_edge_info.items():
            from_node = info['from_node']
            to_node = info['to_node']
            x1, y1 = origin_node_info[from_node]['x'], origin_node_info[from_node]['y']
            x2, y2 = origin_node_info[to_node]['x'], origin_node_info[to_node]['y']
            ax.plot([x1, x2], [y1, y2], color='lightgray', linewidth=0.8, zorder=1)

        # 画清扫过的路段
        cleared_edges = []
        for t in sorted(cleared_edges_per_step.keys()):
            if t <= frame:
                cleared_edges.extend(cleared_edges_per_step[t])
        for edge_id in cleared_edges:
            info = origin_edge_info[edge_id]
            from_node = info['from_node']
            to_node = info['to_node']
            x1, y1 = origin_node_info[from_node]['x'], origin_node_info[from_node]['y']
            x2, y2 = origin_node_info[to_node]['x'], origin_node_info[to_node]['y']
            ax.plot([x1, x2], [y1, y2], color='red', linewidth=2, zorder=2)

        # 画扫雪车（节点位置）
        if frame in truck_positions_dict:
            positions = truck_positions_dict[frame]
            for i in range(5):
                node_id = positions[i]
                x, y = origin_node_info[node_id]['x'], origin_node_info[node_id]['y']
                ax.scatter(x, y, color=truck_colors[i], s=80, zorder=3, label=f'Truck {i}' if frame==0 else "")
        
        if frame == 0:
            ax.legend(loc='upper right')
        ax.set_title(f"Time step: {frame}")
        ax.axis("equal")
        ax.axis("off")

    frames = sorted(cleared_edges_per_step.keys())
    ani = animation.FuncAnimation(fig, update, frames=frames, repeat=False, interval=1000)
    plt.show()
    return ani

# 调用示例
ani = visualize_snowplow_with_trucks(origin_edge_info, origin_node_info, summary_clear_edge_dict, summary_truck_location_dict)
