# 自定义模拟器对接指南

本文档说明如何将自研交通仿真器对接到排涝策略评估系统。

---

## 对接流程总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   与交通模拟器对接流程 (排涝项目)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  1. 基础准备                                                                  │
│     └─> 解析路网文件 (.net.xml) 获取edge和lane信息                          │
│     └─> 解析路由文件 (.rou.xml) 获取车辆路径                                │
│     └─> 实现在 `src/simulator_adapter.py` 适配器中                          │
│                                                                               │
│  2. 策略生成阶段 (generate_strategy.py)                                      │
│     └─> 不依赖模拟器，仅解析路由XML文件                                      │
│     └─> 统计车流量：计算每辆车路径与积水点组的交集                           │
│     └─> 输出：策略JSON文件 (batches排水顺序)                                 │
│                                                                               │
│  3. 仿真评估阶段 (evaluate_strategy.py)                                      │
│     【核心对接点】                                                            │
│                                                                               │
│     3.1 启动仿真                                                              │
│         └─> 调用: start_simulation(config_file, gui=False)                  │
│         └─> 功能: 加载路网、路由，初始化模拟器                               │
│                                                                               │
│     3.2 初始化积水状态                                                        │
│         └─> 根据当前批次确定已排水/未排水组                                  │
│         └─> 对每个lane调用: get_lane_vehicle_ids(lane_id)                   │
│         └─> 对每辆车调用: set_vehicle_max_speed(veh_id, speed)              │
│                                                                               │
│     3.3 仿真推进循环                                                          │
│         for step in range(simulation_steps):                                │
│             └─> 调用: simulation_step()                                      │
│             └─> 持续对积水区域车辆限速:                                      │
│                 - 遍历积水车道                                                │
│                 - 获取车道上的车辆ID                                          │
│                 - 设置每辆车的最大速度                                        │
│                                                                               │
│     3.4 性能指标测量 (在延迟点)                                               │
│         测量点 = 批次完成时间 + 评估延迟 (30/60/120秒)                       │
│                                                                               │
│         [指标1] 累计通过量                                                    │
│         └─> 调用: get_vehicle_position(veh_id) 或 get_vehicle_lane(veh_id) │
│         └─> 判断车辆是否已离开积水区域                                       │
│         └─> 累计计数所有离开积水区域的车辆                                   │
│                                                                               │
│         [指标2] 排队长度                                                      │
│         └─> 调用: get_lane_vehicle_count(lane_id)                           │
│         └─> 或: len(get_lane_vehicle_ids(lane_id))                          │
│         └─> 计算积水车道上的平均车辆数                                       │
│                                                                               │
│         [指标3] 平均速度                                                      │
│         └─> 调用: get_vehicle_speed(veh_id)                                 │
│         └─> 计算积水区域内所有车辆的平均速度                                 │
│                                                                               │
│     3.5 关闭仿真                                                              │
│         └─> 调用: close_simulation()                                         │
│         └─> 清理资源，准备下一次独立仿真                                     │
│                                                                               │
│  4. 对比分析阶段 (compare_strategies.py)                                     │
│     └─> 不依赖模拟器，仅处理评估结果JSON文件                                 │
│     └─> 生成图表和报告                                                       │
│                                                                               │
│  【关键特性】                                                                 │
│     • 静态评估：每个批次完成状态是独立仿真实验                                │
│     • 持续限速：每个仿真步都要对积水区域车辆设置速度限制                      │
│     • 多点测量：在一次仿真中的多个时间点测量指标                              │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 必须实现的接口函数

### 1. 启动与关闭

#### `start_simulation(config_file, gui=False)`
**功能**: 启动仿真器，加载路网和路由
**参数**:
- `config_file` (str): 配置文件路径 (如 `data/Core_500m_test.sumocfg`)
- `gui` (bool): 是否显示图形界面

**返回**: 无

**实现要点**:
```python
def start_simulation(config_file, gui=False):
    """
    启动自研仿真器
    - 解析配置文件获取路网和路由文件路径
    - 加载路网拓扑结构
    - 加载车辆路由信息
    - 初始化仿真引擎
    """
    # 伪代码示例
    config = parse_config(config_file)
    simulator.load_network(config['net_file'])
    simulator.load_routes(config['route_file'])
    simulator.initialize()
```

**SUMO对应**:
```python
traci.start([sumo, "-c", config_file, "--no-warnings"])
```

---

#### `close_simulation()`
**功能**: 关闭当前仿真，释放资源
**参数**: 无
**返回**: 无

**实现要点**:
```python
def close_simulation():
    """
    关闭仿真器
    - 清理车辆和路网状态
    - 释放内存资源
    - 准备下一次独立仿真
    """
    simulator.cleanup()
    simulator.close()
```

**SUMO对应**:
```python
traci.close()
```

---

### 2. 仿真推进

#### `simulation_step()`
**功能**: 推进仿真一个时间步 (通常1秒)
**参数**: 无
**返回**: 无

**实现要点**:
```python
def simulation_step():
    """
    仿真推进1秒
    - 更新所有车辆位置和速度
    - 处理交通信号灯
    - 处理车辆进入/离开路网
    """
    simulator.advance_time(1.0)  # 推进1秒
```

**SUMO对应**:
```python
traci.simulationStep()
```

**调用频率**: 每个仿真步调用一次 (通常200-2000次/仿真)

---

### 3. 车道查询

#### `get_lane_vehicle_ids(lane_id)`
**功能**: 获取指定车道上当前所有车辆的ID列表
**参数**:
- `lane_id` (str): 车道ID (如 `"200040454_0"`, `"200040454_1"`)

**返回**: `List[str]` - 车辆ID列表

**实现要点**:
```python
def get_lane_vehicle_ids(lane_id):
    """
    查询车道上的车辆
    - 遍历所有车辆
    - 判断车辆当前所在车道
    - 返回在目标车道上的车辆ID列表
    """
    vehicles = []
    for veh_id in simulator.get_all_vehicles():
        if simulator.get_vehicle_lane(veh_id) == lane_id:
            vehicles.append(veh_id)
    return vehicles
```

**SUMO对应**:
```python
traci.lane.getLastStepVehicleIDs(lane_id)
```

**调用频率**: 每个仿真步对每个积水车道调用 (9组×平均5车道 = ~45次/步)

---

#### `get_lane_vehicle_count(lane_id)`
**功能**: 获取车道上的车辆数量 (用于排队长度指标)
**参数**:
- `lane_id` (str): 车道ID

**返回**: `int` - 车辆数量

**实现要点**:
```python
def get_lane_vehicle_count(lane_id):
    """
    快速查询车道车辆数
    - 如果模拟器内部维护了车道-车辆映射，直接返回长度
    - 否则调用 get_lane_vehicle_ids() 并返回长度
    """
    return len(get_lane_vehicle_ids(lane_id))
```

**SUMO对应**:
```python
traci.lane.getLastStepVehicleNumber(lane_id)
```

---

### 4. 车辆控制

#### `set_vehicle_max_speed(veh_id, max_speed)`
**功能**: 设置车辆的最大速度限制
**参数**:
- `veh_id` (str): 车辆ID
- `max_speed` (float): 最大速度 (m/s)

**返回**: 无

**实现要点**:
```python
def set_vehicle_max_speed(veh_id, max_speed):
    """
    限制车辆速度
    - 设置车辆的速度上限
    - 车辆实际速度不会超过此值
    - 车辆加速时受此限制约束
    
    重要：
    - 积水区域: max_speed = 1.5 m/s
    - 正常区域: max_speed = 15 m/s (或不设限制)
    """
    vehicle = simulator.get_vehicle(veh_id)
    vehicle.set_max_speed(max_speed)
```

**SUMO对应**:
```python
traci.vehicle.setMaxSpeed(veh_id, max_speed)
```

**调用频率**: 每个仿真步对积水区域的所有车辆调用 (可能数百次/步)

---

### 5. 车辆查询

#### `get_vehicle_speed(veh_id)`
**功能**: 获取车辆当前速度
**参数**:
- `veh_id` (str): 车辆ID

**返回**: `float` - 速度 (m/s)

**实现要点**:
```python
def get_vehicle_speed(veh_id):
    """
    查询车辆瞬时速度
    - 返回车辆当前行驶速度 (m/s)
    - 用于计算平均速度指标
    """
    vehicle = simulator.get_vehicle(veh_id)
    return vehicle.get_speed()
```

**SUMO对应**:
```python
traci.vehicle.getSpeed(veh_id)
```

---

#### `get_vehicle_position(veh_id)`
**功能**: 获取车辆位置 (用于判断是否离开积水区域)
**参数**:
- `veh_id` (str): 车辆ID

**返回**: `Tuple[float, float]` - (x, y) 坐标，或返回edge/lane ID

**实现要点**:
```python
def get_vehicle_position(veh_id):
    """
    查询车辆位置
    
    选项1: 返回坐标
    return (x, y)
    
    选项2: 返回所在edge ID (推荐，用于判断是否在积水区域)
    return vehicle.get_current_edge_id()
    
    选项3: 返回所在lane ID
    return vehicle.get_current_lane_id()
    """
    vehicle = simulator.get_vehicle(veh_id)
    return vehicle.get_current_edge_id()
```

**SUMO对应**:
```python
# 方式1: 坐标
traci.vehicle.getPosition(veh_id)

# 方式2: Road ID (推荐)
traci.vehicle.getRoadID(veh_id)

# 方式3: Lane ID
traci.vehicle.getLaneID(veh_id)
```

---

#### `get_vehicle_lane(veh_id)`
**功能**: 获取车辆当前所在车道ID
**参数**:
- `veh_id` (str): 车辆ID

**返回**: `str` - 车道ID

**实现要点**:
```python
def get_vehicle_lane(veh_id):
    """
    查询车辆所在车道
    - 返回车道完整ID (如 "200040454_0")
    - 用于判断车辆是否在积水车道上
    """
    vehicle = simulator.get_vehicle(veh_id)
    return vehicle.get_lane_id()
```

**SUMO对应**:
```python
traci.vehicle.getLaneID(veh_id)
```

---

### 6. 路网解析辅助 (可选，在评估外部实现)

#### `edge_to_lanes(net_file, edge_id)`
**功能**: 将edge ID转换为lane ID列表
**参数**:
- `net_file` (str): 路网文件路径
- `edge_id` (str): edge ID (如 `"200040454"`)

**返回**: `List[str]` - 车道ID列表 (如 `["200040454_0", "200040454_1"]`)

**实现要点**:
```python
def edge_to_lanes(net_file, edge_id):
    """
    解析路网文件，将edge转换为lanes
    - 解析 .net.xml 文件
    - 查找指定edge
    - 返回该edge下所有lane的ID列表
    
    注意：
    - 本项目中积水点已经是edge ID
    - 需要转换为lane ID才能查询车辆
    """
    net = parse_network_file(net_file)
    edge = net.get_edge(edge_id)
    return [lane.id for lane in edge.get_lanes()]
```

**SUMO对应**:
```python
import sumolib
net = sumolib.net.readNet(net_file)
edge = net.getEdge(edge_id)
lanes = [lane.getID() for lane in edge.getLanes()]
```

---

## 关键实现逻辑

### 逻辑1: 持续限速机制

**为什么每步都要设置限速？**
- 新车辆不断进入积水区域
- 必须确保所有在积水区域的车辆都受限速

**代码示例** (在 `evaluate_strategy.py` 中):
```python
# 积水车道列表 (在仿真开始前计算)
flooded_lanes = []
for group in flooded_groups:  # 未排水的组
    flooded_lanes.extend(group_lanes[group])

# 仿真循环
for step in range(total_steps):
    simulation_step()  # 推进1秒
    
    # 对积水区域的所有车辆限速
    for lane_id in flooded_lanes:
        vehicle_ids = get_lane_vehicle_ids(lane_id)
        for veh_id in vehicle_ids:
            set_vehicle_max_speed(veh_id, flooded_speed)  # 1.5 m/s
```

**性能优化建议**:
- 如果模拟器支持"区域限速"，可一次性设置整个lane的限速
- 如果支持"持久化限速"，设置一次后自动应用于后续进入的车辆

---

### 逻辑2: 累计通过量计算

**定义**: 从仿真开始到当前时刻，驶离积水区域的车辆总数

**实现方式**:
```python
# 初始化
left_vehicles = set()  # 记录已离开的车辆
all_flooded_lanes = set(flooded_lanes)  # 积水车道集合

# 每个测量点
for step in range(total_steps):
    simulation_step()
    
    # 在测量点记录
    if step in measurement_steps:
        for veh_id in simulator.get_all_vehicles():
            current_lane = get_vehicle_lane(veh_id)
            # 如果车辆不在积水车道，且之前可能在积水区域
            if current_lane not in all_flooded_lanes:
                left_vehicles.add(veh_id)
        
        cumulative_throughput = len(left_vehicles)
```

**注意**:
- 需要跟踪所有车辆的历史位置，判断是否曾经在积水区域
- 或者更简单：统计不在积水区域的所有车辆数 (适用于所有车辆都必经积水区域的场景)

---

### 逻辑3: 排队长度计算

**定义**: 积水车道上的平均车辆数

**实现方式**:
```python
def calculate_queue_length(flooded_lanes):
    """
    计算积水区域排队长度
    """
    total_vehicles = 0
    for lane_id in flooded_lanes:
        total_vehicles += get_lane_vehicle_count(lane_id)
    
    avg_queue_length = total_vehicles / len(flooded_lanes)
    return avg_queue_length
```

---

### 逻辑4: 平均速度计算

**定义**: 积水区域内所有车辆的平均速度

**实现方式**:
```python
def calculate_avg_speed(flooded_lanes):
    """
    计算积水区域平均速度
    """
    speeds = []
    for lane_id in flooded_lanes:
        vehicle_ids = get_lane_vehicle_ids(lane_id)
        for veh_id in vehicle_ids:
            speed = get_vehicle_speed(veh_id)
            speeds.append(speed)
    
    if len(speeds) > 0:
        return sum(speeds) / len(speeds)
    else:
        return 0.0
```

---

## 数据格式要求

### Edge ID 与 Lane ID

**本项目积水点数据使用 Edge ID**:
```json
"waterlogging_points": {
  "g1": ["200040454", "200041869", ...],  # Edge IDs
  ...
}
```

**需要转换为 Lane ID**:
```
Edge: "200040454"
  ├─ Lane 0: "200040454_0"
  ├─ Lane 1: "200040454_1"
  └─ Lane 2: "200040454_2"
```

**转换代码** (在 `evaluate_strategy.py` 的 `get_group_lanes()` 函数):
```python
def get_group_lanes(net_file, flood_points):
    """
    将积水点edge ID转换为lane ID列表
    """
    group_lanes = {}
    for group, edges in flood_points.items():
        lanes = []
        for edge_id in edges:
            # 调用适配器函数
            lane_ids = edge_to_lanes(net_file, edge_id)
            lanes.extend(lane_ids)
        group_lanes[group] = lanes
    return group_lanes
```

---

### 速度单位

**统一使用 m/s**:
- 积水速度: `1.5 m/s` (约5.4 km/h)
- 正常速度: `15 m/s` (约54 km/h)

**如果模拟器使用其他单位 (如 km/h)**:
```python
def set_vehicle_max_speed(veh_id, max_speed_ms):
    """
    max_speed_ms: 单位 m/s
    """
    max_speed_kmh = max_speed_ms * 3.6  # 转换为 km/h
    vehicle.set_max_speed(max_speed_kmh)
```

---

### 时间步长

**本项目假设时间步长 = 1秒**:
- `simulation_step()` 推进1秒
- `simulation_steps = 200` 表示仿真200秒

**如果模拟器时间步长不是1秒**:
```python
# 假设模拟器时间步长为0.1秒
def simulation_step():
    for _ in range(10):  # 调用10次推进1秒
        simulator.advance_time(0.1)
```

---

## 适配器模板使用

我们提供了 `src/simulator_adapter.py` 模板文件，包含所有必需接口的函数签名。

**步骤1**: 打开 `src/simulator_adapter.py`

**步骤2**: 根据您的模拟器API实现每个函数

**步骤3**: 在 `evaluate_strategy.py` 中导入适配器:
```python
# 替换原有的 traci 导入
# import traci

# 改为导入适配器
from simulator_adapter import (
    start_simulation,
    close_simulation,
    simulation_step,
    get_lane_vehicle_ids,
    set_vehicle_max_speed,
    get_vehicle_speed,
    get_vehicle_lane
)
```

**步骤4**: 替换代码中的 `traci.xxx` 调用为适配器函数

---

## 测试建议

### 单元测试

**测试1: 启动关闭**
```python
def test_start_close():
    start_simulation("data/Core_500m_test.sumocfg")
    close_simulation()
    print("✓ 启动关闭测试通过")
```

**测试2: 单步推进**
```python
def test_simulation_step():
    start_simulation("data/Core_500m_test.sumocfg")
    for i in range(10):
        simulation_step()
    close_simulation()
    print("✓ 仿真推进测试通过")
```

**测试3: 车辆查询**
```python
def test_vehicle_query():
    start_simulation("data/Core_500m_test.sumocfg")
    for _ in range(50):  # 推进50秒，确保有车辆进入
        simulation_step()
    
    lane_id = "200040454_0"
    vehicle_ids = get_lane_vehicle_ids(lane_id)
    print(f"车道 {lane_id} 上有 {len(vehicle_ids)} 辆车")
    
    if len(vehicle_ids) > 0:
        veh_id = vehicle_ids[0]
        speed = get_vehicle_speed(veh_id)
        print(f"车辆 {veh_id} 速度: {speed:.2f} m/s")
    
    close_simulation()
    print("✓ 车辆查询测试通过")
```

**测试4: 限速控制**
```python
def test_speed_control():
    start_simulation("data/Core_500m_test.sumocfg")
    for _ in range(50):
        simulation_step()
    
    lane_id = "200040454_0"
    vehicle_ids = get_lane_vehicle_ids(lane_id)
    
    if len(vehicle_ids) > 0:
        veh_id = vehicle_ids[0]
        set_vehicle_max_speed(veh_id, 1.5)  # 限速1.5 m/s
        
        for _ in range(10):
            simulation_step()
        
        speed = get_vehicle_speed(veh_id)
        assert speed <= 1.6, f"限速失败: 速度{speed} > 1.5"
        print(f"✓ 限速测试通过 (速度={speed:.2f} m/s)")
    
    close_simulation()
```

---

### 集成测试

**完整评估测试**:
```bash
# 运行完整流程，使用适配器
cd src
python evaluate_strategy.py -s ../results/strategies_*/best_strategy.json
```

**预期输出**:
- 每个批次的评估结果
- 性能指标数值合理 (通过量>0，排队长度<1000，速度在0-15之间)
- 无报错

---

## 常见问题

### Q1: 模拟器不支持设置单车辆限速怎么办？
**A**: 如果只能设置车道限速，可以：
1. 在仿真开始前修改路网文件，设置积水车道的限速属性
2. 或在仿真中动态修改车道限速 (如果支持)

### Q2: 如何处理车辆ID格式不同？
**A**: 在适配器中进行ID转换：
```python
def convert_vehicle_id_from_simulator(sim_veh_id):
    # 将模拟器ID转换为本项目使用的格式
    return f"veh_{sim_veh_id}"

def convert_vehicle_id_to_simulator(veh_id):
    # 将本项目ID转换为模拟器格式
    return int(veh_id.replace("veh_", ""))
```

### Q3: 模拟器使用不同的路网格式怎么办？
**A**: 
- 如果模拟器不兼容SUMO的.net.xml格式，需要转换路网文件
- 或者在适配器中实现路网解析逻辑，建立edge-lane映射表

### Q4: 性能问题：每步查询所有车辆太慢？
**A**: 优化建议：
1. 在模拟器内部维护车道-车辆索引
2. 只查询积水车道，不遍历全部车辆
3. 使用批量API一次性获取多个车道的车辆信息

---

## 参考资料

- SUMO TraCI文档: https://sumo.dlr.de/docs/TraCI.html
- 本项目代码: `src/evaluate_strategy.py` (查看如何使用SUMO接口)
- 适配器模板: `src/simulator_adapter.py`

---

**更新时间**: 2026-02-03  
**版本**: v1.0
