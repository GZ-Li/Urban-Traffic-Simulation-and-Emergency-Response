# 扫雪策略生成系统

## 项目文件结构

```
snow_plowing_20260131/
├── config.json                # 主配置文件 (仅包含关键参数)
├── regions.json               # 区域边界配置 (外部文件)
├── main.py                    # 简单主入口 (仅策略生成)
├── generate_strategies.py     # 独立策略生成器
├── evaluate_strategies.py     # 独立SUMO评估器
├── compare_results.py         # 独立对比分析器
├── strategies/                # 策略算法模块
│   ├── __init__.py
│   ├── greedy_strategy.py    # 贪心策略
│   └── random_strategy.py    # 随机策略
└── results/                   # 输出目录
```

## 策略生成架构

```
输入:
  config.json (扫雪车数量, 速度, 最大时间) + regions.json (区域边界)
       ↓
┌──────────────────────────────────────────────────────────────┐
│  核心流程                                                        │
├──────────────────────────────────────────────────────────────┤
│  1. 加载路网     → 解析.net.xml, 构建NetworkX图                │
│  2. 加载交通流   → 统计每条边的车辆数 (仅贪心策略)                │
│  3. 分配区域     → 根据坐标将边映射到区域                        │
│  4. 初始化       → 将所有扫雪车设置到unified_start_edge         │
│  5. 生成路径     → 策略特定逻辑 (见下方)                         │
│  6. 记录结果     → 保存清扫时间线                                │
└──────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│  策略对比                                                       │
├─────────────────────────────────────────────────────────────┤
│  贪心策略                        随机策略                        │
│  • 按traffic_flow降序排序        • 随机打乱道路顺序             │
│  • 优先清扫高流量道路             • 按打乱后的顺序清扫           │
│  • nx.shortest_path()           • nx.shortest_path()        │
│  • 清扫直到max_time              • 清扫直到max_time           │
└─────────────────────────────────────────────────────────────┘
       ↓
输出:
  {strategy_name, trucks: [{cleaning_records}], summary}
  → results/YYYYMMDD_HHMMSS/strategy_name.json

关键细节:
  • U型转弯逻辑: lane_count % 2 == 0 → 返回from_node
  • 传送机制: 连续10次路径规划失败后跳过
  • 时间计算: travel_time = dist/speed_pass, clean_time = dist/speed_clean
```

## 核心特性

### 简化配置

**config.json** - 仅包含关键参数:
```json
{
  "snowplow_parameters": {
    "num_trucks": 5,              // 关键: 扫雪车数量
    "num_regions": 5,             // 关键: 区域数量 (必须与num_trucks相同)
    "regions_file": "regions.json", // 外部区域配置文件
    "speed_clean": 3,             // 清扫速度 (米/秒)
    "speed_pass": 10,             // 通行速度 (米/秒)
    "max_time_minutes": 300       // 最大清扫时间 (分钟)
  }
}
```

**regions.json** - 详细区域边界配置 (独立文件):
```json
{
  "regions": [
    {
      "id": "region1",
      "bounds": {"x_min": ..., "x_max": ..., "y_min": ..., "y_max": ...}
    }
  ]
}
```

## 与自研交通模拟器对接流程

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 扫雪系统与交通模拟器对接架构                                                      │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│ 1. 路网数据转换与加载                                                          │
│    ├─> [模拟器] → 导出路网数据(.net.xml格式或自定义格式)                        │
│    ├─> [扫雪系统] GreedyStrategy.load_network()                            │
│    │   └─> 解析路网: edge_id, from_node, to_node, length, lane_count      │
│    │   └─> 构建NetworkX图: G.add_edge(from, to, edge_id, length)          │
│    └─> 位置文件: strategies/greedy_strategy.py (Line 33-67)               │
│                                                                            │
│ 2. 交通流量数据获取                                                            │
│    ├─> [模拟器] → 实时统计车辆经过边的次数                                     │
│    │   └─> 方案A: 导出route文件(.rou.xml) 统计每条边的vehicle数量            │
│    │   └─> 方案B: 通过API实时查询: get_edge_vehicle_count(edge_id)         │
│    ├─> [扫雪系统] GreedyStrategy.load_traffic_flow()                       │
│    │   └─> 解析: traffic_flow[edge_id] = vehicle_count                    │
│    └─> 位置文件: strategies/greedy_strategy.py (Line 69-84)               │
│                                                                            │
│ 3. 路径规划与策略生成                                                          │
│    ├─> [扫雪系统] generate_strategies.py                                   │
│    │   ├─> Greedy策略: 按traffic_flow排序，优先清扫高流量道路               │
│    │   ├─> Random策略: 随机选择道路清扫                                     │
│    │   └─> 核心算法:                                                        │
│    │       • nx.shortest_path() → 计算车辆到目标道路的最短路径              │
│    │       • travel_time = distance / speed_pass                          │
│    │       • clean_time = edge_length / speed_clean                       │
│    │       • 记录清扫时间线: [{edge_id, start_time, end_time}]             │
│    └─> 输出: results/strategies_YYYYMMDD/greedy_strategy.json             │
│                                                                            │
│ 4. 模拟器仿真验证                                                              │
│    ├─> [扫雪系统] evaluate_strategies.py                                   │
│    │   └─> 读取策略JSON: truck_id → [cleaning_records]                    │
│    ├─> [模拟器对接接口] 创建扫雪车实体                                         │
│    │   ├─> API: add_vehicle(vehicle_id, type="snowplow", route_edges)    │
│    │   ├─> 设置起点: unified_start_edge (统一起点)                          │
│    │   ├─> 设置路由: 根据cleaning_records中的edge序列                       │
│    │   └─> 车辆属性: speed_clean(清扫速度), speed_pass(通行速度)             │
│    ├─> [模拟器] 实时模拟                                                      │
│    │   ├─> 每个仿真步(step): 更新车辆位置                                   │
│    │   ├─> API查询: get_vehicle_position(vehicle_id) → (edge_id, pos)    │
│    │   ├─> 判断状态: 清扫中(speed=speed_clean) vs 通行中(speed=speed_pass) │
│    │   └─> 记录实际到达时间: actual_arrival_time[edge_id]                  │
│    ├─> [扫雪系统] 收集仿真数据                                                │
│    │   └─> 对比: 预测时间 vs 实际时间                                        │
│    └─> 输出: results/evaluation_*.json                                    │
│                                                                            │
│ 5. 道路状态动态更新 (高级功能)                                                  │
│    ├─> [扫雪系统] → 清扫完成事件: {edge_id, completion_time}                │
│    ├─> [模拟器] 接收清扫完成通知                                              │
│    │   └─> API: update_edge_condition(edge_id, snow_cleared=True)        │
│    │   └─> 恢复道路速度: maxSpeed × clearance_factor (0.5 → 1.0)          │
│    └─> [模拟器] 更新交通流: 车辆重新路由，避开积雪道路                          │
│                                                                            │
│ 6. 结果对比与评估                                                              │
│    ├─> [扫雪系统] compare_results.py                                       │
│    │   ├─> 指标1: 清扫覆盖率 = cleaned_edges / total_edges                │
│    │   ├─> 指标2: 平均响应时间 = avg(实际到达时间 - 策略预测时间)             │
│    │   ├─> 指标3: 高流量道路优先率 (Greedy vs Random)                       │
│    │   └─> 生成对比图表: matplotlib可视化                                   │
│    └─> 输出: results/comparison_YYYYMMDD.png                              │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ 关键对接接口定义 (需在自研模拟器中实现)                                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│ 【数据导出接口】                                                               │
│   • export_network(format="networkx") → 返回路网图结构                      │
│   • export_traffic_flow(time_window) → 返回边流量统计字典                   │
│                                                                            │
│ 【车辆控制接口】                                                               │
│   • add_snowplow(truck_id, start_edge, route_plan) → 创建扫雪车            │
│   • set_vehicle_speed(vehicle_id, speed) → 动态调整速度                    │
│   • get_vehicle_state(vehicle_id) → {edge_id, position, speed, status}   │
│                                                                            │
│ 【道路状态接口】                                                               │
│   • update_edge_snow_state(edge_id, cleared_ratio) → 更新积雪状态          │
│   • get_edge_condition(edge_id) → {snow_depth, speed_factor, passable}   │
│                                                                            │
│ 【仿真控制接口】                                                               │
│   • step() → 推进一个仿真步                                                  │
│   • get_current_time() → 返回当前仿真时间(秒)                               │
│   • close() → 关闭仿真器                                                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

参考实现:
  • SUMO版本: evaluate_strategies.py (使用traci接口)
  • 策略生成: generate_strategies.py (独立于模拟器)
  • 结果分析: compare_results.py (可视化对比)
```

## 扫雪策略生成关键代码实现

```
┌─────────────────────────────────────────────────────────────┐
│ 策略生成模块                                                   │
├─────────────────────────────────────────────────────────────┤
│ strategies/greedy_strategy.py                               │
│ ├── GreedyStrategy - 贪心策略生成器                          │
│ │   ├── __init__() - 初始化配置与区域                       │
│ │   ├── load_network() - 加载路网构建图                      │
│ │   │   └─> 解析.net.xml → NetworkX图结构                   │
│ │   │   └─> edge_data = {edge_id: {from, to, length...}}   │
│ │   ├── load_traffic_flow() - 统计交通流量                  │
│ │   │   └─> 遍历.rou.xml中所有车辆路由                      │
│ │   │   └─> traffic_flow[edge_id] = 车辆数                 │
│ │   ├── assign_region_by_location() - 区域分配              │
│ │   │   └─> 根据坐标判断边所属区域                          │
│ │   ├── get_edge_center() - 计算边中心坐标                  │
│ │   │   └─> 从shape字符串提取中点                           │
│ │   ├── generate() - 主生成流程 ⭐                          │
│ │   │   └─> 调用load_network() + load_traffic_flow()      │
│ │   │   └─> 初始化truck_states (每区域一辆车)               │
│ │   │   └─> 贪心主循环:                                     │
│ │   │       • 选当前区域最高流量未清扫道路                   │
│ │   │       • nx.shortest_path() 规划路径                  │
│ │   │       • 计算travel_time + clean_time                │
│ │   │       • U-turn判断 (lane_count%2==0)                │
│ │   │       • 更新truck_states与cleaning_records          │
│ │   │   └─> 返回策略结果字典                                │
│ │   └── save_result() - 保存JSON结果                       │
│ │                                                           │
│ strategies/random_strategy.py                               │
│ ├── RandomStrategy - 随机策略生成器                          │
│ │   ├── __init__() - 初始化配置与区域                       │
│ │   ├── load_network() - 加载路网 (同贪心)                  │
│ │   ├── assign_region_by_location() - 区域分配              │
│ │   ├── get_edge_center() - 计算边中心坐标                  │
│ │   ├── generate() - 随机策略生成流程 ⭐                    │
│ │   │   └─> 调用load_network() (无需流量统计)              │
│ │   │   └─> 随机打乱道路顺序 random.shuffle()               │
│ │   │   └─> 主循环: 按打乱顺序依次清扫                      │
│ │   └── save_result() - 保存JSON结果                       │
├─────────────────────────────────────────────────────────────┤
│ generate_strategies.py - 策略生成主程序                       │
│ ├── load_config() - 加载config.json配置                     │
│ ├── generate_strategies() - 批量生成策略 ⭐                  │
│ │   ├─> 创建输出目录 results/strategies_YYYYMMDD/          │
│ │   ├─> 调用 GreedyStrategy.generate()                     │
│ │   │   └─> 保存 greedy_strategy.json                     │
│ │   ├─> 调用 RandomStrategy.generate()                     │
│ │   │   └─> 保存 random_strategy.json                     │
│ │   └─> 返回生成结果汇总字典                                 │
│ └── main() - 命令行入口                                       │
│     └─> argparse处理参数 (-s 指定策略)                       │
├─────────────────────────────────────────────────────────────┤
│ evaluate_strategies.py - SUMO仿真评估器                      │
│ ├── load_config() - 加载配置                                 │
│ ├── load_strategy() - 读取策略JSON文件                       │
│ ├── evaluate_strategy() - 在SUMO中评估策略 ⭐                │
│ │   ├─> 调用modify_network_params()                        │
│ │   │   └─> 根据清扫记录修改路网参数                         │
│ │   │   └─> 更新道路速度/摩擦系数                            │
│ │   ├─> 调用run_sumo_simulation()                          │
│ │   │   └─> traci启动SUMO仿真                              │
│ │   │   └─> 逐步推进仿真记录数据                            │
│ │   └─> 统计评估指标并保存evaluation_*.json                 │
│ ├── modify_network_params() - 修改路网参数                   │
│ │   └─> 根据清扫状态动态更新边属性                           │
│ ├── run_sumo_simulation() - 运行SUMO仿真                    │
│ │   └─> traci.start() + 循环traci.simulationStep()        │
│ └── main() - 命令行入口                                       │
├─────────────────────────────────────────────────────────────┤
│ compare_results.py - 结果对比分析器                           │
│ ├── load_evaluation_result() - 加载评估结果JSON              │
│ ├── compare_results() - 多策略对比分析 ⭐                    │
│ │   ├─> 对比清扫覆盖率、响应时间等指标                        │
│ │   ├─> matplotlib生成对比图表                              │
│ │   └─> 保存comparison_report.json + .png                  │
│ └── main() - 命令行入口                                       │
├─────────────────────────────────────────────────────────────┤
│ main.py - 总入口                                             │
│ └── 串联调用: generate → evaluate → compare                 │
└─────────────────────────────────────────────────────────────┘

函数调用关系:
  主流程: main.py
    └─> generate_strategies.generate_strategies()
        ├─> GreedyStrategy.generate()
        │   ├─> load_network()
        │   ├─> load_traffic_flow()
        │   ├─> assign_region_by_location()
        │   └─> nx.shortest_path() [贪心主循环]
        └─> RandomStrategy.generate()
            ├─> load_network()
            ├─> random.shuffle()
            └─> nx.shortest_path() [随机主循环]
    └─> evaluate_strategy()
        ├─> modify_network_params()
        └─> run_sumo_simulation()
    └─> compare_results()

核心数据流:
  config.json → GreedyStrategy → greedy_strategy.json
                                      ↓
                              evaluate_strategy()
                                      ↓
                              evaluation_greedy.json
                                      ↓
                              compare_results()
                                      ↓
                            comparison_report.json + .png
```

## 使用说明

### 快速开始 (主入口)

```bash
python main.py
```

执行流程:
1. 从 `config.json` 加载配置
2. 从 `regions.json` 加载区域边界
3. 生成策略 (贪心 & 随机)
4. 保存结果到 `results/YYYYMMDD_HHMMSS/`

### 独立模块

1. **仅生成策略**:
```bash
python generate_strategies.py
python generate_strategies.py -s greedy  # 仅生成贪心策略
```

2. **SUMO评估** (独立运行):
```bash
python evaluate_strategies.py -s results/greedy_strategy.json
```

3. **对比分析** (独立运行):
```bash
python compare_results.py -e eval1.json eval2.json
```

## 输入参数

### 核心参数

- **num_trucks**: 扫雪车数量 (必须与num_regions相同)
- **num_regions**: 地理区域数量
- **speed_clean**: 清扫道路时的速度 (米/秒)
- **speed_pass**: 通行速度 (不清扫时) (米/秒)
- **max_time_minutes**: 最大清扫时间限制
- **unified_start_edge**: 所有扫雪车的统一起始边ID

### 文件路径

- **net_file**: SUMO路网文件路径
- **route_file**: SUMO路由文件路径 (交通流量数据)
- **regions_file**: 外部区域配置文件

## 输出格式

### 策略输出 (JSON)

```json
{
  "strategy_name": "greedy",
  "config": {
    "num_trucks": 5,
    "max_time_minutes": 300,
    "speed_clean": 3,
    "speed_pass": 10
  },
  "trucks": [
    {
      "truck_id": "region1",
      "cleaning_records": [
        {
          "edge_id": "123456",
          "start_time": 0.0,
          "end_time": 100.5
        }
      ]
    }
  ],
  "summary": {
    "total_roads_cleaned": 596,
    "total_time_minutes": 300.0
  }
}
```

## 配置提示

1. **调整扫雪车数量**: 修改 config.json 中的 `num_trucks`
2. **更改区域边界**: 直接编辑 regions.json
3. **调整时间限制**: 修改 `max_time_minutes`
4. **更改速度**: 调整 `speed_clean` 和 `speed_pass`

## 依赖安装

```bash
pip install networkx
```

无需可视化依赖 (核心代码已移除matplotlib).

