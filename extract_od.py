import xml.etree.ElementTree as ET
from collections import defaultdict
import math

def extract_od_matrix(rou_file):
    tree = ET.parse(rou_file)
    root = tree.getroot()
    od_counts = defaultdict(int)
    nodes = set()
    for vehicle in root.findall('vehicle'):
        route = vehicle.find('route')
        if route is not None:
            edges = route.get('edges').split()
            if len(edges) >= 2:
                origin = edges[0]
                destination = edges[-1]
                od_counts[(origin, destination)] += 1
                
    return od_counts

def normalize_to_min_one(od_counts):
    min_count = min(value for value in od_counts.values() if value > 0)
    scaling_factor = 1.0 / min_count
    normalized_od = {
        od: max(1, round(count * scaling_factor))
        for od, count in od_counts.items()
    }
    return normalized_od

def process_sumo_od(rou_file):
    od_matrix = extract_od_matrix(rou_file)
    normalized_matrix = normalize_to_min_one(od_matrix)
    return normalized_matrix

if __name__ == "__main__":
    rou_file = "E:\\Traffic_Simulation\\Adverse_weather_traffic_merge\\rou\\mapcore_500m_core_withshape_with_light_test.rou.xml"
    od_matrix = process_sumo_od(rou_file)
    print(od_matrix)
    # print("OD Matrix (normalized to min=1):")
    # for (origin, destination), count in sorted(od_matrix.items()):
    #     print(f"From {origin} to {destination}: {count}")