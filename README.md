# 城市交通仿真与应急响应

基于 SUMO 的城市交通模拟与优化项目集合

## 项目列表

### 1. 城市交通高峰模拟
**路径**: `Peak_Hour_Traffic_Simulation/`

（项目开发中）

---

### 2. 高峰期道路资源优化
**路径**: `Traffic_Optimization/`

（项目开发中）

---

### 3. 公交车利用率提升
**路径**: `Bus_Utility_Optimization/`

（项目开发中）

---

### 4. 内涝排水策略评估
**路径**: `waterlogging_drainage_project/`

城市内涝情景下的排水策略优化与交通疏导系统，评估不同排水方案对交通的影响。

#### 核心功能
- 内涝情景建模：模拟不同降雨强度下的道路积水
- 排水策略生成：生成最优和最差排水顺序
- 交通仿真评估：使用 SUMO 模拟不同排水策略下的交通状况
- 策略对比分析：在多个时间延迟点（30s, 60s, 120s）评估策略效果

#### 评估指标
- **通过量 (Cumulative Throughput)**: 驶离积水区域的累计车辆数
- **队列长度 (Queue Length)**: 积水区域内滞留的平均车辆数
- **平均速度 (Average Speed)**: 积水区域内车辆的平均行驶速度

#### 项目结构
```
waterlogging_drainage_project/
├── config.json                          # 配置文件
├── data/                                # SUMO 路网与路由文件
├── src/                                 
│   ├── generate_strategy.py            # 策略生成
│   ├── evaluate_strategy.py            # SUMO 仿真评估
│   ├── compare_strategies.py           # 策略对比
│   └── visualize_waterlogging.py       # 可视化
├── waterlogging_point_identification/  # 内涝点数据
└── results/                             # 输出目录
```

#### 快速开始
```bash
cd waterlogging_drainage_project
python src/main.py
```

#### 依赖
- Python 3.8+
- SUMO 1.15+
- pandas, numpy, matplotlib

---

### 5. 除雪作业优化
**路径**: `snow_plowing/`

冬季道路除雪作业路径规划与效果评估系统，优化除雪车辆调度。

#### 核心功能
- **策略生成**: 贪心策略（优先清扫高流量道路）vs 随机策略
- **路径规划**: 使用 NetworkX 和 Dijkstra 算法计算最短路径
- **区域分配**: 将道路按坐标分配到不同区域，每个扫雪车负责一个区域
- **仿真评估**: 基于 SUMO 路网进行除雪效果评估

#### 策略对比
| 策略 | 描述 |
|------|------|
| 贪心策略 | 按交通流量降序排序，优先清扫高流量道路 |
| 随机策略 | 随机打乱道路顺序进行清扫 |

#### 配置参数
- `num_trucks`: 扫雪车数量（必须与 `num_regions` 相同）
- `speed_clean`: 清扫速度（米/秒）
- `speed_pass`: 通行速度（米/秒）
- `max_time_minutes`: 最大清扫时间（分钟）

#### 项目结构
```
snow_plowing/
├── config.json                 # 主配置文件
├── regions.json                # 区域边界配置
├── generate_strategies.py      # 策略生成器
├── evaluate_strategies.py      # SUMO 评估器
├── strategies/                 # 策略算法模块
│   ├── greedy_strategy.py     # 贪心策略
│   └── random_strategy.py     # 随机策略
└── results/                    # 输出目录
```

#### 快速开始
```bash
cd snow_plowing
python generate_strategies.py
python evaluate_strategies.py
```

---

### 6. 单点事故应急响应
**路径**: `Emergency_Response_Optimization/`

基于匈牙利算法的交通事故应急响应优化系统，为多个医院和事故点分配最优救护车路径。

#### 核心功能
- **路径规划**: 使用 Dijkstra 算法计算救护车从医院到事故点的最优路径
- **优化分配**: 将问题建模为任务分配问题 (Min-Max Assignment)，最小化最大响应时间
- **算法对比**: 对比最优算法与贪心算法的性能差异
- **可视化**: 生成分配方案对比图和路网地图
- **SUMO 仿真**: 基于 SUMO 平台进行实际验证

#### 算法优势
相比贪心算法，最优算法可以：
- 减少最大响应时间
- 实现更均衡的医院资源利用
- 保证全局最优解

#### 项目结构
```
Emergency_Response_Optimization/
├── src/
│   ├── path_planning.py            # 路径规划（Dijkstra）
│   ├── optimization.py             # 优化算法（匈牙利算法）
│   ├── visualization.py            # 可视化
│   └── sumo_simulation.py          # SUMO 仿真接口
├── data/
│   ├── Hospital_Location.csv       # 医院位置
│   ├── cases.txt                   # 测试案例
│   └── new_add_light.net.xml       # 路网文件
├── run_single_experiment.py        # 单次实验工具
└── results/                        # 实验结果
```

#### 快速开始
```bash
cd Emergency_Response_Optimization
python run_single_experiment.py
```

#### 依赖
- Python 3.8+
- numpy, pandas, scipy
- networkx, matplotlib
- sumolib, traci

---

### 7. 多点事故应急响应
**路径**: （项目开发中）

---

### 8. 马拉松路线规划
**路径**: `optim_route/`

基于 OR-Tools 和遗传算法的多约束路线规划系统，支持 OSM 和 SUMO Net 两种路网格式。

#### 核心特性
- **双算法优化**: OR-Tools 求解最优途经点顺序 + 遗传算法局部优化
- **多路网格式支持**: OSM XML 和 SUMO .net.xml
- **多约束优化**: 途经点约束、距离约束、拥堵系数约束
- **评估指标**: 距离满足度、途经点满足度

#### 优化流程
1. **第一阶段 (OR-Tools)**: 
   - 使用 CP-SAT 求解器
   - 计算最优途经点访问顺序
   - 优化目标：最小化总距离
   
2. **第二阶段 (遗传算法)**:
   - 在 OR-Tools 解的基础上进行局部优化
   - 考虑道路拥堵系数
   - 优化目标：最小化实际行驶时间

#### 支持的路网格式
| 格式 | 说明 | 处理器 |
|------|------|--------|
| OSM XML | OpenStreetMap XML 格式 | OSMDataProcessor |
| Net .net.xml | SUMO 路网格式 | NetDataProcessor |

#### 项目结构
```
optim_route/
├── route_planner.py            # 主入口，路线规划核心
├── run_wuhan_net.py            # 测试脚本
├── utils.py                    # 数据处理与评估
├── data/
│   ├── wuhan.net.xml           # 大范围路网
│   └── wuhan_core.net.xml      # 核心区域路网
└── results/                    # 输出目录
```

#### 快速开始
```bash
cd optim_route

# 使用 uv 安装依赖
uv sync

# 运行测试
uv run python run_wuhan_net.py \
    --net-file data/wuhan_core.net.xml \
    --output-dir results \
    --cases case3 \
    --generations 200
```

#### 依赖
- Python 3.8+
- ortools
- networkx
- numpy, pandas

---

### 9. 定点赛事人流疏散
**路径**: `concert_evacuation/`

（项目开发中）

---

## 技术栈

- **SUMO 1.15+**: 交通仿真平台
- **Python 3.8+**: 主要开发语言
- **TraCI**: Python-SUMO 接口
- **OR-Tools**: 约束规划求解器
- **NetworkX**: 图算法库（Dijkstra 最短路径）
- **Matplotlib**: 数据可视化
- **NumPy/Pandas**: 数据处理
- **Scipy**: 科学计算（匈牙利算法）

## 通用依赖安装

```bash
# 安装 SUMO
# Windows: 从 https://www.eclipse.org/sumo/ 下载安装
# Linux: sudo apt-get install sumo sumo-tools sumo-doc

# Python 依赖
pip install traci sumolib numpy pandas matplotlib networkx ortools scipy
```
