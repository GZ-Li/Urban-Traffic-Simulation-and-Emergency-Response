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


NET_FILE = "D:\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml"
# BASE_CONFIG = "Core_500m_test_scale.sumocfg"
# OUTPUT_DIR = "output"


# SCALES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
STRATEGIES = {
    "none": "clean no roads",
    "three_lanes": "clean roads with 3 or more lanes",
    "two_lanes": "clean roads with 2 or more lanes",
    "all": "clean all roads"
}



Demand_STRATEGY = {
    "none": "clear no roads",
    "top20": "clean top20 percent demand roads",
    "top50": "clean top 50 percent demand roads",
    "top 80": "clean top 80 percent demand roads",
    "all": "clean all roads"
}



# def modify_config_file(scale):
#     tree = ET.parse("Core_500m_test_scale.sumocfg")
#     root = tree.getroot()
#     for elem in root.findall('input'):
#         for route_elem in elem.findall('route-files'):
#             route_elem.set('value', f"scale_rou\\routes_od_{int(scale*100)}.rou.xml")
#     modified_config = "Core_500m_test_scale.sumocfg"
#     tree.write(modified_config)
#     return modified_config


def get_cleared_edges_lane(strategy):
    net = sumolib.net.readNet(NET_FILE)
    if strategy == "none":
        return []
    elif strategy == "three_lanes":
        edges = [e.getID() for e in net.getEdges() if e.getLaneNumber() >= 3]
        sampled_edges = random.sample(edges, 500)
        print(len(edges))
        return sampled_edges
    elif strategy == "two_lanes":
        edges = [e.getID() for e in net.getEdges() if e.getLaneNumber() == 2]
        sampled_edges = random.sample(edges, 500)
        print(len(edges))
        return sampled_edges
    elif strategy == "one_lane":
        edges = [e.getID() for e in net.getEdges() if e.getLaneNumber() < 2]
        print(len(edges))
        sampled_edges = random.sample(edges, 500)
        return sampled_edges
    elif strategy == "all":
        edges = [e.getID() for e in net.getEdges()]
        sampled_edges = random.sample(edges, 500)
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
    # if strategy == "top10":
    #     percentage = 0.1
    # elif strategy == "top30":
    #     percentage = 0.3
    # elif strategy == "top50":
    #     percentage = 0.5
    # total_edges = len(sorted_edges)
    # selected_num = int(total_edges * percentage)
    # return [edge for edge, count in sorted_edges[:selected_num]]
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
    


# def get_junction_queue(junction_id):
#     junction_lanes = []
#     for edge in traci.junction.getIncomingEdges(junction_id):
#         for lane in traci.edge.getLaneIDs(edge):
#             junction_lanes.append(lane)
#     total_queued = 0
#     for lane_id in junction_lanes:
#         total_queued += traci.lane.getLastStepHaltingNumber(lane_id)
    
#     return total_queued


def run_simulation(strategy):
    res = {}
    traci.start(["sumo", "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test.sumocfg"])
    cleared_edges = get_cleared_edges_lane(strategy)
    # print(cleared_edges)
    # cleared_edges = get_cleared_edges_demand(strategy, "E:\\Traffic_Simulation\\Adverse_weather_traffic\\rou\\mapcore_500m_core_withshape_with_light_test_normal.rou.xml")
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
            res[int(current_count / 1000)*1000] = [lane_cong_ratio, lane_avg_queue_len, global_avg_speed, junction_cong_ratio, junction_avg_queue_len, junction_avg_speed]
            print(res)
    return res


# def plot_strategy_comparison(all_results):
#     metrics = [
#         ('congestion_ratio', 'cong_ratio'),
#         ('average_queue_length', 'avg_queue_len'), 
#         ('average_speed', 'avg_speed')
#     ]
#     plt.figure(figsize=(15, 10))
#     for idx, (title, metric_key) in enumerate(metrics, 1):
#         plt.subplot(3, 1, idx)       
#         for strategy, res in all_results.items():
#             df = pd.DataFrame.from_dict(res, orient='index', 
#                                       columns=['cong_ratio', 'avg_queue_len', 'avg_speed'])
#             df.index.name = 'vehicle_count'
#             df.reset_index(inplace=True)
            
#             plt.plot(df['vehicle_count'], df[metric_key], 
#                     label=strategy,
#                     marker='o',
#                     linestyle='-')
#         plt.title(title)
#         plt.xlabel('#Vehicles')
#         plt.ylabel(title)
#         plt.xticks(range(0, 12001, 1000))  # 固定x轴刻度为整千
#         plt.grid(True)
#         plt.legend()  
#     plt.tight_layout()
#     plt.savefig('strategy_comparison.png')
#     plt.show()


import matplotlib.pyplot as plt
from collections import defaultdict

def plot_strategy_metrics(strategies):
    # 定义指标名称
    metric_names = [
        "lane_cong_ratio", "lane_avg_queue_len", "global_avg_speed", "junction_cong_ratio", "junction_avg_queue_len", "junction_avg_speed"
    ]
    
    # 整理数据
    metrics_data = {name: defaultdict(dict) for name in metric_names}
    for strategy, res in strategies.items():
        for step, values in res.items():
            for i, name in enumerate(metric_names):
                metrics_data[name][step][strategy] = values[i]
    
    # 绘制每个指标的对比图
    plt.style.use('seaborn')
    for metric_name, data in metrics_data.items():
        plt.figure(figsize=(10, 6))
        steps = sorted(data.keys())
        
        for strategy in strategies.keys():
            y_values = [data[step].get(strategy, 0) for step in steps]  # 处理可能的缺失值
            plt.plot(steps, y_values, label=strategy, marker='o', linestyle='-')
        
        plt.title(f"{metric_name}", fontsize=14)
        plt.xlabel("#vehicles", fontsize=12)
        plt.ylabel(metric_name, fontsize=12)
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{metric_name}.png", dpi=300, bbox_inches='tight')
        plt.show()


if __name__ == "__main__":
    results = {}
    for strategy in ["two_lanes"]:
        start_time = time.time()
        results[strategy] = run_simulation(strategy)
        end_time = time.time()
        traci.close()
        print(end_time - start_time)
    #     with open('snowplow_res_numlane_supplementonelane.json', 'w', encoding='utf-8') as f:
    #         json.dump(results, f, indent=4, ensure_ascii=False)
    # print(results)
    # with open('snowplow_res_numlane_supplementonelane.json', 'w', encoding='utf-8') as f:
    #     json.dump(results, f, indent=4, ensure_ascii=False)
    # plot_strategy_metrics(results)
    # cleared_edges = get_cleared_edges_lane("three_lanes")