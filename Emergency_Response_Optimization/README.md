# Emergency Response Optimization System

基于匈牙利算法的交通事故应急响应优化系统

## 项目简介

本项目实现了一个交通事故应急响应系统，通过优化算法为多个医院和事故点之间分配救护车路径，目标是最小化最大响应时间（Min-Max Assignment Problem）。

### 核心功能

- **路径规划**: 使用A*算法和K短路算法计算救护车从医院到事故点的多条最优路径
- **优化分配**: 使用匈牙利算法（Hungarian Algorithm）+ 二分搜索求解最优分配方案
- **事故点生成**: 在指定事故点周围随机生成测试案例
- **可视化**: 对比贪心算法和最优算法的分配效果
- **SUMO仿真**: 基于SUMO交通仿真平台进行实际验证

### 算法优势

相比贪心算法，本项目的最优算法可以：
- 减少30-40%的最大响应时间
- 实现更均衡的医院资源利用
- 保证全局最优解

## 项目结构

```
Emergency_Response_Optimization/
├── src/                                    # 源代码
│   ├── config.py                           # 配置文件
│   ├── path_planning.py                    # 路径规划模块（A*、K短路）
│   ├── optimization.py                     # 优化算法模块（匈牙利算法）
│   ├── accident_generator.py               # 事故点生成器
│   ├── visualization.py                    # 可视化模块
│   └── sumo_simulation.py                  # SUMO仿真接口
├── data/                                   # 数据文件
│   ├── Hospital_Location.csv               # 医院位置数据（6个医院）
│   ├── cases.txt                           # 测试案例
│   ├── new_add_light.net.xml               # SUMO路网文件（10342节点，16383边）
│   ├── mapall_addline_response.rou.xml     # 预生成救护车路由（150辆）
│   └── response.sumocfg                    # SUMO仿真配置文件
├── test_case.py                            # 测试脚本（复现test3场景）
├── main.py                                 # 主程序入口
├── run_complete_pipeline.py                # 完整流程运行
├── run_single_experiment.py                # 单次实验工具
├── visualize_map_enhanced.py               # 地图可视化工具
├── generate_multi_accident_summary.py      # Multi_Accident报告生成
├── Multi_Accident/                         # 多事故点数据
│   ├── optimization_vs_greedy.json         # 优化结果对比
│   ├── shortest_paths.json                 # 最短路径数据
│   ├── path_time_length.json               # 路径时间长度
│   └── summary.txt                         # 结果总结报告
├── results/                                # 实验结果
│   └── test_run_YYYYMMDD_HHMMSS/           # 按时间戳保存的测试结果
│       ├── arrival_times.json              # 救护车到达时间
│       ├── optimal_paths.json              # 最优分配方案
│       ├── greedy_paths.json               # 贪心分配方案
│       ├── time_matrix.csv                 # 时间矩阵
│       ├── summary.txt                     # 详细报告
│       ├── comparison.png                  # 算法对比图
│       ├── assignment_map_optimal.png      # 最优解地图
│       └── assignment_map_greedy.png       # 贪心解地图
├── docs/                                   # 文档
│   └── ALGORITHM.md                        # 算法说明
└── README.md                               # 本文件
```

## 安装依赖

```bash
pip install -r requirements.txt
```

### 主要依赖

- Python >= 3.8
- numpy
- pandas
- scipy
- networkx
- matplotlib
- sumolib (SUMO工具包)
- traci (SUMO Python接口)

## 配置说明

在运行前，需要修改 `src/config.py` 中的配置：

```python
# 配置SUMO路网文件路径
SUMO_NET_FILE = "data/your_network.net.xml"
INPUT_ROUTE_FILE = "data/your_routes.rou.xml"

# 配置事故点ID
SIMULATION_CONFIG["accident_spots"] = ["edge_id_1", "edge_id_2", ...]
```

## 使用方法

### 1. 快速开始

运行完整的测试案例（复现test3场景）：

```bash
python test_case.py
```

### 2. 单次实验

使用单次实验工具：

```bash
python run_single_experiment.py
```

### 3. 完整流程

运行完整的实验流程：

```bash
python run_complete_pipeline.py
```

### 4. 地图可视化

生成最优/贪心策略的地图可视化：

```bash
# 可视化最优策略
python visualize_map_enhanced.py -s optimal

# 可视化贪心策略
python visualize_map_enhanced.py -s greedy

# 同时生成两种策略的地图
python visualize_map_enhanced.py -s both

# 可视化Multi_Accident数据
python visualize_map_enhanced.py -m
```

## 关键代码实现

### 核心模块架构

```
┌─────────────────────────────────────────────────────────────┐
│ 应急响应优化系统 - 核心模块                                    │
├─────────────────────────────────────────────────────────────┤
│ src/path_planning.py                                         │
│ ├── sumo_net_to_networkx() - SUMO路网转NetworkX图           │
│ │   ├── 解析junction节点坐标                                │
│ │   ├── 解析edge生成{edge_id}_out, {edge_id}_in节点        │
│ │   └── 解析connection建立边连接关系                        │
│ ├── find_k_shortest_paths() - K条最短路径计算               │
│ │   ├── 使用NetworkX shortest_simple_paths                 │
│ │   ├── Yen's K-Shortest Path算法实现                       │
│ │   └── 返回: [{path, time, length}, ...] (k条路径)         │
│ ├── heuristic() - A*算法启发函数                            │
│ │   └── 基于NetworkX节点位置计算欧氏距离                    │
│ └── filter_internal_edges() - 过滤内部边                    │
│     └── 移除:前缀的内部连接边                               │
├─────────────────────────────────────────────────────────────┤
│ src/optimization.py                                          │
│ ├── solve_optimal_assignment() - 最优分配求解               │
│ │   ├── 输入: time_matrix (num_hospitals × num_accidents)  │
│ │   ├── 二分搜索最优makespan                                │
│ │   │   ├── low = min(time_matrix)                         │
│ │   │   └── high = max(time_matrix)                        │
│ │   ├── 构建cost_matrix: 时间<=mid置0, 否则1e6             │
│ │   ├── scipy.optimize.linear_sum_assignment() 匈牙利算法   │
│ │   └── 返回: (best_total_time, best_assignment)           │
│ ├── solve_greedy_assignment() - 贪心分配求解                │
│ │   ├── 每次选择当前最小时间的医院-事故对                    │
│ │   ├── 标记已分配的事故点和医院                             │
│ │   └── 返回: (max_time, assignment_list)                  │
│ ├── compare_algorithms() - 算法对比                         │
│ │   ├── 遍历实验结果目录                                    │
│ │   ├── 加载各实验的time_matrix.csv                        │
│ │   └── 统计最优算法vs贪心算法性能                          │
│ └── print_comparison_statistics() - 打印统计结果             │
│     └── 计算平均改进幅度和成功率                             │
├─────────────────────────────────────────────────────────────┤
│ src/sumo_simulation.py                                       │
│ ├── setup_sumo_simulation() - 启动SUMO仿真                  │
│ │   ├── sumo_binary选择: sumo-gui或sumo                    │
│ │   ├── 配置参数: --no-warnings, --time-to-teleport -1    │
│ │   └── traci.start()启动仿真                              │
│ ├── measure_route_time() - 测量单条路径时间                 │
│ │   ├── 创建救护车vehicle: traci.vehicle.add()            │
│ │   ├── 设置路由: traci.vehicle.setRoute()                │
│ │   ├── 实时步进仿真直到到达终点                            │
│ │   └── 返回: 实际行驶时间                                  │
│ ├── batch_measure_routes() - 批量测量路径                   │
│ │   ├── 对每条路径调用measure_route_time()                │
│ │   └── 返回: {route_id: travel_time}字典                 │
│ └── measure_hospital_accident_pairs() - 测量医院-事故对时间  │
│     ├── 使用find_k_shortest_paths()计算k条路径             │
│     ├── batch_measure_routes()测量实际时间                 │
│     └── 构建time_matrix返回                                │
├─────────────────────────────────────────────────────────────┤
│ src/visualization.py                                         │
│ ├── setup_chinese_font() - 设置中文字体                     │
│ │   └── SimHei, DejaVu Sans字体配置                        │
│ ├── visualize_comparison() - 算法对比可视化                 │
│ │   ├── 创建2×1子图布局                                    │
│ │   ├── 上图: 贪心算法甘特图                                │
│ │   └── 下图: 最优算法甘特图                                │
│ ├── plot_assignment() - 绘制单个分配方案                    │
│ │   ├── 使用matplotlib barh绘制水平条形图                  │
│ │   ├── y轴: 医院编号 (0-5)                                │
│ │   ├── x轴: 时间 (0-max_time)                             │
│ │   └── 颜色: 区分不同事故点                                │
│ └── print_performance_comparison() - 打印性能对比            │
│     └── 输出改进幅度和时间差异                               │
├─────────────────────────────────────────────────────────────┤
│ test_case.py - 主测试脚本                                    │
│ ├── is_vehicle_finished() - 判断车辆到达                    │
│ │   ├── traci.vehicle.getRoadID()获取当前edge             │
│ │   ├── 比较路径终点: path.split()[-1]                     │
│ │   └── 返回: True/False                                    │
│ └── 主流程 (main)                                            │
│     ├── 1. 配置参数                                         │
│     │   ├── accident_spots: 4个事故点ID                    │
│     │   ├── hospital_num: 6, acc_num: 4, path_num: 5      │
│     │   └── MAX_SIMULATION_TIME: 1200秒                    │
│     ├── 2. 加载路网和医院数据                               │
│     │   ├── sumo_net_to_networkx()构建图                   │
│     │   └── pd.read_csv()加载医院位置                      │
│     ├── 3. 计算时间矩阵                                     │
│     │   ├── find_k_shortest_paths()计算k=5条路径           │
│     │   └── 生成6×4 time_matrix                            │
│     ├── 4. 求解最优分配和贪心分配                           │
│     │   ├── solve_optimal_assignment()                     │
│     │   └── solve_greedy_assignment()                      │
│     ├── 5. SUMO仿真验证                                     │
│     │   ├── traci.start()启动仿真                          │
│     │   ├── 每个事故点30辆救护车 (120辆总计)               │
│     │   ├── 每10步检查车辆位置                              │
│     │   └── 记录到达时间到DataFrame                         │
│     └── 6. 生成结果输出                                     │
│         ├── results/test_run_YYYYMMDD_HHMMSS/              │
│         ├── arrival_times.json - 120辆到达时间             │
│         ├── optimal_paths.json - 最优分配方案               │
│         ├── time_matrix.csv - 6×4时间矩阵                  │
│         ├── summary.txt - 详细报告                          │
│         └── comparison.png - 算法对比图                     │
├─────────────────────────────────────────────────────────────┤
│ main.py - 主程序入口                                         │
│ ├── run_single_experiment() - 单次实验运行                  │
│ │   ├── 输入: time_matrix                                  │
│ │   ├── 调用solve_optimal/greedy_assignment()             │
│ │   └── 返回: 分配方案和最大时间                            │
│ ├── load_experiment_data() - 加载实验数据                   │
│ │   └── 从exp_res目录加载历史实验结果                       │
│ ├── demo_visualization() - 演示可视化                       │
│ │   └── 使用示例数据展示visualize_comparison()            │
│ └── main() - 主函数                                          │
│     └── 调用demo_visualization()                           │
├─────────────────────────────────────────────────────────────┤
│ run_complete_pipeline.py - 完整流程运行                      │
│ └── run_complete_pipeline() - 完整流程主函数                │
│     ├── 参数: SUMO文件路径, 医院文件, 事故点列表            │
│     ├── 1. 加载路网构建图结构                               │
│     ├── 2. 计算k条最短路径                                  │
│     ├── 3. SUMO仿真测量实际时间                             │
│     ├── 4. 构建时间矩阵                                     │
│     ├── 5. 优化求解                                         │
│     └── 6. 结果保存和可视化                                 │
├─────────────────────────────────────────────────────────────┤
│ run_single_experiment.py - 单次实验工具                      │
│ ├── run_single_experiment() - 单次实验执行                  │
│ │   ├── 输入: time_matrix                                  │
│ │   ├── 求解最优和贪心分配                                  │
│ │   └── 可视化对比结果                                      │
│ ├── prepare_visualization_data() - 准备可视化数据           │
│ │   └── 转换assignment为甘特图数据格式                      │
│ ├── load_from_csv() - 从CSV加载时间矩阵                     │
│ │   └── 读取用户提供的time_matrix.csv                      │
│ ├── interactive_input() - 交互式输入                        │
│ │   └── 引导用户逐行输入时间矩阵                            │
│ ├── example_with_sample_data() - 示例数据演示               │
│ │   └── 使用预设time_matrix运行演示                        │
│ └── main() - 主函数                                          │
│     └── 提供三种输入方式: CSV/交互/示例                      │
├─────────────────────────────────────────────────────────────┤
│ visualize_map_enhanced.py - 地图可视化工具                  │
│ ├── load_edge_coordinates() - 加载边坐标                    │
│ │   ├── 解析.net.xml的edge shape属性                       │
│ │   ├── 提取坐标字符串转换为(x,y)元组                       │
│ │   └── 返回: {edge_id: (x, y)}字典                        │
│ ├── visualize_test_results() - 可视化测试结果               │
│ │   ├── 加载optimal_paths.json/greedy_paths.json          │
│ │   ├── 加载Hospital_Location.csv                         │
│ │   ├── matplotlib绘图                                     │
│ │   │   ├── 路网背景 (灰色, linewidth=0.5, alpha=0.3)     │
│ │   │   ├── 医院位置 (彩色方块 marker='s', s=100)          │
│ │   │   ├── 事故位置 (红色三角 marker='^', s=120)          │
│ │   │   └── 分配箭头 (颜色对应医院, 时间标注)              │
│ │   └── 保存: assignment_map_{strategy}.png               │
│ ├── visualize_multi_accident() - Multi_Accident可视化       │
│ │   ├── 加载optimization_vs_greedy.json                   │
│ │   ├── 加载shortest_paths.json                           │
│ │   └── 相同绘图逻辑,输出到visualization/目录              │
│ └── main() - 主函数                                          │
│     ├── argparse解析命令行参数                              │
│     ├── -s: optimal/greedy/both 策略选择                   │
│     └── -m: Multi_Accident数据源标志                       │
├─────────────────────────────────────────────────────────────┤
│ generate_multi_accident_summary.py - 报告生成工具            │
│ ├── load_json() - JSON文件加载                              │
│ │   └── with open() + json.load()                         │
│ └── generate_summary() - 生成summary.txt                    │
│     ├── 加载三个JSON文件                                    │
│     │   ├── optimization_vs_greedy.json - 分配结果         │
│     │   ├── shortest_paths.json - 路径edge序列 (2811行)   │
│     │   └── path_time_length.json - 时间长度               │
│     ├── 构建时间矩阵 (6×5)                                  │
│     ├── 检测异常                                            │
│     │   ├── 重复分配: 同一事故分配给多个医院                │
│     │   └── 串行累加: 同一医院处理多个事故                  │
│     ├── 计算性能指标                                        │
│     │   ├── 最优算法: 2014秒 (并行执行)                    │
│     │   ├── 贪心算法: 4532秒 (串行累加)                    │
│     │   └── 性能提升: 55.5%                                │
│     └── 输出summary.txt (173行)                             │
│         ├── 配置信息                                        │
│         ├── 时间矩阵                                        │
│         ├── 最优分配方案 (含完整37-60条edge路径)           │
│         ├── 贪心分配方案                                    │
│         └── 异常标记: ⚠️重复, ⚠️串行累加                    │
└─────────────────────────────────────────────────────────────┘
```

### 数据流程图

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│ 输入数据    │      │ 路径规划     │      │ 优化分配     │
├─────────────┤      ├──────────────┤      ├──────────────┤
│ 路网文件    │─────>│ 构建图结构   │─────>│ 时间矩阵     │
│ 医院位置    │      │ K短路径计算  │      │ 6x4矩阵      │
│ 事故点列表  │      └──────────────┘      └──────┬───────┘
└─────────────┘                                    │
                                                   v
      ┌────────────────────────────────────────────────────┐
      │               优化算法求解                          │
      ├────────────────────────────────────────────────────┤
      │  最优算法                    贪心算法               │
      │  ├─ 二分搜索makespan        ├─ 选最小时间对        │
      │  ├─ 构建二分图              ├─ 标记已分配          │
      │  └─ 匈牙利算法匹配          └─ 迭代至完成          │
      └────────────────┬───────────────────┬───────────────┘
                       │                   │
                       v                   v
            ┌──────────────────┐ ┌──────────────────┐
            │ optimal_paths    │ │ greedy_paths     │
            │ makespan: 1863s  │ │ makespan: 2698s  │
            └────────┬─────────┘ └────────┬─────────┘
                     │                    │
                     └──────────┬─────────┘
                                v
                    ┌───────────────────────┐
                    │   SUMO实时仿真验证    │
                    ├───────────────────────┤
                    │ 120辆救护车测试       │
                    │ 实际到达率: 65.8%     │
                    │ 实际响应时间统计      │
                    └───────────┬───────────┘
                                v
                    ┌───────────────────────┐
                    │   结果输出与可视化    │
                    ├───────────────────────┤
                    │ summary.txt           │
                    │ comparison.png        │
                    │ assignment_map_*.png  │
                    └───────────────────────┘
```

## 算法原理

### 问题描述

给定：
- N个医院，每个医院有救护车
- M个事故点需要救援
- 时间矩阵 T[i][j] 表示医院i到事故点j的响应时间

目标：最小化最大响应时间（Makespan）

### 解决方案

1. **二分搜索**: 搜索最优的最大完成时间
2. **匈牙利算法**: 在给定时间约束下，求解最优分配
3. **可行性检查**: 验证是否所有事故点都能在限定时间内得到救援

### 时间复杂度

- 二分搜索: O(log(T_max))
- 匈牙利算法: O(N³)
- 总体: O(N³ log(T_max))

## 实验结果

基于20组实验的统计结果：

| 算法 | 平均最大响应时间 | 改进幅度 |
|------|-----------------|---------|
| 贪心算法 | 740秒 | - |
| 最优算法 | 500秒 | **32.4%** |

## 引用与参考

本项目基于以下理论基础：
- 匈牙利算法（Kuhn-Munkres Algorithm）
- K短路算法（Yen's Algorithm）
- 最小最大化问题（Min-Max Optimization）

## 开发者

开发于交通仿真与优化研究项目

## 许可证

MIT License

## 注意事项

1. 需要安装SUMO仿真平台
2. 需要准备相应的路网文件（.net.xml）
3. 医院位置和事故点需要在路网中存在

## 后续改进方向

- [ ] 支持动态事故点
- [ ] 多目标优化（时间 + 成本）
- [ ] 实时路况考虑
- [ ] 救护车数量约束
- [ ] Web可视化界面
