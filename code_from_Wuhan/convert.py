import xml.etree.ElementTree as ET
import json
import random
import string
from datetime import datetime

def generate_object_id():
    """生成一个24位十六进制的ObjectId字符串"""
    # 生成类似MongoDB ObjectId的字符串（24个十六进制字符）
    timestamp = hex(int(datetime.now().timestamp()))[2:].zfill(8)
    random_part = ''.join(random.choices('0123456789abcdef', k=16))
    return timestamp + random_part

def parse_xml_to_json():
    """将XML路由文件转换为JSON格式"""
    # 解析XML文件
    tree = ET.parse('mapall_addline.rou.xml')
    root = tree.getroot()
    
    # 存储结果的列表
    persons = []
    
    # 用于确保ObjectId唯一性
    used_oids = set()
    
    # 遍历所有vehicle元素
    for idx, vehicle in enumerate(root.findall('vehicle')):
        # 生成唯一的ObjectId
        while True:
            oid = generate_object_id()
            if oid not in used_oids:
                used_oids.add(oid)
                break
        
        # 提取vehicle属性
        vehicle_id = vehicle.get('id')
        depart_time = float(vehicle.get('depart'))
        
        # 提取路由edges
        route_elem = vehicle.find('route')
        edges_str = route_elem.get('edges')
        road_ids = [int(edge) for edge in edges_str.split()]
        
        # 构造person对象
        person = {
            "_id": {
                "$oid": oid
            },
            "class": "person",
            "data": {
                "id": idx,  # 使用索引作为id
                "attribute": {},
                "home": {
                    "lane_position": {
                        "lane_id": None,  # 空着
                        "s": 0
                    }
                },
                "schedules": [
                    {
                        "trips": [
                            {
                                "mode": 2,
                                "end": {
                                    "lane_position": {
                                        "lane_id": 0,
                                        "s": 0
                                    }
                                },
                                "routes": [
                                    {
                                        "type": 1,
                                        "driving": {
                                            "road_ids": road_ids,
                                            "eta": None  # 空着
                                        }
                                    }
                                ],
                                "trip_stops": []
                            }
                        ],
                        "loop_count": 1,
                        "departure_time": depart_time
                    }
                ],
                "vehicle_attribute": {
                    "length": 5.0,  # SUMO默认值
                    "width": 1.8,  # SUMO默认值
                    "max_speed": 55.55,  # SUMO默认值 (200km/h)
                    "max_acceleration": 2.6,  # SUMO默认值
                    "max_braking_acceleration": 4.5,  # SUMO默认值 (decel)
                    "usual_acceleration": 2,  # 无SUMO对应，使用JSON原值
                    "usual_braking_acceleration": -4.5,  # 无SUMO对应，使用JSON原值
                    "lane_change_length": 10,  # 无SUMO对应，使用JSON原值
                    "min_gap": 2.5,  # SUMO默认值
                    "headway": 1.0,  # SUMO默认值 (tau)
                    "model": "Krauss",  # SUMO默认值
                    "lane_max_speed_recognition_deviation": 1,  # 无SUMO对应，使用JSON原值
                    "emission_attribute": {
                        "weight": 2100,  # 使用JSON原值
                        "type": 1,  # 使用JSON原值
                        "coefficient_drag": 0.251,  # 使用JSON原值
                        "lambda_s": 0.29,  # 使用JSON原值
                        "frontal_area": 2.52,  # 使用JSON原值
                        "fuel_efficiency": {
                            "energy_conversion_efficiency": 0.013230000000000002,  # 使用JSON原值
                            "c_ef": 66.98  # 使用JSON原值
                        }
                    },
                    "capacity": 4  # SUMO默认值 (personCapacity)
                },
                "bike_attribute": {
                    "speed": 5,
                    "model": "normal"
                },
                "pedestrian_attribute": {
                    "speed": 1.34,
                    "model": "normal"
                },
                "labels": {},
                "type": 0
            }
        }
        
        persons.append(person)
    
    # 写入JSON文件
    with open('convert.json', 'w', encoding='utf-8') as f:
        json.dump(persons, f, indent=2, ensure_ascii=False)
    
    print(f"转换完成！共处理了 {len(persons)} 个vehicle，已保存到 convert.json")
    return persons

if __name__ == "__main__":
    parse_xml_to_json()