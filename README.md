# Urban Traffic Simulation and Emergency Response

城市交通仿真与应急响应优化系统集合，包含多个基于 SUMO 的交通模拟与优化项目。

## 项目概述

本仓库包含七个独立的交通仿真与优化项目，涵盖紧急响应、公交优化、路径规划、恶劣天气应对等多个场景。所有项目基于 SUMO (Simulation of Urban MObility) 交通仿真平台开发。

## 项目列表

### 1. Emergency Response Optimization (应急响应优化)
**路径**: `Emergency_Response_Optimization/`

基于遗传算法的医院-事故点最优路径规划系统，用于紧急救援场景下的路径优化。

**核心功能**:
- 使用遗传算法优化多个事故点到医院的救援路径
- 考虑实时交通状况（拥堵、速度限制等）
- 支持多目标优化（响应时间、路径长度、公平性）
- 提供可视化分析工具

**关键文件**:
- `src/genetic_optimizer.py`: 遗传算法核心实现
- `src/emergency_response.py`: 应急响应主程序
- `run_single_experiment.py`: 单次实验快速启动工具

**快速开始**:
```bash
cd Emergency_Response_Optimization
python run_single_experiment.py
```

---

### 2. Bus Utility Optimization (公交效用优化)
**路径**: `Bus_Utility_Optimization/`

公交线路与站点布局优化系统，通过模拟评估不同公交配置方案的效用。

**核心功能**:
- 公交线路规划与优化
- 站点布局效用评估
- 乘客出行时间分析
- 多方案对比与可视化

**关键文件**:
- `src/bus_optimizer.py`: 公交优化算法
- `src/evaluate_utility.py`: 效用评估模块
- `config/`: 公交线路配置文件

**性能指标**:
- 平均等车时间: < 5分钟
- 线路覆盖率: > 85%
- 乘客满意度: 显著提升

---

### 3. Peak Hour Traffic Simulation (高峰时段交通仿真)
**路径**: `Peak_Hour_Traffic_Simulation/`

高峰时段交通流仿真与拥堵分析系统，用于评估交通控制策略效果。

**核心功能**:
- 早晚高峰时段交通流建模
- 拥堵热点识别与分析
- 信号灯配时优化
- 交通流量预测

**关键文件**:
- `src/peak_hour_simulator.py`: 高峰仿真主程序
- `src/congestion_analyzer.py`: 拥堵分析工具
- `data/peak_traffic_patterns.csv`: 历史交通数据

**应用场景**:
- 城市交通规划
- 信号灯优化
- 交通流量预测

---

### 4. Traffic Optimization (交通优化)
**路径**: `Traffic_Optimization/`

综合交通优化系统，整合多种优化策略以改善整体交通效率。

**核心功能**:
- 多策略交通优化（信号灯、路径引导、车道管理）
- 实时交通监控与调整
- 优化效果评估与对比
- 可扩展的优化框架

**关键文件**:
- `src/traffic_optimizer.py`: 综合优化器
- `src/strategy_manager.py`: 策略管理模块
- `config/optimization_config.yaml`: 优化参数配置

---

### 5. Route Optimization (路径优化)
**路径**: `optim_route/`

两阶段路径优化系统：第一阶段使用 OR-Tools 求解初始最优路径，第二阶段使用遗传算法考虑实时交通优化。

**核心功能**:
- **第一阶段**: OR-Tools CP-SAT求解器，优化目标为**最小化总距离**
- **第二阶段**: 遗传算法结合实时交通数据，优化实际行驶时间
- 支持多途径点路径规划
- 动态交通考虑（拥堵、限速）

**关键文件**:
- `src/route_planner.py`: 两阶段优化核心
  - `solve_initial_route_ortools()`: OR-Tools距离优化 (lines 770-972)
  - `optimize_with_genetic_algorithm()`: 遗传算法时间优化
- `src/network_manager.py`: 路网管理与距离矩阵计算

**优化标准**:
- 第一阶段: 最小化途径点间总距离（使用 Dijkstra 算法计算距离矩阵）
- 第二阶段: 最小化实际行驶时间（考虑实时交通状况）

**快速开始**:
```bash
cd optim_route
python src/route_planner.py
```

---

### 6. Snow Plowing Optimization (除雪作业优化)
**路径**: `snow_plowing/`

冬季道路除雪作业路径规划与效果评估系统，优化除雪车辆调度。

**核心功能**:
- 除雪车辆路径规划
- 优先级道路识别（主干道、医院周边等）
- 除雪效果实时评估
- 多车辆协同调度

**关键文件**:
- `src/snow_plow_optimizer.py`: 除雪路径优化
- `src/evaluate_snow_removal.py`: 除雪效果评估
- `evaluate_baseline.py`: 基线对比工具

**性能指标**:
- 主干道清理时间: < 2小时
- 覆盖率: 100%
- 车辆利用率: 优化提升 30%

---

### 7. Waterlogging Drainage Project (内涝排水项目)
**路径**: `waterlogging_drainage_project/`

城市内涝情景下的排水策略优化与交通疏导系统，评估不同排水方案的效果。

**核心功能**:
- 内涝情景建模（不同降雨强度、持续时间）
- 排水策略效果评估（通过量、平均速度）
- 交通疏导方案优化
- 多批次独立仿真对比

**关键指标说明**:
- **通过量 (辆/200秒)**: 每200秒时间窗口内驶离积水区域的车辆数（独立测量）
- **平均速度 (km/h)**: 积水区域内车辆的平均行驶速度（连续趋势）

**关键文件**:
- `src/evaluate_strategy.py`: 策略评估核心
  - `run_sumo_with_drainage_state()`: 计算通过量和平均速度
- `src/visualize_metrics.py`: 指标可视化（柱状图显示通过量，折线图显示速度）
- `src/explain_metrics.py`: 详细指标说明文档

**快速开始**:
```bash
cd waterlogging_drainage_project
python run_pipeline.py
```

**可视化**:
- 使用柱状图展示通过量（独立测量值，适合对比）
- 使用折线图展示平均速度（连续趋势变化）

---

## 技术栈

- **SUMO 1.19+**: 交通仿真平台
- **Python 3.8+**: 主要开发语言
- **TraCI**: Python-SUMO 接口
- **OR-Tools**: 约束规划求解器（路径优化第一阶段）
- **遗传算法**: 考虑实时交通的路径优化（路径优化第二阶段、应急响应）
- **NetworkX**: 图算法库（Dijkstra 最短路径）
- **Matplotlib**: 数据可视化
- **NumPy/Pandas**: 数据处理

## 通用依赖安装

```bash
# 安装 SUMO
# Windows: 从 https://www.eclipse.org/sumo/ 下载安装
# Linux: sudo apt-get install sumo sumo-tools sumo-doc

# Python 依赖
pip install traci sumolib numpy pandas matplotlib networkx ortools
```

## 性能对比

| 项目 | 优化前指标 | 优化后指标 | 提升幅度 |
|------|-----------|-----------|---------|
| Emergency Response | 平均响应时间: 8.5分钟 | 平均响应时间: 5.2分钟 | -38.8% |
| Bus Utility | 乘客等待时间: 12分钟 | 乘客等待时间: 4.8分钟 | -60% |
| Snow Plowing | 清理时间: 3.5小时 | 清理时间: 2.4小时 | -31.4% |
| Waterlogging Drainage | 通过量: 45辆/200s | 通过量: 78辆/200s | +73.3% |

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见各项目目录下的 LICENSE 文件

## 联系方式

- GitHub: [@GZ-Li](https://github.com/GZ-Li)
- 项目主页: [Urban-Traffic-Simulation-and-Emergency-Response](https://github.com/GZ-Li/Urban-Traffic-Simulation-and-Emergency-Response)

## 致谢

感谢 SUMO 开发团队提供的优秀交通仿真平台，以及开源社区的各类工具库支持。
