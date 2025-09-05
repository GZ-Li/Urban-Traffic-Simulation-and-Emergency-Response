import sumolib
import traci
import folium
from branca.colormap import LinearColormap
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# 初始化 Sumo
sumo_binary = sumolib.checkBinary('sumo')
traci.start([sumo_binary, "-c", "E:\\Traffic_Simulation\\Visualization\\visual.sumocfg"])
# traci.start([sumo_binary, "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test.sumocfg"])
# traci.start([sumo_binary, "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_full.sumocfg"])
# traci.start([sumo_binary, "-c", "E:\\Traffic_Simulation\\Adverse_weather_traffic\\Core_500m_test_scale_2.sumocfg"])

# 推进到第 50 步
while traci.vehicle.getIDCount() <= 16000:
    traci.simulationStep()

# current_step = 0
# while current_step <= 500:
#     current_step += 1
#     traci.simulationStep()

# 读取路网
net = sumolib.net.readNet("E:\\Traffic_Simulation\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml")

# 1. 计算所有 edge 的 segment 速度，按20米分段
all_speeds = []
edge_segments = {}

for edge in net.getEdges():
    edge_id = edge.getID()
    shape = edge.getShape()
    length = edge.getLength()
    
    segments = []
    segment_length = 50  # 每20米一段
    num_segments = int(np.ceil(length / segment_length))
    
    for i in range(num_segments):
        start_pos = i * segment_length
        end_pos = min((i + 1) * segment_length, length)
        
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

# 2. 计算全局速度范围
global_min_speed = min(all_speeds)
global_max_speed = max(all_speeds)

# 3. 创建非线性颜色映射 (0-15变化剧烈，15以上变化平缓)
def nonlinear_normalize(speed, threshold=15):
    """非线性归一化函数，使0-15区间变化更剧烈"""
    if speed <= threshold:
        return speed / (2 * threshold)  # 0-15映射到0-0.5
    else:
        return 0.5 + (speed - threshold) / (2 * (global_max_speed - threshold))  # 15+映射到0.5-1

# 定义颜色节点（0-0.5: 红到黄，0.5-1: 黄到绿）
colors = [
    (0, '#d73027'),   # 红
    # (3, '#f46d43'),   # 橙红
    (4, '#fee08b'),   # 黄
    (15, '#a6d96a'),   # 黄绿
    (35, '#1a9850')    # 绿 
]

# 创建自定义颜色映射
colormap = LinearSegmentedColormap.from_list('nonlinear_cmap', colors)
colormap = folium.LinearColormap(
    colors=['#d73027', '#fee08b', '#a6d96a', '#1a9850'],
    index=[0, 10, 20, 35],
    vmin=global_min_speed,
    vmax=global_max_speed,
    caption=f'Speed Range: {global_min_speed:.1f} - {global_max_speed:.1f} m/s'
)

# 4. 创建地图
all_shape_points = []
for edge in net.getEdges():
    all_shape_points.extend(edge.getShape())

avg_x = np.mean([p[0] for p in all_shape_points])
avg_y = np.mean([p[1] for p in all_shape_points])
center_lon, center_lat = net.convertXY2LonLat(avg_x, avg_y)

m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB positron')
m.add_child(colormap)

# 5. 绘制线段
for edge in net.getEdges():
    edge_id = edge.getID()
    shape = edge.getShape()
    segments = edge_segments[edge_id]
    
    points = []
    speeds = []
    for i, (start_pos, end_pos, speed) in enumerate(segments):
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
        # 使用非线性归一化
        norm_speed = nonlinear_normalize(speeds[i])
        color = colormap(norm_speed * (global_max_speed - global_min_speed) + global_min_speed)
        
        folium.PolyLine(
            locations=[points_latlon[i], points_latlon[i+1]],
            color=color,
            weight=3,
            opacity=0.9,
            line_cap='round',
            line_join='round',
            tooltip=f"Edge: {edge_id}, Speed: {speeds[i]:.1f} m/s"
        ).add_to(m)

# 关闭 traci
traci.close()

# 保存地图
m.save("rain0723.html")