"""
SUMO仿真模块 - 在仿真环境中测量救护车到达时间
"""
import traci
import numpy as np
import os
from pathlib import Path


def setup_sumo_simulation(sumo_config_file, use_gui=False):
    """
    启动SUMO仿真
    
    Args:
        sumo_config_file: SUMO配置文件路径
        use_gui: 是否使用图形界面
    
    Returns:
        True if successful
    """
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    
    sumo_cmd = [
        sumo_binary,
        "-c", sumo_config_file,
        "--no-warnings",
        "--time-to-teleport", "-1",
        "--collision.action", "none"
    ]
    
    try:
        traci.start(sumo_cmd)
        return True
    except Exception as e:
        print(f"❌ 启动SUMO失败: {e}")
        return False


def measure_route_time(route_edges, vehicle_id="ambulance_test", 
                       max_steps=2000, depart_time=100):
    """
    在SUMO中测量指定路径的实际行驶时间
    
    Args:
        route_edges: 路径edge列表
        vehicle_id: 车辆ID
        max_steps: 最大仿真步数
        depart_time: 出发时间
    
    Returns:
        到达时间（秒），如果失败返回None
    """
    try:
        # 构建路由字符串
        route_str = " ".join(route_edges)
        
        # 添加救护车到仿真
        traci.route.add(f"route_{vehicle_id}", route_edges)
        traci.vehicle.add(
            vehicle_id,
            f"route_{vehicle_id}",
            typeID="ambulance",
            depart=str(depart_time)
        )
        
        # 设置救护车参数
        traci.vehicle.setSpeedMode(vehicle_id, 0)  # 关闭速度限制
        traci.vehicle.setSpeed(vehicle_id, 30)  # 设置速度30m/s
        traci.vehicle.setColor(vehicle_id, (255, 0, 0))  # 红色
        
        arrival_time = None
        start_step = traci.simulation.getTime()
        
        # 仿真直到车辆到达
        for step in range(max_steps):
            traci.simulationStep()
            current_time = traci.simulation.getTime()
            
            # 检查车辆是否还在仿真中
            if vehicle_id not in traci.vehicle.getIDList():
                # 车辆已经到达或消失
                arrival_time = current_time - depart_time
                break
            
            # 检查车辆是否到达目标edge
            current_edge = traci.vehicle.getRoadID(vehicle_id)
            if current_edge == route_edges[-1]:
                # 到达目标edge
                arrival_time = current_time - depart_time
                # 移除车辆
                traci.vehicle.remove(vehicle_id)
                break
        
        return arrival_time
    
    except Exception as e:
        print(f"⚠️  测量失败: {e}")
        return None


def batch_measure_routes(routes_dict, sumo_config_file, use_gui=False):
    """
    批量测量多条路径的时间
    
    Args:
        routes_dict: 路径字典 {route_id: [edge1, edge2, ...]}
        sumo_config_file: SUMO配置文件
        use_gui: 是否使用GUI
    
    Returns:
        时间字典 {route_id: time_seconds}
    """
    if not setup_sumo_simulation(sumo_config_file, use_gui):
        return {}
    
    results = {}
    total = len(routes_dict)
    
    print(f"\n开始测量 {total} 条路径...")
    
    for i, (route_id, edges) in enumerate(routes_dict.items(), 1):
        if i % 10 == 0 or i == 1:
            print(f"  进度: {i}/{total}")
        
        time = measure_route_time(edges, vehicle_id=f"ambulance_{route_id}")
        
        if time is not None:
            results[route_id] = time
        else:
            print(f"  ⚠️  路径 {route_id} 测量失败")
            results[route_id] = 9999  # 使用一个大值表示失败
    
    traci.close()
    print(f"✅ 完成！成功测量 {len([t for t in results.values() if t < 9999])}/{total} 条路径")
    
    return results


def measure_hospital_accident_pairs(G, hospitals, accidents, k_paths=5, 
                                    sumo_config_file=None, use_gui=False):
    """
    为所有医院-事故点对测量K条路径的时间
    
    Args:
        G: 路网图
        hospitals: 医院字典 {name: edge_id}
        accidents: 事故点列表 [edge_id1, edge_id2, ...]
        k_paths: 每对计算的路径数
        sumo_config_file: SUMO配置文件
        use_gui: 是否使用GUI
    
    Returns:
        routes_info: 路径信息列表
        time_matrix: 时间矩阵
    """
    from path_planning import find_k_shortest_paths, filter_internal_edges
    
    routes_to_measure = {}
    routes_info = []
    route_id = 0
    
    print("\n" + "="*60)
    print("📍 生成路径")
    print("="*60)
    
    hospital_list = list(hospitals.items())
    
    for i, (hosp_name, hosp_edge) in enumerate(hospital_list):
        for j, acc_edge in enumerate(accidents):
            try:
                # 计算K短路
                paths = find_k_shortest_paths(G, hosp_edge, acc_edge, k=k_paths)
                
                for path_idx, path in enumerate(paths):
                    # 过滤内部边
                    filtered_path = filter_internal_edges(path)
                    
                    route_info = {
                        'route_id': route_id,
                        'hospital_idx': i,
                        'hospital_name': hosp_name,
                        'accident_idx': j,
                        'path_idx': path_idx,
                        'edges': filtered_path
                    }
                    
                    routes_info.append(route_info)
                    routes_to_measure[route_id] = filtered_path
                    route_id += 1
                
                if (i * len(accidents) + j + 1) % 5 == 0:
                    print(f"  已生成 {i * len(accidents) + j + 1}/{len(hospitals) * len(accidents)} 对的路径")
            
            except Exception as e:
                print(f"  ⚠️  {hosp_name} → 事故点{j+1} 路径计算失败: {e}")
    
    print(f"✅ 共生成 {len(routes_to_measure)} 条路径")
    
    # 测量所有路径的时间
    if sumo_config_file and os.path.exists(sumo_config_file):
        print("\n" + "="*60)
        print("🚗 SUMO仿真测量")
        print("="*60)
        
        time_results = batch_measure_routes(routes_to_measure, sumo_config_file, use_gui)
        
        # 添加时间到路径信息
        for route in routes_info:
            route['time'] = time_results.get(route['route_id'], 9999)
        
        # 构建时间矩阵（取每对的最短时间）
        num_hospitals = len(hospitals)
        num_accidents = len(accidents)
        time_matrix = np.full((num_hospitals, num_accidents), np.inf)
        
        for route in routes_info:
            h_idx = route['hospital_idx']
            a_idx = route['accident_idx']
            time = route['time']
            
            if time < time_matrix[h_idx, a_idx]:
                time_matrix[h_idx, a_idx] = time
        
        # 替换inf为一个大值
        time_matrix[time_matrix == np.inf] = 9999
        
        return routes_info, time_matrix
    
    else:
        print("\n⚠️  未提供SUMO配置文件，跳过仿真测量")
        return routes_info, None
