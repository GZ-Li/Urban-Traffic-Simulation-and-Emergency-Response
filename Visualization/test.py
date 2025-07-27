import folium
from sumolib.net import readNet

# 加载SUMO路网（.net.xml）
net = readNet("E:\\Traffic_Simulation\\Adverse_weather_traffic\\net\\core_withshape_with_light_changing.net.xml")  # 替换为你的文件路径

# 创建folium地图（中心点初始值可以手动给出，后续也可以自动计算）
m = folium.Map(location=[0, 0], zoom_start=13)

# 收集所有经纬度点用于设定中心
all_coords = []

# 遍历每条边
for edge in net.getEdges():
    shape = edge.getShape()  # 返回一系列坐标点 [(x, y), (x, y), ...]
    latlon_shape = [net.convertXY2LonLat(x, y)[::-1] for x, y in shape]  # 转换为[(lat, lon)]
    # 添加到地图
    folium.PolyLine(
        latlon_shape,
        color="blue",
        weight=2,
        opacity=0.7,
        tooltip=edge.getID()
    ).add_to(m)
    all_coords.extend(latlon_shape)

# 设置地图中心为所有点的平均
if all_coords:
    avg_lat = sum(p[0] for p in all_coords) / len(all_coords)
    avg_lon = sum(p[1] for p in all_coords) / len(all_coords)
    m.location = [avg_lat, avg_lon]

# 保存或显示地图
m.save("sumo_network_map.html")
print("地图已保存为 sumo_network_map.html")
