"""
配置文件 - 包含所有项目路径和参数配置
"""
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# SUMO 路网和路由文件（需要用户自行配置）
# 请将您的SUMO路网文件放在data目录下，或修改以下路径
SUMO_NET_FILE = os.path.join(DATA_DIR, "network.net.xml")  # 替换为实际路网文件
INPUT_ROUTE_FILE = os.path.join(DATA_DIR, "routes.rou.xml")  # 替换为实际路由文件
OUTPUT_ROUTE_FILE = os.path.join(RESULTS_DIR, "routes_with_ambulances.rou.xml")

# 医院位置数据
HOSPITAL_LOCATION_FILE = os.path.join(DATA_DIR, "Hospital_Location.csv")

# 事故点配置
ACCIDENT_CASES_FILE = os.path.join(DATA_DIR, "cases.txt")

# 实验结果目录
EXPERIMENT_RESULTS_DIR = os.path.join(RESULTS_DIR, "exp_res")

# 仿真参数
SIMULATION_CONFIG = {
    "accident_spots": ["200042649", "200040849", "200063134", "200002421", "200040901"],
    "radius": 1000,  # 事故点搜索半径（米）
    "num_per_accident": 5,  # 每个事故点附近随机选取的edge数量
    "ambulance_depart_time": 100.0,  # 救护车出发时间（秒）
    "ambulance_speed": 30,  # 救护车速度（m/s）
    "max_simulation_steps": 1200,  # 最大仿真步数
    "k_paths": 5,  # 每对医院-事故点计算的路径数
    "num_experiments": 20  # 实验次数
}

# 医院配置
HOSPITAL_CONFIG = {
    "num_hospitals": 6,
    "ambulances_per_hospital": 2
}

# 优化算法参数
OPTIMIZATION_CONFIG = {
    "algorithm": "hungarian",  # 匈牙利算法
    "objective": "min_max"  # 最小化最大完成时间
}

# 可视化参数
VISUALIZATION_CONFIG = {
    "figsize": (12, 10),
    "time_max": 800,  # 时间轴最大值（秒）
    "font_size": 10
}
