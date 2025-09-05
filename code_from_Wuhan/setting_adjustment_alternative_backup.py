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
import numpy as np
from collections import defaultdict
from google.protobuf import json_format
from google.protobuf.message import Message
from pycityproto.city.map.v2.map_pb2 import Map
from pycityproto.city.person.v2.person_pb2 import Persons, Person


simulation_config = {
    "net_path": "data/Full_map.net.xml",
    "pb_map_path": "data/map_pku_wuhan_demo_1015c.pb",
    "road_data_csv": "data/actual_speed_variation.csv",
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
    return pd.DataFrame(matched_data), mapping_dict


def three_categories(percentage):
    if percentage > -10:
        return 1
    if percentage > -40 and percentage <= -10:
        return 2
    else:
        return 3


def pb2json(pb: Message):
    """
    Convert a protobuf message to a JSON string.

    Args:
    - pb: The protobuf message to be converted.

    Returns:
    - The JSON string.
    """
    return json_format.MessageToJson(
        pb,
        including_default_value_fields=True,
        preserving_proto_field_name=True,
        use_integers_for_enums=True,
    )


def adapt_mapping_dict(pb_map_path, mapping_dict = None):
    map = Map()
    new_mapping_dict = {}
    with open(pb_map_path, "rb") as f:
        map.ParseFromString(f.read())
    map2 = pb2json(map)
    with open(f"{pb_map_path.split('.')[0]}.json", "w", encoding="utf-8") as f:
        json.dump(json.loads(map2), f, indent=2, ensure_ascii=False)
    map2 = json.loads(map2)
    road_lst = []
    for element in map2['roads']:
        road_lst.append(str(element['id']))
    for k, v in mapping_dict.items():
        temp_lst = []
        for r in v:
            if str(r) in road_lst:
                temp_lst.append(str(r))
        if len(temp_lst) > 0:
            new_mapping_dict[k] = temp_lst
    return new_mapping_dict


def calculate_acc(road_df, normal_speed, rain_speed): # road_df包括normal和rain情况下的速度信息；
    road_df2 = copy.deepcopy(road_df)
    road_df2['normal_speed'] = normal_speed
    road_df2['rain_speed'] = rain_speed
    effect_percent = []
    GT_category = []
    simu_category = []
    for i in range(road_df2.shape[0]):
        temp_percent = (road_df2['rain_speed'][i] - road_df2['normal_speed'][i]) / road_df2['normal_speed'][i]
        effect_percent.append(temp_percent)
        GT_category.append(three_categories(road_df2['speed_diff_percent'][i]))
        simu_category.append(three_categories(temp_percent))
    road_df2['simu_diff_percent'] = effect_percent
    road_df2['GT_category'] = GT_category
    road_df2['simu_category'] = simu_category
    total_count_1 = 0
    correct_count_1 = 0
    total_count_2 = 0
    correct_count_2 = 0
    print(road_df2)
    for i in range(road_df2.shape[0]):
        total_count_2 += 1
        if road_df2['GT_category'][i] != 1:
            total_count_1 += 1
            if road_df2['GT_category'][i] == road_df2['simu_category'][i]:
                correct_count_1 += 1
        if road_df2['GT_category'][i] == road_df2['simu_category'][i]:
            correct_count_2 += 1
        acc1 = correct_count_1 / total_count_1
        acc2 = correct_count_2 / total_count_2
    return acc1, acc2
    

# 计算指定id的road上面车辆的平均速度   
# def get_average_speed(road_id):
#     return average_speed (a float)

    
net = readNet(simulation_config['net_path'])
road_df = load_road_data(simulation_config['road_data_csv'])
df, ori_mapping_dict = match_edges_to_roads(net, road_df)
print(road_df)
mapping_dict = adapt_mapping_dict(simulation_config['pb_map_path'], ori_mapping_dict)
    
# # # 启动正常天气运行
# # # =====================================
# import argparse
# import json
# import os
# import sys
# import time
# from typing import Optional, Tuple

# from engine import get_engine


# class Env:
#     def __init__(
#         self,
#         mongo_uri: str,
#         map_db: str,
#         map_coll: str,
#         agent_db: str,
#         agent_coll: str,
#         start_step,
#         step_size,
#         step_count,
#         log_dir,
#         reward,
#         output_sql_dsn: str = "",
#         output_job_prefix: str = "traffic_light_optimization_",
#         output_bbox: Optional[Tuple[float, float, float, float]] = None,
#     ):
#         self.log_dir = log_dir
#         self.eng = get_engine(
#             mongo_uri=mongo_uri,
#             map_db=map_db,
#             map_coll=map_coll,
#             agent_db=agent_db,
#             agent_coll=agent_coll,
#             start_step=start_step,
#             total_step=(step_count + 1) * step_size,
#             use_max_pressure=True,
#             output_sql_dsn=output_sql_dsn,
#             output_job_prefix=output_job_prefix,
#             output_bbox=output_bbox,
#         )

#         self.step_size = step_size
#         self.step_count = step_count
#         self._step = 0
#         self.reward = reward
#         self.info = {
#             "ATT": 1e999,
#             "Throughput": 0,
#             "reward": 0,
#             "ATT_inside": 1e999,
#             "ATT_finished": 1e999,
#             "Throughput_inside": 0,
#         }

#     async def test(self):
#         lanes = await self.eng.get_lanes()

#         for lane in lanes:
#             print(f"lane id:{lane}")

#         roads = await self.eng.get_roads()

#         for road in roads:
#             avg_v = await self.eng.get_road_avg_v(road)
#             lanes_id = await self.eng.get_lane_id_of_road(road)
#             vehicles = await self.eng.get_vehicle_ids_of_road(road)
#             for vehicle in vehicles:
#                 pos = await self.eng.get_vehicle_pos(vehicle)
#                 v = await self.eng.get_vehicle_speed(vehicle)
#                 road_id = await self.eng.get_road_id_with_vehicle(vehicle)
#                 lane_id = await self.eng.get_lane_id_with_vehicle(vehicle)
#                 if lane_id != None:
#                     await self.eng.set_vehicle_acc(vehicle, 10)
#                     await self.eng.set_max_vehicle_speed(vehicle, 50)
#                 print(f"vehicle id:{vehicle}, pos:{pos},v:{v}")
#             print(f"road id:{road}, avg_v:{avg_v}")

#     def reset(self):
#         # 重启环境
#         self.eng._stop_simulator()
#         self.eng._start_simulator()

#     async def step(self):
#         await self.test()
#         self.eng.next_step(self.step_size)

#         self._step += 1
#         done = False
#         if self._step >= self.step_count:
#             self.info["ATT"] = (
#                 await self.eng.get_departed_vehicle_average_traveling_time()
#             )
#             self.info["ATT_finished"] = (
#                 await self.eng.get_finished_vehicle_average_traveling_time()
#             )
#             self.info["Throughput"] = await self.eng.get_finished_vehicle_count()
#             self._step = 0
#             done = True
#             with open(f"{self.log_dir}/info.log", "a") as f:
#                 f.write(
#                     f"{self.info['ATT']:.3f} {self.info['Throughput']} {time.time():.3f}\n"
#                 )
#         return done, self.info

# # # =====================================

# # ======================================
# # 指定id的road上面的车辆的平均速度
# speed_lst = []
# if time_step % 100 == 0:
#     for k, v in mapping_dict.items():
#         temp_lst = []
#         for road_id in v:
#             temp_lst.append(get_average_speed(road_id))
#             speed_lst.append(sum(temp_lst) / len(temp_lst))
# road_df['normal_speed'] = speed_lst
# # =======================================
with open("data/normal_simulation_speed_record.json", "r", encoding="utf-8") as f:
    normal_data = json.load(f)


# # # 启动雨天天气运行
# # # =====================================


# # # =====================================

# # ======================================
# # 指定id的road上面的车辆的平均速度
# speed_lst = []
# if time_step % 100 == 0:
#     for k, v in mapping_dict.items():
#         temp_lst = []
#         for road_id in v:
#             temp_lst.append(get_average_speed(road_id))
#             speed_lst.append(sum(temp_lst) / len(temp_lst))
# road_df['rain_speed'] = speed_lst
# # =======================================
with open("data/rain_simulation_speed_record.json", "r", encoding="utf-8") as f:
    rain_data = json.load(f)

time_params = list(normal_data.keys())
setting_params = []
for k in list(rain_data.keys()):
    setting_params.append(k.split("|")[0])
setting_params = list(set(setting_params))

print(calculate_acc(road_df, normal_data["10000"], rain_data["1.0_2.0_16_3.0|10000"]))