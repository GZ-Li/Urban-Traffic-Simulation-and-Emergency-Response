import os
import re
import json
import traci
import pandas as pd
from sumolib.net import readNet
from shapely.geometry import LineString
import xml.etree.ElementTree as ET
import pyproj
import itertools
from collections import defaultdict

# ==================== 配置部分 ====================
simulation_config = {
    "net_path": "E:\\Traffic_Simulation\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml",
    "road_data_csv": "E:\\Traffic_Simulation\\Adverse_weather_traffic\\actual_speed_variation_0718.csv",
    "scale": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90],
    # "scale": [1, 2, 3],
    "simulation_duration": 401,
    "interval": 50,
    "weather_params": {
        "accel": "2.6",
        "decel": "3.6",
        "max_speed": "35",
        "min_gap": "2.5"
    },
}


tree = ET.parse(simulation_config['net_path'])
root = tree.getroot()
location_tag = root.find("location")
netOffset_str = location_tag.attrib["netOffset"]
projParameter = location_tag.attrib["projParameter"]
netOffsetX, netOffsetY = map(float, netOffset_str.split(","))
transformer = pyproj.Transformer.from_proj(
    pyproj.Proj(projParameter),
    pyproj.Proj(proj="latlong", datum="WGS84"),
    always_xy=True
)


def init_sumo(route_file=None):
    sumo_cmd = [
        "sumo",
        "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_scale_normal.sumocfg",
    ]
    traci.start(sumo_cmd)


def coordinate_transform(transformer, netOffsetX, netOffsetY, x_sumo, y_sumo):
    x_proj = x_sumo - netOffsetX
    y_proj = y_sumo - netOffsetY
    lon, lat = transformer.transform(x_proj, y_proj)
    return (lon, lat)


def load_road_data(csv_path):
    return pd.read_csv(csv_path)


def string_to_linestring(linestring_str):
    coordinates_str = re.findall(r'\(([^)]+)', linestring_str)
    if not coordinates_str:
        raise ValueError("Invalid LINESTRING format")
    coordinates = []
    for coord in coordinates_str[0].split(','):
        x, y = map(float, coord.strip().split())
        coordinates.append((x, y))
    linestring = LineString(coordinates)
    return linestring


def is_road_matched(short_line_coords, long_line_coords, tolerance=1e-6):
    short_line = LineString(short_line_coords)
    long_line = string_to_linestring(long_line_coords)
    long_line_buffer = long_line.buffer(tolerance)
    if long_line_buffer.contains(short_line):
        return True
    intersection = short_line.intersection(long_line_buffer)
    if intersection.length >= short_line.length * (1 - tolerance):
        return True
    return False


def get_edge_coordinates(net, edge_id):
    edge = net.getEdge(edge_id)
    shape = edge.getShape()
    coords_lst = []
    coord1, coord2 = (float(shape[0][0]), float(shape[0][1])), (float(shape[1][0]), float(shape[1][1]))
    return [coord1, coord2]


def match_edges_to_roads(net, road_df):
    matched_data = [] 
    for edge in net.getEdges():
        edge_id = edge.getID()
        edge_coords = get_edge_coordinates(net, edge_id)
        for _, road in road_df.iterrows():
            if is_road_matched((coordinate_transform(transformer, netOffsetX, netOffsetY, edge_coords[0][0], edge_coords[0][1]), coordinate_transform(transformer, netOffsetX, netOffsetY, edge_coords[1][0], edge_coords[1][1])), road['geometry'], 0.002):
                matched_data.append({
                    'edge_id': edge_id,
                    'road_name': road['name'],
                    'direction': road['direction'],
                    'normal_speed': road['normal_speed'],
                    'geometry': road['geometry']
                })
                break
    return pd.DataFrame(matched_data)


def modify_vehicle_xml(input_file, output_file, accel, decel, maxSpeed, minGap): # Input parameters are str
    tree = ET.parse(input_file)
    root = tree.getroot()
    vehicles = []
    for i, elem in enumerate(root):
        if elem.tag == 'vehicle':
            vehicles.append((i, elem))
    for i, vehicle in reversed(vehicles):
        vehicle_id = vehicle.get('id')
        vtype_id = f"{vehicle_id}_rain"
        vtype = ET.Element('vType', {'id': vtype_id, 'accel': accel, 'decel': decel, "maxSpeed": maxSpeed, 'minGap': minGap})
        root.insert(i, vtype)
        vehicle.set('type', vtype_id)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    
def modify_sumocfg(input_file, out_file, scale):
    tree = ET.parse(input_file) 
    root = tree.getroot()
    for route in root.iter('route-files'):
        route.set('value', f"scale_rou/routes_od_{str(scale)}_normal.rou.xml") 
    tree.write(out_file, encoding='utf-8', xml_declaration=True)


# def modify_vehicle_xml(input_file, output_file, accel, decel, maxSpeed, minGap):
#     accel = str(accel)
#     decel = str(decel)
#     maxSpeed = str(maxSpeed)
#     minGap = str(minGap)
#     tree = ET.parse(input_file)
#     root = tree.getroot()
#     vehicles = root.findall('vehicle')
#     vtype_list = []
#     new_root = ET.Element('routes')
#     for vehicle in vehicles:
#         vehicle_id = vehicle.get('id')
#         vtype_id = f"{vehicle_id}_rain"
#         vtype = ET.Element('vType', {
#             'id': vtype_id,
#             'accel': accel,
#             'decel': decel,
#             'maxSpeed': maxSpeed,
#             'minGap': minGap
#         })
#         vtype_list.append(vtype)
#     for vehicle_index in range(len(vehicles)):
#         vehicle = vehicles[vehicle_index]
#         vehicle_id = vehicle.get('id')
#         vtype_id = f"{vehicle_id}_rain"
#         vehicle.set('type', vtype_id)
#         new_root.append(vtype_list[vehicle_index])
#         new_root.append(vehicle)
#     new_tree = ET.ElementTree(new_root)
#     new_tree.write("D:\\Adverse_weather_traffic\\rou\\mapcore_500m_core_withshape_with_light_test_rain.rou.xml", encoding='utf-8', xml_declaration=True)
#     print(f"✅ 成功写入：{output_file}")


def run_simulation(matched_df, duration=401, output_json_path="E:\\Traffic_Simulation\\Adverse_weather_traffic\\simulation_results\\scale_average_speeds_normal_0718.json"):
    total_res = {}
    for scale in simulation_config['scale']:
        print(scale)
        param = simulation_config['weather_params']
        modify_vehicle_xml(f"scale_rou/routes_od_{str(scale)}.rou.xml", f"scale_rou/routes_od_{str(scale)}_normal.rou.xml", "2.6", "3.6", "35", "2.5")
        modify_sumocfg("E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_scale_normal.sumocfg", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_scale_normal.sumocfg", scale)
        init_sumo()
        time_road_speeds = {}
        for step in range(duration):
            traci.simulationStep()
            if (step % simulation_config['interval'] == 0) and (step != 0):
                current_speeds = {}
                for edge_id in matched_df['edge_id']:
                    vehicles = traci.edge.getLastStepVehicleIDs(edge_id)
                    if vehicles:
                        avg_speed = sum(traci.vehicle.getSpeed(veh) for veh in vehicles) / len(vehicles)
                        current_speeds[edge_id] = avg_speed
                    else:
                        current_speeds[edge_id] = None
                time_road_speeds[step] = current_speeds
        total_res[str(scale)] = time_road_speeds
        traci.close()
    with open(output_json_path, "w") as f:
        json.dump(total_res, f, indent=4)


if __name__ == '__main__':
    net = readNet(simulation_config['net_path'])
    road_df = load_road_data(simulation_config['road_data_csv'])
    df = match_edges_to_roads(net, road_df)
    run_simulation(df)