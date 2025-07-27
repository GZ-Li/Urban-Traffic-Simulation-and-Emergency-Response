import os
import traci
import sumolib
import pandas as pd
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


def modify_config_file(scale):
    tree = ET.parse("Core_500m_test_scale.sumocfg")
    root = tree.getroot()
    for elem in root.findall('input'):
        for route_elem in elem.findall('route-files'):
            route_elem.set('value', f"scale_rou\\routes_od_{int(scale*100)}.rou.xml")
    modified_config = "Core_500m_test_scale.sumocfg"
    tree.write(modified_config)
    return modified_config


def get_cleared_edges_lane(strategy):
    net = sumolib.net.readNet(NET_FILE)
    if strategy == "none":
        return []
    elif strategy == "three_lanes":
        return [e.getID() for e in net.getEdges() if e.getLaneNumber() >= 3]
    elif strategy == "two_lanes":
        return [e.getID() for e in net.getEdges() if e.getLaneNumber() >= 2]
    elif strategy == "all":
        return [e.getID() for e in net.getEdges()]
    

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
    if strategy == "top10":
        percentage = 0.1
    elif strategy == "top30":
        percentage = 0.3
    elif strategy == "top50":
        percentage = 0.5
    total_edges = len(sorted_edges)
    selected_num = int(total_edges * percentage)
    return [edge for edge, count in sorted_edges[:selected_num]]


# def get_junction_queue(junction_id):
#     junction_lanes = []
#     for edge in traci.junction.getIncomingEdges(junction_id):
#         for lane in traci.edge.getLaneIDs(edge):
#             junction_lanes.append(lane)
#     total_queued = 0
#     for lane_id in junction_lanes:
#         total_queued += traci.lane.getLastStepHaltingNumber(lane_id)
    
#     return total_queued


def run_simulation(scale, strategy):
    traci.start(["sumo", "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_rain.sumocfg"])
    cleared_edges = get_cleared_edges_lane(strategy)
    junction_ids = traci.junction.getIDList()
    metrics = {'congestion': 0, 'queue': 0, 'speed': 0}
    lane_ids = traci.lane.getIDList()
    while traci.simulation.getTime() <= 51:
        traci.simulationStep()
        for veh_id in traci.vehicle.getIDList():
            current_edge = traci.vehicle.getRoadID(veh_id)
            if current_edge in cleared_edges:
                traci.vehicle.setAcceleration(veh_id, 2.6, 1)
                traci.vehicle.setDecel(veh_id, 4.5)
                traci.vehicle.setMaxSpeed(veh_id, 30)
                traci.vehicle.setMinGap(veh_id, 2.5)
            else:
                traci.vehicle.setAcceleration(veh_id, 1.3, 1)
                traci.vehicle.setDecel(veh_id, 2.25)
                traci.vehicle.setMaxSpeed(veh_id, 15)
                traci.vehicle.setMinGap(veh_id, 5)
        if traci.simulation.getTime() == 50:
            congested_lanes = 0
            total_queue = 0
            for lane_id in lane_ids:
                queue = traci.lane.getLastStepHaltingNumber(lane_id)
                total_queue += queue
                if queue > 10:
                    congested_lanes += 1
            
            metrics['congestion_ratio'] = congested_lanes / len(lane_ids)
            metrics['avg_queue_length'] = total_queue / len(lane_ids)
            metrics['total_queued'] = total_queue
            metrics['avg_speed'] = sum(traci.vehicle.getSpeed(veh) for veh in traci.vehicle.getIDList()) / max(1, len(traci.vehicle.getIDList()))
    return {
        'scale': scale,
        'strategy': strategy,
        'congestion_ratio': congested_lanes / len(lane_ids),
        'avg_queue_length': total_queue / len(lane_ids),
        'avg_speed': sum(traci.vehicle.getSpeed(veh) for veh in traci.vehicle.getIDList()) / max(1, len(traci.vehicle.getIDList()))
    }


def plot_results(results):
    plt.figure(figsize=(15, 12))
    style = {
        "none": {"color": "red", "marker": "o", "label": "No Plowing"},
        "three_lanes": {"color": "blue", "marker": "s", "label": "three lanes"},
        "two_lanes": {"color": "green", "marker": "^", "label": "two lanes"},
        "all": {"color": "purple", "marker": "d", "label": "all roads"}
    }
    metrics = [
        ('congestion_ratio', 'Congestion Ratio', 'Ratio'),
        ('avg_queue_length', 'Average Queue Length', 'Meters'), 
        ('avg_speed', 'Average Speed', 'm/s')
    ]
    for i, (col, title, unit) in enumerate(metrics, 1):
        plt.subplot(3, 1, i)
        for strategy, group in results.groupby('strategy'):
            plt.plot(group['scale'], group[col], 
                    label=style[strategy]["label"],
                    color=style[strategy]["color"],
                    marker=style[strategy]["marker"],
                    linestyle='-')
        plt.title(title, fontsize=12)
        plt.xlabel('Scale', fontsize=10)
        plt.ylabel(unit, fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.legend()
    
    plt.tight_layout()
    # plt.savefig(os.path.join(OUTPUT_DIR, 'results.png'), dpi=300)
    plt.show()


if __name__ == "__main__":
    results = []
    for scale in [0.1, 0.2, 0.3, 0.4]:
        for strategy in STRATEGIES:
            results.append(run_simulation(scale, strategy))
            traci.close()
    results_df = pd.DataFrame(results)
    # results_df.to_csv(os.path.join(OUTPUT_DIR, 'results.csv'), index=False)
    plot_results(results_df)
    # print("实验完成！结果已保存到:", OUTPUT_DIR)