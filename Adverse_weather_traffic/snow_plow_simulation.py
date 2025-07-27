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
CONFIG_FILE = "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_scale.sumocfg"

def run_snowplow_simulation():
    
    # 扫雪车参数
    # snowplow_id = "snowplow_1"
    cleared_edges = set()
    max_steps = 450
    
    snowplow_routes_1 = "200014261 200025126 200015069 200015067 200025154 200007033 200001532 200001528 200020476 200020477 200021947"
    # snowplow_routes_1 = "200015067 200025154 200007033 200001532 200001590 200001586"
    snowplow_routes_2 = "200025155 200015066 200015032"
    snowplow_routes_3 = "200060659 200060651 200080654"
    snowplow_maxspeed = 15
    
    tree = ET.parse("E:\\Traffic_Simulation\\Adverse_weather_traffic\\snowplow_rou\\routes_od_4_rain.rou.xml") # rou
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
    restricted_vtype = ET.Element('vType', {
        'id': "restricted_type",
        'maxSpeed': "10", 
        'minGap': "5", 
    })
    # root.insert(4, restricted_vtype)
    # for vehicle in root.findall('vehicle'):
    #     if vehicle.get('id') not in ["snowplow_1", "snowplow_2", "snowplow_3"]:
    #         vehicle.set('type', 'restricted_type')
            
    tree.write("snowplow_rou/routes_od_4_snowplow.rou.xml", encoding='utf-8', xml_declaration=True)
    
    traci.start(["sumo-gui", "-c", CONFIG_FILE, "--start"])

    # 添加扫雪车（设置为应急车辆类型）
    # traci.vehicletype.copy("DEFAULT_VEHTYPE", "snowplow")
    # # traci.vehicletype.setParameter("snowplow", "has.bluelight.device", "true")  # 蓝灯效果
    # traci.vehicle.add(
    #     vehID="snowplow_1",
    #     routeID=["200064849", "200064848", "200061267"],  # 随机行驶
    #     typeID="snowplow",
    #     depart="now"
    # )
    # traci.vehicle.setColor("snowplow_1", (0, 0, 1))  # 纯蓝色
    # traci.vehicle.setMaxSpeed("snowplow_1", 10)  # 扫雪车速度10m/s
    
    

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
                traci.edge.setParameter(current_edge_1, "viz.color", "144,238,144,255")
        if ("snowplow_2" in traci.vehicle.getIDList()):
            current_edge_2 = traci.vehicle.getRoadID("snowplow_2")
            if current_edge_2 not in cleared_edges:
                cleared_edges.add(current_edge_2)
                traci.edge.setParameter(current_edge_2, "viz.color", "144,238,144,255")
        if ("snowplow_3" in traci.vehicle.getIDList()):
            current_edge_3 = traci.vehicle.getRoadID("snowplow_3")
            if current_edge_3 not in cleared_edges:
                cleared_edges.add(current_edge_3)
                traci.edge.setParameter(current_edge_3, "viz.color", "144,238,144,255")
        
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
    
    
    # net = sumolib.net.readNet("E:\\Traffic_Simulation\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml")

    # # 1. 计算所有 edge 的 segment 速度，按20米分段
    # all_speeds = []
    # edge_segments = {}

    # for edge in net.getEdges():
    #     edge_id = edge.getID()
    #     shape = edge.getShape()
    #     length = edge.getLength()
        
    #     segments = []
    #     segment_length = 50  # 每20米一段
    #     num_segments = int(np.ceil(length / segment_length))
        
    #     for i in range(num_segments):
    #         start_pos = i * segment_length
    #         end_pos = min((i + 1) * segment_length, length)
            
    #         vehicles = traci.edge.getLastStepVehicleIDs(edge_id)
    #         segment_vehicles = [
    #             vid for vid in vehicles 
    #             if start_pos <= traci.vehicle.getLanePosition(vid) <= end_pos
    #         ]
            
    #         if segment_vehicles:
    #             avg_speed = np.mean([traci.vehicle.getSpeed(vid) for vid in segment_vehicles])
    #         else:
    #             avg_speed = 35  # 默认速度
            
    #         segments.append((start_pos, end_pos, avg_speed))
    #         all_speeds.append(avg_speed)
        
    #     edge_segments[edge_id] = segments

    # # 2. 计算全局速度范围
    # global_min_speed = min(all_speeds)
    # global_max_speed = max(all_speeds)

    # # 3. 创建非线性颜色映射 (0-15变化剧烈，15以上变化平缓)
    # def nonlinear_normalize(speed, threshold=15):
    #     """非线性归一化函数，使0-15区间变化更剧烈"""
    #     if speed <= threshold:
    #         return speed / (2 * threshold)  # 0-15映射到0-0.5
    #     else:
    #         return 0.5 + (speed - threshold) / (2 * (global_max_speed - threshold))  # 15+映射到0.5-1

    # # 定义颜色节点（0-0.5: 红到黄，0.5-1: 黄到绿）
    # colors = [
    #     (0, '#d73027'),   # 红
    #     (5, '#f46d43'),   # 橙红
    #     (10, '#fee08b'),   # 黄
    #     (15, '#a6d96a'),   # 黄绿
    #     (35, '#1a9850')    # 绿 
    # ]

    # # 创建自定义颜色映射
    # colormap = LinearSegmentedColormap.from_list('nonlinear_cmap', colors)
    # colormap = folium.LinearColormap(
    #     colors=['#d73027', '#f46d43', '#fee08b', '#a6d96a', '#1a9850'],
    #     index=[0, 5, 10, 15, 35],
    #     vmin=global_min_speed,
    #     vmax=global_max_speed,
    #     caption=f'Speed Range: {global_min_speed:.1f} - {global_max_speed:.1f} m/s'
    # )

    # # 4. 创建地图
    # all_shape_points = []
    # for edge in net.getEdges():
    #     all_shape_points.extend(edge.getShape())

    # avg_x = np.mean([p[0] for p in all_shape_points])
    # avg_y = np.mean([p[1] for p in all_shape_points])
    # center_lon, center_lat = net.convertXY2LonLat(avg_x, avg_y)

    # m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB positron')
    # m.add_child(colormap)

    # # 5. 绘制线段
    # for edge in net.getEdges():
    #     edge_id = edge.getID()
    #     shape = edge.getShape()
    #     segments = edge_segments[edge_id]
        
    #     points = []
    #     speeds = []
    #     for i, (start_pos, end_pos, speed) in enumerate(segments):
    #         if i == 0:
    #             start_coord = sumolib.geomhelper.positionAtShapeOffset(shape, start_pos)
    #             points.append(start_coord)
    #             speeds.append(speed)
            
    #         end_coord = sumolib.geomhelper.positionAtShapeOffset(shape, end_pos)
    #         points.append(end_coord)
    #         speeds.append(speed)
        
    #     # 转换为经纬度
    #     points_lonlat = [net.convertXY2LonLat(p[0], p[1]) for p in points]
    #     points_latlon = [(lat, lon) for (lon, lat) in points_lonlat]
        
    #     # 创建颜色渐变线段
    #     for i in range(len(points_latlon)-1):
    #         # 使用非线性归一化
    #         norm_speed = nonlinear_normalize(speeds[i])
    #         color = colormap(norm_speed * (global_max_speed - global_min_speed) + global_min_speed)
            
    #         folium.PolyLine(
    #             locations=[points_latlon[i], points_latlon[i+1]],
    #             color=color,
    #             weight=3,
    #             opacity=0.9,
    #             line_cap='round',
    #             line_join='round',
    #             tooltip=f"Edge: {edge_id}, Speed: {speeds[i]:.1f} m/s"
    #         ).add_to(m)
    # m.save("E:\\Traffic_Simulation\\Visualization\\snowplow_with_plow2.html")

    traci.close()
    print(f"仿真结束，共清扫 {len(cleared_edges)} 条道路")

if __name__ == "__main__":
    run_snowplow_simulation()