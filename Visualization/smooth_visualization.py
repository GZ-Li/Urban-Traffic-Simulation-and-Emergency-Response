import sumolib
import traci
import folium
from branca.colormap import LinearColormap
import numpy as np

# 初始化 Sumo
sumo_binary = sumolib.checkBinary('sumo')
# traci.start([sumo_binary, "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test.sumocfg"])
traci.start([sumo_binary, "-c", "E:\\Traffic_Simulation\\Visualization\\visual.sumocfg"])

# 推进到第 50 步
while traci.vehicle.getIDCount() <= 16000:
    traci.simulationStep()

# 读取路网
net = sumolib.net.readNet("E:\\Traffic_Simulation\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml")

# 1. 计算所有 edge 的 segment 速度，并记录全局最大/最小速度
all_speeds = []
edge_segments = {}

for edge in net.getEdges():
    edge_id = edge.getID()
    shape = edge.getShape()
    length = edge.getLength()
    
    # 增加分段数使曲线更平滑
    segments = []
    for i in range(10):  # 从5段增加到10段
        start_pos = i * length / 10
        end_pos = (i + 1) * length / 10
        
        vehicles = traci.edge.getLastStepVehicleIDs(edge_id)
        segment_vehicles = [
            vid for vid in vehicles 
            if start_pos <= traci.vehicle.getLanePosition(vid) <= end_pos
        ]
        
        if segment_vehicles:
            avg_speed = np.mean([traci.vehicle.getSpeed(vid) for vid in segment_vehicles])
        else:
            avg_speed = 35  # 默认速度
        
        segments.append((start_pos, end_pos, avg_speed))
        all_speeds.append(avg_speed)
    
    edge_segments[edge_id] = segments

# 2. 计算全局速度范围（扩展范围使颜色区分更明显）
global_min_speed = min(all_speeds) * 0.9  # 留出10%余量
global_max_speed = max(all_speeds) * 1.1

# 3. 创建更平滑的颜色映射
colors = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', 
          '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']
colormap = LinearColormap(colors, vmin=global_min_speed, vmax=global_max_speed)
colormap.caption = f'Speed Range: {global_min_speed:.1f} - {global_max_speed:.1f} m/s'

# 4. 创建地图
all_shape_points = []
for edge in net.getEdges():
    all_shape_points.extend(edge.getShape())

avg_x = np.mean([p[0] for p in all_shape_points])
avg_y = np.mean([p[1] for p in all_shape_points])
center_lon, center_lat = net.convertXY2LonLat(avg_x, avg_y)

m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB positron')
m.add_child(colormap)

# 5. 绘制更平滑的线段
for edge in net.getEdges():
    edge_id = edge.getID()
    shape = edge.getShape()
    segments = edge_segments[edge_id]
    
    # 为每个edge创建连续的点列表
    points = []
    speeds = []
    for i, (start_pos, end_pos, speed) in enumerate(segments):
        # 添加起点（第一个segment）和终点
        if i == 0:
            start_coord = sumolib.geomhelper.positionAtShapeOffset(shape, start_pos)
            points.append(start_coord)
            speeds.append(speed)
        
        end_coord = sumolib.geomhelper.positionAtShapeOffset(shape, end_pos)
        points.append(end_coord)
        speeds.append(speed)
    
    # 转换为经纬度
    points_lonlat = [net.convertXY2LonLat(p[0], p[1]) for p in points]
    points_latlon = [(lat, lon) for (lon, lat) in points_lonlat]
    
    # 创建颜色渐变线段
    for i in range(len(points_latlon)-1):
        folium.PolyLine(
            locations=[points_latlon[i], points_latlon[i+1]],
            color=colormap(speeds[i]),
            weight=3,  # 加宽线条
            opacity=0.9,
            line_cap='round',  # 使连接处更平滑
            line_join='round',
            tooltip=f"Edge: {edge_id}, Speed: {speeds[i]:.1f} m/s"
        ).add_to(m)

# 关闭 traci
traci.close()

# 保存地图
m.save("sumo_smooth_traffic_visualization_rain_07211819.html")