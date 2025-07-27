import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from datetime import datetime
import os
import math
import numpy as np
from shapely.ops import transform
from functools import partial
import time
import random

# 坐标转换参数
x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def gcj02towgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 * math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 * math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 * math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 * math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    """
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def transform_geometry(geom):
    """转换几何对象的坐标"""

    def transform_coords(x, y, z=None):
        wgs_x, wgs_y = gcj02towgs84(x, y)
        return wgs_x, wgs_y

    return transform(transform_coords, geom)


def get_traffic_data(rectangle, key, current_time):
    """获取交通数据并返回GeoDataFrame"""
    try:
        # 初始化数据字典
        data = {
            'name': [],
            'status': [],
            'status_desc': [],
            'direction': [],
            'angle': [],
            'speed': [],
            'timestamp': [],
            'date': [],
            'time': [],
            'geometry': []
        }

        # 状态码映射
        status_mapping = {
            "0": "未知",
            "1": "畅通",
            "2": "缓行",
            "3": "拥堵"
        }

        # 构建API请求URL
        url = f'https://restapi.amap.com/v3/traffic/status/rectangle?rectangle={rectangle}&output=json&extensions=all&key={key}&level=6'

        # 发送请求并获取JSON响应
        res = requests.get(url, timeout=10).json()


        # 遍历每条道路数据
        for road in res['trafficinfo']['roads']:
            try:
                polylines = [(float(y[0]), float(y[1])) for y in
                             [x.split(',') for x in road['polyline'].split(';')]]

                # 创建线几何对象
                line = LineString(polylines)

                # 转换为WGS84坐标系
                wgs84_line = transform_geometry(line)

                status = road.get('status', '0')

                data['geometry'].append(wgs84_line)
                data['name'].append(road.get('name', ''))
                data['status'].append(float(status))
                data['status_desc'].append(status_mapping.get(status, '未知'))
                data['direction'].append(road.get('direction', ''))
                data['angle'].append(float(road.get('angle', 0)))
                data['speed'].append(int(road.get('speed', 0)))
                data['timestamp'].append(current_time.strftime("%Y-%m-%d %H:%M:%S"))
                data['date'].append(current_time.strftime("%Y-%m-%d"))
                data['time'].append(current_time.strftime("%H:%M:%S"))
            except Exception as e:
                print(f"处理单条道路数据时出错: {str(e)}")
                continue

        # 创建GeoDataFrame对象
        gdf = gpd.GeoDataFrame(data, geometry='geometry', crs='EPSG:4326')
        gdf['status'] = gdf['status'].astype(np.float64)

        return gdf

    except Exception as e:
        print(f"处理出错: {str(e)}")
        return None


def process_rectangles_sequential(rectangles, key='9998c64b9c00549709c1caf0af149ecd', output_dir='output'):
    """
    顺序处理多个矩形区域的交通数据，将所有数据保存在同一个时间段的文件中，并进行去重
    增加随机延时，避免请求过于频繁
    """
    # 生成统一的时间戳
    current_time = datetime.now()
    filename = f'0407Monday_1_4_17304500_traffic_status_{current_time.strftime("%Y%m%d%H%M%S")}_wgs84.shp'
    output_path = os.path.join(output_dir, filename)

    # 用于存储所有区域的数据
    all_gdfs = []

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    total_rectangles = len(rectangles)
    for i, rectangle in enumerate(rectangles, 1):
        try:
            print(f"开始处理区域 [{i}/{total_rectangles}]: {rectangle}")
            gdf = get_traffic_data(rectangle, key, current_time)
            if gdf is not None:
                all_gdfs.append(gdf)
            print(f"区域 {rectangle} 处理完成")

            # 随机延时，除了最后一个请求
            if i < total_rectangles:
                delay = random.uniform(1, 3)  # 随机 1-3 秒延时
                print(f"等待 {delay:.1f} 秒后继续...")
                time.sleep(delay)

        except Exception as e:
            print(f"处理区域 {rectangle} 时出错: {str(e)}")
            # 发生错误时也添加延时
            time.sleep(random.uniform(2, 4))

    # 合并所有数据并去重
    if all_gdfs:
        print("\n开始合并和去重数据...")
        # 合并所有数据
        combined_gdf = gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True))

        # 去重前的记录数
        before_count = len(combined_gdf)

        # 基于name、direction和angle进行去重
        combined_gdf = combined_gdf.drop_duplicates(
            subset=['name', 'direction', 'angle'],
            keep='first'
        )

        # 去重后的记录数
        after_count = len(combined_gdf)

        # 保存处理后的数据
        combined_gdf.to_file(output_path, encoding='utf-8')
        print(f"已保存所有数据到: {output_path}")
        print(f"去重统计: {before_count} -> {after_count} 条记录 (删除了 {before_count - after_count} 条重复记录)")


if __name__ == "__main__":
    rectangles = [
        '114.488157,30.478389;114.509065,30.496407',
        '114.467246,30.496407;114.488159,30.514425',
        '114.467250,30.460371;114.488155,30.478389',
        '114.488155,30.496407;114.509067,30.514425',
        '114.488159,30.460371;114.509063,30.478389',
        '114.509063,30.496407;114.529976,30.514425',
        '114.509067,30.460371;114.529972,30.478389',
        '114.467248,30.478389;114.488157,30.496407',
        '114.509065,30.478389;114.529974,30.496407',
        '114.446335,30.514425;114.467252,30.532443',
        '114.446343,30.442353;114.467244,30.460371',
        '114.467244,30.514425;114.488160,30.532443',
        '114.467252,30.442353;114.488153,30.460371',
        '114.488153,30.514425;114.509069,30.532443',
        '114.488160,30.442353;114.509062,30.460371',
        '114.509062,30.514425;114.529978,30.532443',
        '114.509069,30.442353;114.529970,30.460371',
        '114.529970,30.514425;114.550887,30.532443',
        '114.529978,30.442353;114.550879,30.460371',
        '114.446341,30.460371;114.467246,30.478389',
        '114.529976,30.460371;114.550881,30.478389',
        '114.446339,30.478389;114.467248,30.496407',
        '114.529974,30.478389;114.550883,30.496407',
        '114.446337,30.496407;114.467250,30.514425',
        '114.529972,30.496407;114.550885,30.514425',
        '114.425424,30.532443;114.446345,30.550461',
        '114.425436,30.424335;114.446333,30.442353',
        '114.446333,30.532443;114.467254,30.550461',
        '114.446345,30.424335;114.467242,30.442353',
        '114.467242,30.532443;114.488162,30.550461',
        '114.467254,30.424335;114.488151,30.442353',
        '114.488151,30.532443;114.509071,30.550461',
        '114.488162,30.424335;114.509060,30.442353',
        '114.509060,30.532443;114.529980,30.550461',
        '114.509071,30.424335;114.529968,30.442353',
        '114.529968,30.532443;114.550889,30.550461',
        '114.529980,30.424335;114.550877,30.442353',
        '114.550877,30.532443;114.571798,30.550461',
        '114.550889,30.424335;114.571786,30.442353',
        '114.425434,30.442353;114.446335,30.460371',
        '114.550887,30.442353;114.571788,30.460371',
        '114.425432,30.460371;114.446337,30.478389',
        '114.550885,30.460371;114.571790,30.478389',
        '114.425430,30.478389;114.446339,30.496407',
        '114.550883,30.478389;114.571792,30.496407',
        '114.425428,30.496407;114.446341,30.514425',
        '114.550881,30.496407;114.571794,30.514425',
        '114.425426,30.514425;114.446343,30.532443',
        '114.550879,30.514425;114.571796,30.532443',
        '114.404513,30.550461;114.425438,30.568479',
        '114.404529,30.406317;114.425422,30.424335',
        '114.425422,30.550461;114.446347,30.568479',
        '114.425438,30.406317;114.446331,30.424335',
        '114.446331,30.550461;114.467255,30.568479',
        '114.446347,30.406317;114.467240,30.424335',
        '114.467240,30.550461;114.488164,30.568479',
        '114.467255,30.406317;114.488149,30.424335',
        '114.488149,30.550461;114.509073,30.568479',
        '114.488164,30.406317;114.509058,30.424335',
        '114.509058,30.550461;114.529982,30.568479',
        '114.509073,30.406317;114.529967,30.424335',
        '114.529967,30.550461;114.550891,30.568479',
        '114.529982,30.406317;114.550875,30.424335',
        '114.550875,30.550461;114.571800,30.568479',
        '114.550891,30.406317;114.571784,30.424335',
        '114.571784,30.550461;114.592709,30.568479',
        '114.571800,30.406317;114.592693,30.424335',
        '114.404527,30.424335;114.425424,30.442353',
        '114.571798,30.424335;114.592695,30.442353',
        '114.404525,30.442353;114.425426,30.460371',
        '114.571796,30.442353;114.592697,30.460371',
        '114.404523,30.460371;114.425428,30.478389',
        '114.571794,30.460371;114.592699,30.478389',
        '114.404521,30.478389;114.425430,30.496407',
        '114.571792,30.478389;114.592701,30.496407',
        '114.404519,30.496407;114.425432,30.514425',
        '114.571790,30.496407;114.592703,30.514425',
        '114.404517,30.514425;114.425434,30.532443',
        '114.571788,30.514425;114.592705,30.532443',
        '114.404515,30.532443;114.425436,30.550461',
        '114.571786,30.532443;114.592707,30.550461',
    ]

    process_rectangles_sequential(rectangles)