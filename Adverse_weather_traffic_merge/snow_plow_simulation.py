import traci
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sumolib
import traci
import folium
from branca.colormap import LinearColormap
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# 配置路径
CONFIG_FILE = "Core_500m_test_scale.sumocfg"

def run_snowplow_simulation():
    
    cleared_edges = set()
    max_steps = 450
    
    # snowplow_routes_1 = "200014261 200025126 200015069 200015067 200025154 200007033 200001532 200001528 200020476 200020477 200021947"
    snowplow_routes_1 = "200015067 200025154 200007033 200001532 200001590 200001586"
    snowplow_routes_2 = "200025155 200015066 200015032"
    snowplow_routes_3 = "200060659 200060651 200080654"
    snowplow_maxspeed = 10
    
    tree = ET.parse("rou\\routes_od_4_snow.rou.xml") 
    root = tree.getroot()
    vtype = ET.Element('vType', {
        'id': "snowplow",
        'vClass': "truck",
        'maxSpeed': "5",
    })
    root.insert(0, vtype)
    vehicle = ET.Element('vehicle', {
        'id': "snowplow_1",
        'type': "snowplow",
        'depart': '0.00',
        'color': "0,0,1"
    })
    ET.SubElement(vehicle, 'route', {
            'edges': snowplow_routes_1
        })
    root.insert(1, vehicle)
    vehicle = ET.Element('vehicle', {
        'id': "snowplow_2",
        'type': "snowplow",
        'depart': '0.00',
        'color': "0,0,1"
    })
    ET.SubElement(vehicle, 'route', {
            'edges': snowplow_routes_2
        })
    root.insert(2, vehicle)
    vehicle = ET.Element('vehicle', {
        'id': "snowplow_3",
        'type': "snowplow",
        'depart': '0.00',
        'color': "0,0,1"
    })
    ET.SubElement(vehicle, 'route', {
            'edges': snowplow_routes_3
        })
    root.insert(3, vehicle)
            
    tree.write("rou/routes_od_4_snowplow.rou.xml", encoding='utf-8', xml_declaration=True)
    traci.start(["sumo-gui", "-c", CONFIG_FILE, "--start"])


    # 主仿真循环
    for step in range(max_steps):
        traci.simulationStep()
        if ("snowplow_1" in traci.vehicle.getIDList()):
            print("snowplow_1")
        if ("snowplow_2" in traci.vehicle.getIDList()):
            print("snowplow_2")
        if ("snowplow_3" in traci.vehicle.getIDList()):
            print("snowplow_3")
        
        # 记录扫雪车当前位置
        if ("snowplow_1" in traci.vehicle.getIDList()):
            current_edge_1 = traci.vehicle.getRoadID("snowplow_1")
            if current_edge_1 not in cleared_edges:
                cleared_edges.add(current_edge_1)
        if ("snowplow_2" in traci.vehicle.getIDList()):
            current_edge_2 = traci.vehicle.getRoadID("snowplow_2")
            if current_edge_2 not in cleared_edges:
                cleared_edges.add(current_edge_2)
        if ("snowplow_3" in traci.vehicle.getIDList()):
            current_edge_3 = traci.vehicle.getRoadID("snowplow_3")
            if current_edge_3 not in cleared_edges:
                cleared_edges.add(current_edge_3)
        
        # 动态调整车辆速度
        for veh_id in traci.vehicle.getIDList():
            edge = traci.vehicle.getRoadID(veh_id)
            if (edge in cleared_edges) and edge not in [current_edge_1, current_edge_2, current_edge_3]:
                traci.vehicle.setMaxSpeed(veh_id, 30)  # 已清扫道路提速
                traci.vehicle.setMinGap(veh_id, 2.5)
                if veh_id not in ["snowplow_1", "snowplow_2", "snowplow_3"]:  # 不影响扫雪车自身
                    traci.vehicle.setColor(veh_id, (180, 230, 255))  # 浅蓝色
            else:
                traci.vehicle.setMaxSpeed(veh_id, 10) 
                traci.vehicle.setMinGap(veh_id, 5)
                if veh_id not in ["snowplow_1", "snowplow_2", "snowplow_3"]:  # 不影响扫雪车自身
                    traci.vehicle.setColor(veh_id, (255, 255, 0)) 

        # 进度打印（每50步）
        if step % 50 == 0:
            print(f"Step {step}/{max_steps} | 已清扫道路: {len(cleared_edges)}条")
            

    traci.close()
    print(f"仿真结束，共清扫 {len(cleared_edges)} 条道路")

if __name__ == "__main__":
    run_snowplow_simulation()