import os
import re
import json
import copy
import traci
import pandas as pd
from sumolib.net import readNet
from shapely.geometry import LineString
import xml.etree.ElementTree as ET
import pyproj
import itertools
from collections import defaultdict


simulation_config = {
    "sumo_cfg": "D:\\Adverse_weather_traffic\\Core_500m_test_rain.sumocfg",
    "original_route": "D:\\Adverse_weather_traffic\\rou\\mapcore_500m_core_withshape_with_light_test.rou.xml",
    "rain_route": "D:\\Adverse_weather_traffic\\rou\\mapcore_500m_core_withshape_with_light_test_rain.rou.xml",
    "net_path": "E:\\Traffic_Simulation\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml",
    "road_data_csv": "E:\\Traffic_Simulation\\Adverse_weather_traffic\\actual_speed_variation_0718.csv",
    "simulation_duration": 400,
    "interval": 50,
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
        "-c", simulation_config['sumo_cfg'],
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
            if is_road_matched((coordinate_transform(transformer, netOffsetX, netOffsetY, edge_coords[0][0], edge_coords[0][1]), coordinate_transform(transformer, netOffsetX, netOffsetY, edge_coords[1][0], edge_coords[1][1])), road['geometry'], 0.0002):
                matched_data.append({
                    'edge_id': edge_id,
                    'name': road['name'],
                    'direction': road['direction'],
                    'normal_speed': road['normal_speed'],
                    'geometry': road['geometry']
                })
                break
    return pd.DataFrame(matched_data)


def three_categories(percentage):
    if percentage > -10:
        return 1
    if percentage > -40 and percentage <= -10:
        return 2
    else:
        return 3
    
    
def calculate_acc(df, road_df, test_dict_normal, test_dict_rain):
    speed_variation = []
    for road_id in df['edge_id']:
        speed1 = test_dict_normal[road_id]
        speed2 = test_dict_rain[road_id]
        if speed1 and speed2 and speed1 != 0:
            variation = (speed2 - speed1) / (speed1)
            speed_variation.append(variation)
        else:
            speed_variation.append(None)
    df['speed_variation'] = speed_variation
    avg_changes = df.groupby(["name", "direction"])["speed_variation"].mean().reset_index()
    df2 = copy.deepcopy(road_df)
    df2 = df2.merge(avg_changes, on=["name", "direction"], how="left")
    correct_num = 0
    total_num = 0
    for i in range(df2.shape[0]):
        if df2['speed_diff_percent'][i] and df2['speed_variation'][i]:
            total_num += 1
            if three_categories(df2['speed_diff_percent'][i]) == three_categories(df2['speed_variation'][i]):
                correct_num += 1
    acc = correct_num / total_num
    print(acc)
    print(correct_num)
    print(total_num)
    return acc
    


net = readNet(simulation_config['net_path'])
road_df = load_road_data(simulation_config['road_data_csv'])
df = match_edges_to_roads(net, road_df)
with open("simulation_results/scale_average_speeds_normal_0718.json", 'r') as fcc_file:
    normal_dict = json.load(fcc_file)
with open("simulation_results/scale_average_speeds_rain_0718.json", 'r') as fcc_file:
    rain_dict = json.load(fcc_file)
time_intervals = list(normal_dict['1'].keys())
param_combination = list(rain_dict.keys())
param_time_accuracy = {}
for param in param_combination:
    for time_ in time_intervals:
        accuracy = calculate_acc(df, road_df, normal_dict[param][time_], rain_dict[param][time_])
        param_time_accuracy[f"{param}_{time_}"] = accuracy 
with open("simulation_results/param_time_accuracy_scale_0718.json", "w") as f:
    json.dump(param_time_accuracy, f, indent=4)

# sorted_entries = sorted(param_time_accuracy.items(), key=lambda x: x[1], reverse=True)
# top_5_entries = dict(sorted_entries[:5])
# with open("simulation_results/top_5_param_time.json", "w") as f:
#     json.dump(top_5_entries, f, indent=4)
# print("Top 5 (param, time) by accuracy:")
# for (param_time, acc) in top_5_entries.items():
#     print(f"{param_time}: {acc:.4f}")