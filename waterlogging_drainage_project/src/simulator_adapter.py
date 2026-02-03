"""
自定义交通仿真器适配器模板

本文件提供与自研仿真器对接的接口函数模板。
请根据您的仿真器API实现以下所有函数。

使用说明:
1. 根据您的仿真器API填充每个函数的实现
2. 在 evaluate_strategy.py 中导入这些函数替换 traci
3. 运行测试验证适配器工作正常

参考文档: ../SIMULATOR_INTEGRATION.md
"""

# ==============================================================================
# 1. 仿真生命周期管理
# ==============================================================================

def start_simulation(config_file, gui=False):
    """
    启动仿真器，加载路网和路由
    
    参数:
        config_file (str): 配置文件路径 (如 "data/Core_500m_test.sumocfg")
        gui (bool): 是否显示图形界面 (默认False)
    
    返回:
        无
    
    实现要点:
        - 解析配置文件获取路网和路由文件路径
        - 加载路网拓扑结构
        - 加载车辆路由信息
        - 初始化仿真引擎
    
    SUMO参考:
        traci.start([sumo, "-c", config_file, "--no-warnings"])
    """
    # TODO: 实现您的仿真器启动逻辑
    raise NotImplementedError("请实现 start_simulation() 函数")


def close_simulation():
    """
    关闭当前仿真，释放资源
    
    参数:
        无
    
    返回:
        无
    
    实现要点:
        - 清理车辆和路网状态
        - 释放内存资源
        - 准备下一次独立仿真
    
    SUMO参考:
        traci.close()
    """
    # TODO: 实现您的仿真器关闭逻辑
    raise NotImplementedError("请实现 close_simulation() 函数")


def simulation_step():
    """
    推进仿真一个时间步 (1秒)
    
    参数:
        无
    
    返回:
        无
    
    实现要点:
        - 更新所有车辆位置和速度
        - 处理交通信号灯
        - 处理车辆进入/离开路网
        - 如果模拟器时间步不是1秒，需要循环调用多次
    
    SUMO参考:
        traci.simulationStep()
    
    调用频率:
        每个仿真步调用一次 (通常200-2000次/仿真)
    """
    # TODO: 实现仿真推进逻辑
    raise NotImplementedError("请实现 simulation_step() 函数")


# ==============================================================================
# 2. 车道查询接口
# ==============================================================================

def get_lane_vehicle_ids(lane_id):
    """
    获取指定车道上当前所有车辆的ID列表
    
    参数:
        lane_id (str): 车道ID (如 "200040454_0")
    
    返回:
        List[str]: 车辆ID列表
    
    实现要点:
        - 遍历所有车辆或使用车道-车辆索引
        - 判断车辆当前所在车道
        - 返回在目标车道上的车辆ID列表
    
    SUMO参考:
        traci.lane.getLastStepVehicleIDs(lane_id)
    
    调用频率:
        每个仿真步对每个积水车道调用 (~45次/步)
    """
    # TODO: 实现车道车辆查询逻辑
    raise NotImplementedError("请实现 get_lane_vehicle_ids() 函数")


def get_lane_vehicle_count(lane_id):
    """
    获取车道上的车辆数量 (用于排队长度指标)
    
    参数:
        lane_id (str): 车道ID
    
    返回:
        int: 车辆数量
    
    实现要点:
        - 快速返回车道上的车辆数
        - 可直接调用 len(get_lane_vehicle_ids(lane_id))
        - 或使用模拟器内部的快速查询接口
    
    SUMO参考:
        traci.lane.getLastStepVehicleNumber(lane_id)
    """
    # 简单实现 (可优化)
    return len(get_lane_vehicle_ids(lane_id))


# ==============================================================================
# 3. 车辆控制接口
# ==============================================================================

def set_vehicle_max_speed(veh_id, max_speed):
    """
    设置车辆的最大速度限制
    
    参数:
        veh_id (str): 车辆ID
        max_speed (float): 最大速度 (m/s)
    
    返回:
        无
    
    实现要点:
        - 设置车辆的速度上限
        - 车辆实际速度不会超过此值
        - 车辆加速时受此限制约束
        - 积水区域: max_speed = 1.5 m/s
        - 正常区域: max_speed = 15 m/s (或不设限)
    
    注意:
        - 速度单位统一为 m/s
        - 如果模拟器使用其他单位 (如 km/h)，需要转换
    
    SUMO参考:
        traci.vehicle.setMaxSpeed(veh_id, max_speed)
    
    调用频率:
        每个仿真步对积水区域的所有车辆调用 (可能数百次/步)
    """
    # TODO: 实现车辆限速逻辑
    raise NotImplementedError("请实现 set_vehicle_max_speed() 函数")


# ==============================================================================
# 4. 车辆状态查询接口
# ==============================================================================

def get_vehicle_speed(veh_id):
    """
    获取车辆当前速度
    
    参数:
        veh_id (str): 车辆ID
    
    返回:
        float: 速度 (m/s)
    
    实现要点:
        - 返回车辆当前行驶速度 (m/s)
        - 用于计算平均速度指标
        - 速度单位统一为 m/s
    
    SUMO参考:
        traci.vehicle.getSpeed(veh_id)
    """
    # TODO: 实现车辆速度查询逻辑
    raise NotImplementedError("请实现 get_vehicle_speed() 函数")


def get_vehicle_position(veh_id):
    """
    获取车辆位置 (用于判断是否离开积水区域)
    
    参数:
        veh_id (str): 车辆ID
    
    返回:
        str 或 Tuple[float, float]: 
            - 推荐返回 edge ID (如 "200040454")
            - 或返回 (x, y) 坐标
    
    实现要点:
        - 推荐返回车辆当前所在的 edge ID
        - 便于判断车辆是否在积水区域
        - 如果只能返回坐标，需要额外逻辑判断所在edge
    
    SUMO参考:
        traci.vehicle.getRoadID(veh_id)  # 返回 edge ID (推荐)
        traci.vehicle.getPosition(veh_id)  # 返回 (x, y)
    """
    # TODO: 实现车辆位置查询逻辑
    raise NotImplementedError("请实现 get_vehicle_position() 函数")


def get_vehicle_lane(veh_id):
    """
    获取车辆当前所在车道ID
    
    参数:
        veh_id (str): 车辆ID
    
    返回:
        str: 车道ID (如 "200040454_0")
    
    实现要点:
        - 返回车道完整ID
        - 用于判断车辆是否在积水车道上
    
    SUMO参考:
        traci.vehicle.getLaneID(veh_id)
    """
    # TODO: 实现车辆车道查询逻辑
    raise NotImplementedError("请实现 get_vehicle_lane() 函数")


# ==============================================================================
# 5. 路网解析辅助接口
# ==============================================================================

def edge_to_lanes(net_file, edge_id):
    """
    将edge ID转换为lane ID列表
    
    参数:
        net_file (str): 路网文件路径
        edge_id (str): edge ID (如 "200040454")
    
    返回:
        List[str]: 车道ID列表 (如 ["200040454_0", "200040454_1"])
    
    实现要点:
        - 解析路网文件
        - 查找指定edge
        - 返回该edge下所有lane的ID列表
        - 本项目中积水点是edge ID，需转换为lane ID才能查询车辆
    
    SUMO参考:
        import sumolib
        net = sumolib.net.readNet(net_file)
        edge = net.getEdge(edge_id)
        lanes = [lane.getID() for lane in edge.getLanes()]
    
    注意:
        - 此函数在仿真外部调用 (仅在初始化时)
        - 可以预先计算好映射表缓存结果
    """
    # TODO: 实现edge到lane的转换逻辑
    raise NotImplementedError("请实现 edge_to_lanes() 函数")


# ==============================================================================
# 6. 可选接口 (用于性能优化)
# ==============================================================================

def get_all_vehicles():
    """
    获取仿真中所有车辆的ID列表 (可选)
    
    返回:
        List[str]: 所有车辆ID列表
    
    用途:
        - 用于计算累计通过量
        - 遍历所有车辆判断位置
    
    SUMO参考:
        traci.vehicle.getIDList()
    """
    # TODO: (可选) 实现全部车辆查询逻辑
    raise NotImplementedError("请实现 get_all_vehicles() 函数 (可选)")


def set_lane_max_speed(lane_id, max_speed):
    """
    设置整个车道的速度限制 (可选)
    
    参数:
        lane_id (str): 车道ID
        max_speed (float): 最大速度 (m/s)
    
    用途:
        - 性能优化: 一次性设置整个车道限速
        - 替代对每辆车单独设置限速
        - 如果模拟器支持车道级限速，推荐使用
    
    SUMO参考:
        traci.lane.setMaxSpeed(lane_id, max_speed)
    """
    # TODO: (可选) 实现车道限速逻辑
    raise NotImplementedError("请实现 set_lane_max_speed() 函数 (可选)")


# ==============================================================================
# 7. 单元测试函数 (建议保留)
# ==============================================================================

def test_adapter():
    """
    测试适配器所有接口是否正常工作
    
    运行方式:
        python simulator_adapter.py
    """
    print("="*80)
    print("适配器单元测试".center(80))
    print("="*80)
    
    config_file = "../data/Core_500m_test.sumocfg"
    
    try:
        # 测试1: 启动关闭
        print("\n[测试1] 启动关闭仿真...")
        start_simulation(config_file, gui=False)
        close_simulation()
        print("✓ 通过")
        
        # 测试2: 仿真推进
        print("\n[测试2] 仿真推进...")
        start_simulation(config_file, gui=False)
        for i in range(10):
            simulation_step()
        print(f"✓ 通过 (推进10步)")
        
        # 测试3: 车辆查询
        print("\n[测试3] 车辆查询...")
        for _ in range(50):  # 推进50秒确保有车辆
            simulation_step()
        
        test_lane = "200040454_0"
        vehicle_ids = get_lane_vehicle_ids(test_lane)
        count = get_lane_vehicle_count(test_lane)
        print(f"  车道 {test_lane}: {count} 辆车")
        print(f"✓ 通过")
        
        # 测试4: 车辆控制
        if len(vehicle_ids) > 0:
            print("\n[测试4] 车辆控制...")
            veh_id = vehicle_ids[0]
            
            # 获取初始速度
            speed_before = get_vehicle_speed(veh_id)
            print(f"  车辆 {veh_id} 初始速度: {speed_before:.2f} m/s")
            
            # 设置限速
            set_vehicle_max_speed(veh_id, 1.5)
            
            # 推进仿真观察效果
            for _ in range(10):
                simulation_step()
            
            speed_after = get_vehicle_speed(veh_id)
            print(f"  限速后速度: {speed_after:.2f} m/s")
            
            if speed_after <= 1.6:
                print(f"✓ 通过 (限速生效)")
            else:
                print(f"⚠ 警告: 限速可能未生效 (速度 {speed_after:.2f} > 1.5)")
        
        # 测试5: 位置查询
        if len(vehicle_ids) > 0:
            print("\n[测试5] 位置查询...")
            veh_id = vehicle_ids[0]
            position = get_vehicle_position(veh_id)
            lane = get_vehicle_lane(veh_id)
            print(f"  车辆 {veh_id}:")
            print(f"    位置: {position}")
            print(f"    车道: {lane}")
            print(f"✓ 通过")
        
        # 测试6: Edge转Lane
        print("\n[测试6] Edge到Lane转换...")
        net_file = "../data/network/new_add_light.net.xml"
        test_edge = "200040454"
        lanes = edge_to_lanes(net_file, test_edge)
        print(f"  Edge {test_edge} -> {len(lanes)} 条车道")
        print(f"  车道列表: {lanes[:3]}...")  # 显示前3条
        print(f"✓ 通过")
        
        close_simulation()
        
        print("\n" + "="*80)
        print("所有测试通过！适配器可以使用。".center(80))
        print("="*80)
        
    except NotImplementedError as e:
        print(f"\n✗ 测试失败: {e}")
        print("请先实现所有必需的接口函数")
    except Exception as e:
        print(f"\n✗ 测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            close_simulation()
        except:
            pass


# ==============================================================================
# 8. 使用示例
# ==============================================================================

def example_usage():
    """
    展示如何在评估代码中使用适配器
    """
    print("\n使用示例代码:\n")
    print("""
# 在 evaluate_strategy.py 中:

# 1. 导入适配器 (替代 traci)
from simulator_adapter import (
    start_simulation,
    close_simulation,
    simulation_step,
    get_lane_vehicle_ids,
    set_vehicle_max_speed,
    get_vehicle_speed,
    get_vehicle_lane
)

# 2. 启动仿真
start_simulation(config_file, gui=False)

# 3. 设置积水区域车速限制
flooded_lanes = ["200040454_0", "200040454_1", ...]
for step in range(200):
    simulation_step()
    
    # 对积水区域的车辆持续限速
    for lane_id in flooded_lanes:
        vehicle_ids = get_lane_vehicle_ids(lane_id)
        for veh_id in vehicle_ids:
            set_vehicle_max_speed(veh_id, 1.5)  # 积水速度
    
    # 在测量点计算指标
    if step in [30, 60, 120]:
        # 计算排队长度
        queue = sum(len(get_lane_vehicle_ids(l)) for l in flooded_lanes)
        
        # 计算平均速度
        speeds = []
        for lane_id in flooded_lanes:
            for veh_id in get_lane_vehicle_ids(lane_id):
                speeds.append(get_vehicle_speed(veh_id))
        avg_speed = sum(speeds) / len(speeds) if speeds else 0

# 4. 关闭仿真
close_simulation()
    """)


# ==============================================================================
# 主程序入口
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 运行测试
        test_adapter()
    else:
        # 显示使用说明
        print(__doc__)
        example_usage()
        print("\n提示: 运行 'python simulator_adapter.py test' 进行适配器测试")
