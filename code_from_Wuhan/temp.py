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
    "pb_map_path": "data/",
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


def adapt_mapping_dict(pb_map_path):
    map = Map()
    with open("E:\\Traffic_Simulation\\code_from_Wuhan\\map_07311617.pb", "rb") as f:
        map.ParseFromString(f.read())
    map2 = pb2json(map)
    with open(f"data\\{pb_map_path.split(".")[0]}.json", "w", encoding="utf-8") as f:
        json.dump(json.loads(map2), f, indent=2, ensure_ascii=False)
    

    
    

    
net = readNet(simulation_config['net_path'])
road_df = load_road_data(simulation_config['road_data_csv'])
df, mapping_dict = match_edges_to_roads(net, road_df)
recall_factor = (2/3)