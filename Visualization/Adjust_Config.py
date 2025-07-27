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
    
modify_vehicle_xml("E:\\Traffic_Simulation\\Adverse_weather_traffic\\full_rou\\mapall_addline_rain.rou.xml", "rou\\visual_full.rou.xml", accel="1.5", decel="3.0", maxSpeed="20", minGap="4.0")