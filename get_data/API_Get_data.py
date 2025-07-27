from math import cos, radians
import folium
from folium.plugins import MeasureControl


def generate_rectangle(center_point, radius_km):
    """
    通过中心点和半径生成矩形范围
    """
    try:
        center_lon, center_lat = map(float, center_point.split(','))
        lat_diff = radius_km / 111.0
        lon_diff = radius_km / (111.0 * cos(radians(center_lat)))

        min_lon = center_lon - lon_diff
        min_lat = center_lat - lat_diff
        max_lon = center_lon + lon_diff
        max_lat = center_lat + lat_diff

        rectangle = f"{min_lon:.6f},{min_lat:.6f};{max_lon:.6f},{max_lat:.6f}"

        return {
            'rectangle': rectangle,
            'center': [center_lat, center_lon],
            'bounds': [[min_lat, min_lon], [max_lat, max_lon]],
            'lat_diff': lat_diff,
            'lon_diff': lon_diff
        }

    except Exception as e:
        print(f"生成矩形范围时出错: {str(e)}")
        return None


def generate_surrounding_rectangles(center_point, radius_km, layers=2):
    """
    生成多层矩形的坐标
    layers: 要生成的层数（默认2层）
    """
    center_coords = generate_rectangle(center_point, radius_km)
    if not center_coords:
        return None

    center_lon, center_lat = map(float, center_point.split(','))
    all_rectangles = []

    # 生成每一层的矩形
    for layer in range(1, layers + 1):
        # 当前层的偏移量
        current_lat_diff = center_coords['lat_diff'] * 2 * layer
        current_lon_diff = center_coords['lon_diff'] * 2 * layer

        layer_centers = []

        # 上下各 2*layer+1 个点
        for i in range(-layer, layer + 1):
            layer_centers.append((center_lon + i * center_coords['lon_diff'] * 2,
                                  center_lat + current_lat_diff))  # 上
            layer_centers.append((center_lon + i * center_coords['lon_diff'] * 2,
                                  center_lat - current_lat_diff))  # 下

        # 左右各 2*(layer-1)+1 个点（不包括已添加的角点）
        for i in range(-(layer - 1), layer):
            layer_centers.append((center_lon - current_lon_diff,
                                  center_lat + i * center_coords['lat_diff'] * 2))  # 左
            layer_centers.append((center_lon + current_lon_diff,
                                  center_lat + i * center_coords['lat_diff'] * 2))  # 右

        # 为当前层的所有中心点生成矩形
        layer_rectangles = []
        for i, (lon, lat) in enumerate(layer_centers):
            rect = generate_rectangle(f"{lon},{lat}", radius_km)
            if rect:
                rect['direction'] = f"第{layer}层{i + 1}号"
                rect['layer'] = layer
                layer_rectangles.append(rect)

        all_rectangles.extend(layer_rectangles)

    return center_coords, all_rectangles


def visualize_rectangles(center_point, radius_km, layers=2):
    """
    可视化中心矩形和周围的矩形，并以特定格式打印坐标
    """
    result = generate_surrounding_rectangles(center_point, radius_km, layers)
    if not result:
        return

    center_coords, surrounding_rectangles = result

    # 创建地图
    m = folium.Map(
        location=center_coords['center'],
        zoom_start=12,
        tiles='https://webst02.is.autonavi.com/appmaptile?style=7&x={x}&y={y}&z={z}',
        attr='AutoNavi'
    )

    # 添加中心矩形
    folium.Rectangle(
        bounds=center_coords['bounds'],
        color='red',
        fill=True,
        fillColor='red',
        fillOpacity=0.2,
        popup='中心矩形'
    ).add_to(m)

    # 为每一层设置不同的基础颜色
    base_colors = ['blue', 'green', 'purple', 'orange', 'darkred', 'darkblue',
                   'darkgreen', 'cadetblue', 'lightred', 'lightblue', 'lightgreen',
                   'gray', 'pink', 'beige', 'lightgray', 'black']

    # 添加周围矩形
    for rect in surrounding_rectangles:
        # 根据层数选择颜色
        color = base_colors[(rect['layer'] - 1) % len(base_colors)]

        folium.Rectangle(
            bounds=rect['bounds'],
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.2,
            popup=f"{rect['direction']}"
        ).add_to(m)

        # 添加中心点标记
        folium.Marker(
            rect['center'],
            popup=f"{rect['direction']}中心点",
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)

    # 添加中心点标记
    folium.Marker(
        center_coords['center'],
        popup='中心点',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    # 添加测量控件
    m.add_child(MeasureControl())

    # 保存地图
    output_file = 'rectangles_visualization.html'
    m.save(output_file)
    print(f"可视化结果已保存到: {output_file}")

    # 修改后的打印格式
    print("\nrectangles = [")
    # 首先打印中心矩形
    print(f"    '{center_coords['rectangle']}',")

    # 然后打印周围的矩形
    for rect in surrounding_rectangles:
        print(f"    '{rect['rectangle']}',")
    print("]")

    return center_coords, surrounding_rectangles


if __name__ == "__main__":
    center_point = "114.498611,30.487398"  # 中心点坐标
    radius = 1  # 半径2公里
    layers = 4  # 想要生成的层数

    visualize_rectangles(center_point, radius, layers)