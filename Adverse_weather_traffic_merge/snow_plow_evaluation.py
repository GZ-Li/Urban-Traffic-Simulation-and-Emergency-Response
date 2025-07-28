import os
import json
import traci
import random
import time
import sumolib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from collections import defaultdict


NET_FILE = "net\\core_withshape_with_light_changing.net.xml"
Lanenum_STRATEGIES = {
    "none": "clean no roads",
    "three_lanes": "clean roads with 3 or more lanes",
    "two_lanes": "clean roads with 2 or more lanes",
    "one_lane": "clean roads with only 1 lane",
    "all": "clean all roads"
}
Demand_STRATEGY = {
    "none": "clear no roads",
    "top20": "clean top20 percent demand roads",
    "top50": "clean top 50 percent demand roads",
    "top 80": "clean top 80 percent demand roads",
    "all": "clean all roads"
}



def get_cleared_edges_lane(strategy, sample_num = 500):
    net = sumolib.net.readNet(NET_FILE)
    if strategy == "none":
        return []
    elif strategy == "three_lanes":
        edges = [e.getID() for e in net.getEdges() if e.getLaneNumber() >= 3]
        sampled_edges = random.sample(edges, sample_num)
        return sampled_edges
    elif strategy == "two_lanes":
        edges = [e.getID() for e in net.getEdges() if e.getLaneNumber() == 2]
        sampled_edges = random.sample(edges, sample_num)
        return sampled_edges
    elif strategy == "one_lane":
        edges = [e.getID() for e in net.getEdges() if e.getLaneNumber() < 2]
        sampled_edges = random.sample(edges, sample_num)
        return sampled_edges
    elif strategy == "all":
        edges = [e.getID() for e in net.getEdges()]
        sampled_edges = random.sample(edges, sample_num)
        return sampled_edges
    


def get_cleared_edges_lane_Parlato(percent):
    net = sumolib.net.readNet(NET_FILE)
    edges = [(e.getID(), e.getLaneNumber()) for e in net.getEdges()]
    sorted_edges = sorted(edges, key=lambda x: x[1], reverse=True)
    edge_num = len(sorted_edges)
    sorted_edge_lst = [edge[0] for edge in sorted_edges]
    return sorted_edge_lst[:int(edge_num*percent)]

    

def get_cleared_edges_demand(strategy, route_file):
    edge_counts = defaultdict(int)
    tree = ET.parse(route_file)
    root = tree.getroot()
    for vehicle in root.findall('.//vehicle'):
        route = vehicle.find('route')
        if route is not None and 'edges' in route.attrib:
            edges = route.attrib['edges'].split()
            for edge in edges:
                edge_counts[edge] += 1
    sorted_edges = sorted(edge_counts.items(), key=lambda x: x[1], reverse=True)
    total_edges = len(sorted_edges)
    get_num = int(total_edges * 0.2)
    if strategy == "top20":
        return [edge for edge, count in sorted_edges[:get_num]]
    if strategy == "top50":
        return [edge for edge, count in sorted_edges[int(0.5*total_edges)-get_num-1:int(0.5*total_edges)-1]]
    if strategy == "top80":
        return [edge for edge, count in sorted_edges[int(0.8*total_edges)-get_num-1:int(0.8*total_edges)-1]]
    if strategy == "all":
        return [edge for edge, count in sorted_edges]
    if strategy == "none":
        return []

    
    
def get_cleared_edges_demand_Parlato(percent, route_file):
    edge_counts = defaultdict(int)
    tree = ET.parse(route_file)
    root = tree.getroot()
    for vehicle in root.findall('.//vehicle'):
        route = vehicle.find('route')
        if route is not None and 'edges' in route.attrib:
            edges = route.attrib['edges'].split()
            for edge in edges:
                edge_counts[edge] += 1
    sorted_edges = sorted(edge_counts.items(), key=lambda x: x[1], reverse=True)
    total_edges = len(sorted_edges)
    get_num = int(total_edges * percent)
    return [edge for edge, count in sorted_edges[:get_num]]



def run_simulation(strategy, obs = "lanenum"): #["lanenum, demand"]
    res = {}
    traci.start(["sumo", "-c", "Core_500m_test.sumocfg"])
    if obs == "lanenum":
        cleared_edges = get_cleared_edges_lane(strategy)
    if obs == "demand":
        cleared_edges = get_cleared_edges_demand(strategy, "rou\\mapcore_500m_core_withshape_with_light_test_normal.rou.xml")
    lane_ids = traci.lane.getIDList()
    last_saved_count = 3000
    while len(traci.vehicle.getIDList()) <=12000:
        traci.simulationStep()
        current_vehicles = traci.vehicle.getIDList()
        current_count = len(current_vehicles)
        for veh_id in traci.vehicle.getIDList():
            current_edge = traci.vehicle.getRoadID(veh_id)
            if current_edge in cleared_edges:
                traci.vehicle.setAcceleration(veh_id, 2.6, 1)
                traci.vehicle.setDecel(veh_id, 4.5)
                traci.vehicle.setMaxSpeed(veh_id, 33)
                traci.vehicle.setMinGap(veh_id, 2.5)
            else:
                traci.vehicle.setAcceleration(veh_id, 1.5, 1)
                traci.vehicle.setDecel(veh_id, 2.5)
                traci.vehicle.setMaxSpeed(veh_id, 20)
                traci.vehicle.setMinGap(veh_id, 4)
        if (current_count >= 3000) and (current_count - last_saved_count >= 1000):
            congested_lanes = 0
            lane_total_queue = 0
            last_saved_count = current_count
            for lane_id in lane_ids:
                lane_queue = traci.lane.getLastStepHaltingNumber(lane_id)
                lane_total_queue += lane_queue
                if lane_queue > 10:
                    congested_lanes += 1
            lane_cong_ratio = congested_lanes / len(lane_ids)
            lane_avg_queue_len = lane_total_queue / len(lane_ids)
            global_avg_speed = sum(traci.vehicle.getSpeed(veh) for veh in traci.vehicle.getIDList()) / max(1, len(traci.vehicle.getIDList()))
    
            junction_metrics = {}
            junction_ids = traci.junction.getIDList()
            global_total_queue = 0
            global_total_speed = 0
            global_vehicle_count = 0

            for junction_id in junction_ids:
                inc_edges = traci.junction.getIncomingEdges(junction_id)
                total_queue = 0
                total_speed = 0
                lane_count = 0
                vehicle_count = 0
                for edge_id in inc_edges:
                    lane_num = traci.edge.getLaneNumber(edge_id)
                    temp_lane_lst = []
                    for t in range(lane_num):
                        temp_lane_lst.append(f"{edge_id}_{t}")
                    for lane_id in temp_lane_lst:
                        queue = traci.lane.getLastStepHaltingNumber(lane_id)
                        total_queue += queue
                        lane_count += 1
                        vehicles = traci.lane.getLastStepVehicleIDs(lane_id)
                        for veh_id in vehicles:
                            speed = traci.vehicle.getSpeed(veh_id)
                            total_speed += speed
                            vehicle_count += 1
                avg_queue = total_queue / lane_count if lane_count > 0 else 0
                avg_speed = total_speed / vehicle_count if vehicle_count > 0 else 35
                junction_metrics[junction_id] = {
                            "avg_queue": avg_queue,
                            "avg_speed": avg_speed,
                            "total_queue": total_queue,
                            "is_congested": avg_queue > 10 or avg_speed < 5  # 自定义拥堵标准
                        }
            
            total_junctions = len(junction_ids)
            congested_junctions = sum(1 for metrics in junction_metrics.values() if metrics["is_congested"])
            junction_cong_ratio = congested_junctions / total_junctions if total_junctions > 0 else 0
            sum_junction_len = 0
            sum_junction_speed = 0
            for k, v in junction_metrics.items():
                sum_junction_len += v['total_queue']
                sum_junction_speed += v['avg_speed']
            junction_avg_queue_len = sum_junction_len / total_junctions
            junction_avg_speed = sum_junction_speed / total_junctions
            print(junction_avg_queue_len)
            res[int(current_count / 1000)*1000] = [lane_avg_queue_len, global_avg_speed, junction_cong_ratio]
            print(res)
    return res



if __name__ == "__main__":
    results = {}
    for strategy in list(Lanenum_STRATEGIES.keys()):
        start_time = time.time()
        results[strategy] = run_simulation(strategy, obs = "lanenum")
        end_time = time.time()
        traci.close()
        print(end_time - start_time)
        with open('snowplow_res_lanenum.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
    with open('snowplow_res_lanenum.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)