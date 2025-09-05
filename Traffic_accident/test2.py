from networkx.algorithms.simple_paths import shortest_simple_paths
import xml.etree.ElementTree as ET
import networkx as nx
import pandas as pd
import math
import traci
import random

sumo_net_file = "E:\\Traffic_Simulation\\Traffic_accident\\full_net\\new_add_light.net.xml" 
input_rou = "E:\\Traffic_Simulation\\Traffic_accident\\full_rou\\mapall_addline.rou.xml"
output_rou = "E:\\Traffic_Simulation\\Traffic_accident\\full_rou\\mapall_addline_response.rou.xml"

accident_spots = ["200042649", "200040849", "200063134", "200002421", "200040901"]
traci.start(["sumo", "-c", "E:\\Traffic_Simulation\\Traffic_accident\\response.sumocfg"])
current_step = 0
accident_spots_simu_flag = {}
for acs in accident_spots:
    accident_spots_simu_flag[acs] = False
while current_step < 500:
    if current_step >= 100:
        if not (list(accident_spots) == True):
            for acs in accident_spots:
                if (accident_spots_simu_flag[acs] == False) and (len(list(traci.edge.getLastStepVehicleIDs(acs))) > 0):
                    veh_id = random.choice(list(traci.edge.getLastStepVehicleIDs(acs)))
                    try:
                        traci.vehicle.setSpeed(veh_id, 0)
                        traci.vehicle.setStop(veh_id, acs, 
                                            traci.vehicle.getLanePosition(veh_id), 
                                            laneIndex=traci.vehicle.getLaneIndex(veh_id), 
                                            duration=9999)
                        traci.vehicle.setColor(veh_id, (255, 0, 0))
                        accident_spots_simu_flag[acs] = True
                        print(current_step)
                        print(acs)
                    except: 
                        continue
    traci.simulationStep()
    current_step += 1