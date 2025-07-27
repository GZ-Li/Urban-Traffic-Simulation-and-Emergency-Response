import os
import re
import math
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
from shapely.wkt import loads


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
    matched_edges = []
    matched_regions = []
    mapping_dict = {}
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
                matched_edges.append(edge_id)
                matched_regions.append((road['name'], road['direction']))
                if (road['name'], road['direction']) in mapping_dict:
                    mapping_dict[(road['name'], road['direction'])].append(edge_id)
                else:
                    mapping_dict[(road['name'], road['direction'])] = [edge_id]
    print(len(set(matched_edges)))
    print(len(set(matched_regions)))
    return pd.DataFrame(matched_data), mapping_dict


def three_categories(percentage):
    if percentage > -10:
        return 1
    if percentage > -30 and percentage <= -10:
        return 2
    else:
        return 3
    
    
def calculate_acc(mapping_dict, road_df, test_dict_normal, test_dict_rain):
    average_speed_dict = {}
    acc_dataframe = []
    for k, v in mapping_dict.items():
        average_speed_dict[k] = []
        for edge in v:
            if test_dict_normal[edge] and test_dict_rain[edge] and test_dict_normal[edge]!=0:
                speed_variation = (test_dict_rain[edge] - test_dict_normal[edge]) * 100 / test_dict_normal[edge]
                average_speed_dict[k].append(speed_variation)
            if (test_dict_normal[edge] == 0) and (test_dict_rain[edge] == 0):
                speed_variation = 0
                average_speed_dict[k].append(speed_variation)
            if (test_dict_normal[edge] == 0) and (test_dict_rain[edge] != 0):
                speed_variation = 1
                average_speed_dict[k].append(speed_variation)
            if test_dict_normal[edge] and (test_dict_rain[edge] == None):
                speed_variation = (35 - test_dict_normal[edge]) * 100 / test_dict_normal[edge]
                average_speed_dict[k].append(speed_variation)
            if (test_dict_normal[edge] == None) and test_dict_rain[edge]:
                speed_variation = (test_dict_rain[edge] - 35) * 100 / 35
                average_speed_dict[k].append(speed_variation)
            if (test_dict_normal[edge] == None) and (test_dict_rain[edge] == None):
                speed_variation = 0
                average_speed_dict[k].append(speed_variation)
    for i in range(road_df.shape[0]):
        if ((road_df['name'][i], road_df['direction'][i]) in mapping_dict) and (len(average_speed_dict[(road_df['name'][i], road_df['direction'][i])]) > 0):
            temp_speed_variation = sum(average_speed_dict[(road_df['name'][i], road_df['direction'][i])]) / len(average_speed_dict[(road_df['name'][i], road_df['direction'][i])])
            acc_dataframe.append({"name": road_df['name'][i], "direction": road_df['direction'][i], "normal_speed": road_df['normal_speed'][i], "rainy_speed": road_df['rainy_speed'][i], "geometry": road_df['geometry'][i], "speed_diff_percent": road_df['speed_diff_percent'][i], "speed_variation": temp_speed_variation, "GT_category": three_categories(road_df['speed_diff_percent'][i]), "predict_category": three_categories(temp_speed_variation)})
    acc_dataframe = pd.DataFrame(acc_dataframe)
    correct_num = 0
    total_num = 0
    for i in range(acc_dataframe.shape[0]):
        if acc_dataframe['GT_category'][i] != 1:
            total_num += 1
            if acc_dataframe['predict_category'][i] == acc_dataframe['GT_category'][i]:
                correct_num += 1
    print(total_num)
    acc = correct_num / total_num
    return acc, acc_dataframe
                  




# def calculate_acc(df, road_df, test_dict_normal, test_dict_rain):
#     speed_variation = []
#     for road_id in df['edge_id']:
#         speed1 = test_dict_normal[road_id]
#         speed2 = test_dict_rain[road_id]
#         if (not math.isnan(speed1)) and (not math.isnan(speed2)) and speed1 != 0:
#             variation = (speed2 - speed1) / (speed1)
#             speed_variation.append(variation)
#         else:
#             speed_variation.append(None)
#     df['speed_variation'] = speed_variation
#     avg_changes = df.groupby(["name", "direction"])["speed_variation"].mean().reset_index()
#     df2 = copy.deepcopy(road_df)
#     df2 = df2.merge(avg_changes, on=["name", "direction"], how="left")
#     correct_num = 0
#     total_num = 0
#     for i in range(df2.shape[0]):
#         if (not math.isnan(df2['speed_diff_percent'][i])):
#             total_num += 1
#             print(df2["speed_diff_percent"][i])
#             print(df2["speed_variation"][i])
#             if three_categories(df2['speed_diff_percent'][i]) == three_categories(df2['speed_variation'][i]):
#                 correct_num += 1
#     acc = correct_num / total_num
#     print(acc)
#     print(correct_num)
#     print(total_num)
#     return acc

# def calculate_acc(df, road_df, test_dict_normal, test_dict_rain):
#     speed_variation = []
#     valid_indices = []
#     for idx, road_id in enumerate(df['edge_id']):
#         speed1 = test_dict_normal[road_id]
#         speed2 = test_dict_rain[road_id]
#         if speed1 and speed2 and speed1 != 0:
#             variation = (speed2 - speed1) / speed1
#             speed_variation.append(variation)
#             valid_indices.append(idx)
#     temp_df = df.iloc[valid_indices].copy()
#     temp_df['speed_variation'] = speed_variation
#     avg_changes = temp_df.groupby(["name", "direction"])["speed_variation"].mean().reset_index()
#     df2 = copy.deepcopy(road_df)
#     df2 = df2.merge(avg_changes, on=["name", "direction"], how="left")
#     correct_num = 0
#     total_num = 0
    
#     for i in range(df2.shape[0]):
#         if not math.isnan(df2['speed_diff_percent'][i]):
#             total_num += 1
#             if three_categories(df2['speed_diff_percent'][i]) == three_categories(df2['speed_variation'][i]):
#                 correct_num += 1
    
#     acc = correct_num / total_num if total_num > 0 else 0
#     return acc


def calculate_recall_category3(df, road_df, test_dict_normal, test_dict_rain):
    speed_variation = []
    for road_id in df['edge_id']:
        speed1 = test_dict_normal[road_id]
        speed2 = test_dict_rain[road_id]
        if speed1 and speed2 and speed1 != 0:
            variation = (speed2 - speed1) / speed1
            speed_variation.append(variation)
        else:
            speed_variation.append(None)
    df['speed_variation'] = speed_variation
    avg_changes = df.groupby(["name", "direction"])["speed_variation"].mean().reset_index()
    df2 = copy.deepcopy(road_df)
    df2 = df2.merge(avg_changes, on=["name", "direction"], how="left")

    correct_category3 = 0
    actual_category3_total = 0

    for i in range(df2.shape[0]):
        if df2['speed_diff_percent'][i] and df2['speed_variation'][i]:
            actual_category = three_categories(df2['speed_variation'][i])
            predicted_category = three_categories(df2['speed_diff_percent'][i])
            
            if actual_category == 3:  # 实际是 category=3
                actual_category3_total += 1
                if predicted_category == 3:  # 预测正确
                    correct_category3 += 1

    recall_category3 = correct_category3 / actual_category3_total if actual_category3_total > 0 else 0
    print(f"Recall for Category 3: {recall_category3:.4f}")
    print(f"Correct Category 3 Predictions: {correct_category3}")
    print(f"Total Actual Category 3 Cases: {actual_category3_total}")
    return recall_category3


net = readNet(simulation_config['net_path'])
road_df = load_road_data(simulation_config['road_data_csv'])
df, mapping_dict = match_edges_to_roads(net, road_df)
print(road_df)
with open("E:\\Traffic_Simulation\\Adverse_weather_traffic\\simulation_results\\rain_average_speeds_0720_test_scale.json", 'r') as fcc_file:
    rain_dict = json.load(fcc_file)
with open("E:\\Traffic_Simulation\\Adverse_weather_traffic\\simulation_results\\normal_average_speeds_0720_test_scale.json", 'r') as fcc_file:
    normal_dict = json.load(fcc_file)
accuracy, df_ = calculate_acc(mapping_dict, road_df, normal_dict['10000'], rain_dict['1.0_3.0_24_5.0']['10000'])
print(set(list(df_['predict_category'])))
print(df_.shape)
print(mapping_dict)

def extract_coordinates_shapely(wkt):
    line = loads(wkt) 
    return list(line.coords) 

arcmap_df = []
arcmap_df_index = 0
pred_lookup = {(row['name'], row['direction']): row for _, row in df_.iterrows()}
for i in range(road_df.shape[0]):
    test_row = road_df.iloc[i]
    if (test_row['name'], test_row['direction']) in mapping_dict:
        pred_row = pred_lookup[(test_row['name'], test_row['direction'])]
        line_coords = extract_coordinates_shapely(test_row['geometry'])
        for l in line_coords:
            temp_dict = {"id": arcmap_df_index, "roadname": test_row['name'], "direction": test_row['direction'], "status": three_categories(pred_row['speed_variation']), "speeddiff": pred_row['speed_variation'], "roadID": i, "x": l[0], "y": l[1]}
            arcmap_df.append(temp_dict)
            arcmap_df_index += 1
    else:
        line_coords = extract_coordinates_shapely(test_row['geometry'])
        for l in line_coords:
            temp_dict = {"id": arcmap_df_index, "roadname": test_row['name'], "direction": test_row['direction'], "status": three_categories(test_row['speed_diff_percent']), "speeddiff": test_row['speed_diff_percent'], "roadID": i, "x": l[0], "y": l[1]}
            arcmap_df.append(temp_dict)
            arcmap_df_index += 1
arcmap_df = pd.DataFrame(arcmap_df)
print(arcmap_df.shape)
arcmap_df.to_csv('predict_diff_0718_scale_adjustment2.csv', encoding='utf-8', index=False) 



# arcmap_df = []
# arcmap_df_index = 0
# for i in range(df_.shape[0]):
#     test_row = df_.iloc[i]
#     line_coords = extract_coordinates_shapely(test_row['geometry'])
#     for l in line_coords:
#         temp_dict = {"id": arcmap_df_index, "roadname": test_row['name'], "direction": test_row['direction'], "status": test_row['predict_category'], "speeddiff": test_row['speed_variation'], "roadID": i, "x": l[0], "y": l[1]}
#         arcmap_df.append(temp_dict)
#         arcmap_df_index += 1
# arcmap_df = pd.DataFrame(arcmap_df)
# print(arcmap_df.shape)
# arcmap_df.to_csv('predict_diff_0718_scale.csv', encoding='utf-8', index=False) 