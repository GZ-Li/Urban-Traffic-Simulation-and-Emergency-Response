"""
事故点生成器 - 在事故点周围随机生成测试案例
"""
import sumolib
import random
import math
import os
from config import SUMO_NET_FILE, SIMULATION_CONFIG, ACCIDENT_CASES_FILE


def distance(p1, p2):
    """
    计算两点之间的欧氏距离
    
    Args:
        p1: 点1坐标 (x, y)
        p2: 点2坐标 (x, y)
    
    Returns:
        欧氏距离
    """
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def generate_accident_cases(net_file, accident_spots, radius=1000, 
                            num_per_accident=5, num_cases=20, output_file=None):
    """
    在指定事故点周围随机生成测试案例
    
    Args:
        net_file: SUMO路网文件路径
        accident_spots: 事故点edge ID列表
        radius: 搜索半径（米）
        num_per_accident: 每个事故点附近选取的edge数量
        num_cases: 生成的测试案例数量
        output_file: 输出文件路径
    
    Returns:
        案例列表，每个案例是edge ID列表
    """
    # 加载路网
    net = sumolib.net.readNet(net_file)
    
    exp_cases = []
    
    for case_id in range(num_cases):
        # 获取每条edge的中心点坐标
        edge_positions = {}
        for edge in net.getEdges():
            shape = edge.getShape()
            if shape:
                x_mean = sum(p[0] for p in shape) / len(shape)
                y_mean = sum(p[1] for p in shape) / len(shape)
                edge_positions[edge.getID()] = (x_mean, y_mean)
        
        # 结果容器
        selected_edges = set()
        
        # 对每个事故edge执行邻域抽样
        for spot_id in accident_spots:
            if spot_id not in edge_positions:
                print(f"⚠️ 警告：{spot_id} 在网络中未找到，跳过")
                continue
            
            spot_pos = edge_positions[spot_id]
            
            # 找到所有距离小于radius的edge
            nearby_edges = [
                edge_id for edge_id, pos in edge_positions.items()
                if distance(spot_pos, pos) <= radius and edge_id != spot_id
            ]
            
            if not nearby_edges:
                print(f"⚠️ {spot_id} 周围{radius}米内没有其他edge，跳过")
                continue
            
            # 随机抽取若干个
            chosen = random.sample(nearby_edges, min(num_per_accident, len(nearby_edges)))
            selected_edges.update(chosen)
        
        # 从选中的edges中随机选择5个作为本次案例
        if len(selected_edges) >= 5:
            exp_cases.append(random.sample(list(selected_edges), 5))
        else:
            exp_cases.append(list(selected_edges))
    
    # 输出到文件
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            for case in exp_cases:
                f.write(" ".join(case) + "\n")
        print(f"✅ 生成了 {len(exp_cases)} 个测试案例，保存到 {output_file}")
    
    return exp_cases


if __name__ == "__main__":
    # 生成测试案例
    cases = generate_accident_cases(
        net_file=SUMO_NET_FILE,
        accident_spots=SIMULATION_CONFIG["accident_spots"],
        radius=SIMULATION_CONFIG["radius"],
        num_per_accident=SIMULATION_CONFIG["num_per_accident"],
        num_cases=SIMULATION_CONFIG["num_experiments"],
        output_file=ACCIDENT_CASES_FILE
    )
