import xml.etree.ElementTree as ET
from collections import defaultdict

def add_neigh_to_adjacent_lane(net_file, output_file, source_edge_id, target_edge_id):
    tree = ET.parse(net_file)
    root = tree.getroot()
    max_source_index = "999"
    max_source_id = "999"
    max_target_index = "999"
    max_target_id = "999"
    for edge in root.findall('edge'):
        if edge.get('id') == source_edge_id:
            lanes = edge.findall('lane')
            max_source_lane = max(lanes, key=lambda x: int(x.get('index')))
            max_source_index = max_source_lane.get("index")
            max_source_id = f"{source_edge_id}_{str(max_source_index)}"
        if edge.get('id') == target_edge_id:
            lanes = edge.findall('lane')
            max_target_lane = max(lanes, key=lambda x: int(x.get('index')))
            max_target_index = max_target_lane.get("index")
            max_target_id = f"{target_edge_id}_{str(max_target_index)}"
    if (max_target_index == "999") or (max_source_index == "999"):
        return
    
    print(max_source_id)
    print(max_target_id)
    
    existing_neigh = max_source_lane.find('neigh')
    if existing_neigh is not None:
        print(f"Lane {max_source_lane.get('id')} already has a <neigh> tag!")
        return

    ET.SubElement(max_source_lane, 'neigh', {'lane': max_target_id})
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
# add_neigh_to_adjacent_lane("D:\\Traffic_Accident\\net\\core_withshape_with_light_changing.net.xml", "net\\test.net.xml", "200014460", "200014459")

def find_opposite_edges(net_file):
    tree = ET.parse(net_file)
    root = tree.getroot()
    edge_dict = defaultdict(list)
    for edge in root.findall('edge'):
        if edge.get('function') != 'internal':  # 忽略内部道路
            from_node = edge.get('from')
            to_node = edge.get('to')
            edge_id = edge.get('id')
            edge_dict[(from_node, to_node)].append(edge_id)
    opposite_pairs = []
    processed_pairs = set()
    for (from_node, to_node), edge_ids in edge_dict.items():
        reverse_key = (to_node, from_node)
        if reverse_key in edge_dict and reverse_key != (from_node, to_node):
            if (reverse_key, (from_node, to_node)) not in processed_pairs:
                for edge_id in edge_ids:
                    for reverse_edge_id in edge_dict[reverse_key]:
                        opposite_pairs.append((edge_id, reverse_edge_id))
                processed_pairs.add(((from_node, to_node), reverse_key))
    return opposite_pairs

# 使用示例
# print(find_opposite_edges("E:\\Traffic_Simulation\\Traffic_accident\\full_net\\new_add_light.net.xml"))

net_file = "E:\\Traffic_Simulation\\Traffic_accident\\full_net\\new_add_light.net.xml"
output_file = "full_net\\new_add_light_reverse.net.xml"
opposite_edges = find_opposite_edges(net_file)
for edge_pair in opposite_edges:
    add_neigh_to_adjacent_lane(output_file, output_file, edge_pair[0], edge_pair[1])
    add_neigh_to_adjacent_lane(output_file, output_file, edge_pair[1], edge_pair[0])