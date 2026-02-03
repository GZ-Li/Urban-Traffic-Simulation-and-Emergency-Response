# 城市内涝排水策略评估系统

基于交通仿真的内涝积水点排水策略评估与优化系统。

## 项目简介

本项目针对城市内涝积水点的排水优先级问题，通过交通仿真技术评估不同排水策略的效果。系统能够：
- **策略生成**：根据交通流量自动生成最优/最差排水顺序
- **仿真评估**：模拟积水对交通的影响，量化排水策略效果
- **对比分析**：多策略对比，生成详细报告和可视化图表

## 核心功能

### 1. 排水策略生成
- 分析路网车流量，识别高流量积水点
- 生成基于流量优先级的排水批次
- 支持最优策略（优先排高流量区域）和最差策略（优先排低流量区域）

### 2. 交通仿真评估
- 模拟积水区域车速下降效果（积水区1.5 m/s vs 正常区15 m/s）
- 在不同排水进度下独立运行仿真
- 支持多时间延迟点评估（30秒、60秒、120秒）

### 3. 性能指标
- **累计通过量**：驶离积水区域的车辆总数（越高越好）
- **排队长度**：积水区域滞留车辆数（越低越好）
- **平均速度**：积水区域平均行驶速度（越高越好）

## 项目结构

```
waterlogging_drainage_project/
├── config.json                          # 主配置文件
├── README_CN.md                         # 中文说明文档（本文件）
├── README.md                            # 英文说明文档
├── QUICKSTART.md                        # 快速上手指南
├── SIMULATOR_INTEGRATION.md             # 模拟器对接文档
├── requirements.txt                     # Python依赖包
├── run_pipeline.py                      # 完整流程脚本
├── data/                                # 仿真数据
│   ├── network/
│   │   └── new_add_light.net.xml       # 路网文件（27MB）
│   ├── routes/
│   │   └── mapall_addline_expand.rou.xml  # 车辆路由文件
│   └── Core_500m_test.sumocfg          # SUMO配置文件
├── src/                                 # 源代码
│   ├── main.py                         # 主流程脚本
│   ├── generate_strategy.py           # 策略生成模块
│   ├── evaluate_strategy.py           # 仿真评估模块
│   ├── compare_strategies.py          # 策略对比模块
│   ├── visualize_waterlogging.py      # 可视化工具
│   └── simulator_adapter.py           # 自定义模拟器适配器模板
├── results/                            # 输出目录（自动生成）
│   ├── strategies_*/                   # 策略文件与评估结果
│   └── comparison_*/                   # 对比报告与图表
└── waterlogging_point_identification/  # 积水点数据
    ├── waterlogging.py                # 积水点识别脚本
    ├── raw_data_V2.xlsx               # 原始数据
    ├── 武汉内涝点V1.0_四位小数.xlsx   # 武汉积水点数据
    └── 内涝点.png                      # 积水点分布图
```

## 环境要求

- **Python**：3.8+
- **交通仿真器**：SUMO 1.15+（或兼容的自研仿真器）
- **Python依赖包**：见 `requirements.txt`

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

主要依赖包：
- `sumolib`：SUMO路网解析
- `traci`：SUMO仿真控制（如使用自研仿真器，需替换为适配器）
- `matplotlib`：图表生成
- `numpy`：数值计算

### 2. 安装SUMO（或配置自研仿真器）

**方案A：使用SUMO**
- 下载地址：https://sumo.dlr.de/docs/Downloads.php
- 设置环境变量 `SUMO_HOME`
- 确保 `sumo` 命令在PATH中

**方案B：使用自研仿真器**
- 参考 `SIMULATOR_INTEGRATION.md` 实现适配器接口
- 修改 `src/simulator_adapter.py` 连接您的仿真器

## 配置说明

编辑 `config.json` 进行自定义配置：

### 路网文件配置
```json
"network": {
  "net_file": "data/network/new_add_light.net.xml",      # 路网文件
  "route_file": "data/routes/mapall_addline_expand.rou.xml"  # 路由文件
}
```

### 仿真参数配置
```json
"sumo_config": {
  "config_file": "data/Core_500m_test.sumocfg",  # SUMO配置文件
  "simulation_steps": 200,                        # 仿真时长（秒）
  "evaluation_delays": [30, 60, 120],            # 评估延迟点（秒）
  "measurement_window": 200                       # 测量时间窗口（秒）
}
```

### 积水点分组配置
```json
"waterlogging_points": {
  "g1": ["200040454", "200041869", ...],  # 积水点组1（edge ID列表）
  "g2": ["200041609", "200041610", ...],  # 积水点组2
  ...
  "g9": ["200001259", "200001286", ...]   # 积水点组9
}
```

### 排水参数配置
```json
"drainage_parameters": {
  "max_clean_at_once": 3,      # 每批次最多排水点数
  "steps_to_clean_one": 600,   # 单个点排水耗时（秒）
  "flooded_speed": 1.5,        # 积水区域车速（m/s）
  "normal_speed": 15,          # 正常区域车速（m/s）
  "start_step": 10             # 开始评估的时间步
}
```

## 使用方法

### 快速运行完整流程

```bash
python run_pipeline.py
```

这将自动执行：
1. 生成最优和最差策略
2. 运行仿真评估
3. 对比分析生成报告

### 分步运行

#### 步骤1：生成排水策略
```bash
cd src
python generate_strategy.py
```

输出：`results/strategies_YYYYMMDD_HHMMSS/`
- `best_strategy.json`：最优策略（高流量优先）
- `worst_strategy.json`：最差策略（低流量优先）

#### 步骤2：评估单个策略
```bash
python evaluate_strategy.py -s results/strategies_*/best_strategy.json
```

输出：`results/strategies_*/evaluation_best.json`
- 包含每个批次完成后的性能指标

#### 步骤3：对比多个策略
```bash
python compare_strategies.py -e results/strategies_*/evaluation_best.json results/strategies_*/evaluation_worst.json
```

输出：`results/comparison_YYYYMMDD_HHMMSS/`
- `comparison_chart.png`：对比图表
- `comparison_report.txt`：详细文本报告
- `comparison_report.json`：JSON格式结果

### 可视化积水点分布

```bash
cd src
python visualize_waterlogging.py
```

生成：`results/waterlogging_visualization_*.png`

## 核心算法

### 策略生成算法
```
1. 解析路由文件，统计每个积水点组的车流量
2. 按车流量排序（降序=最优策略，升序=最差策略）
3. 根据 max_clean_at_once 参数分批
4. 输出排水顺序和批次划分
```

### 静态评估方法
```
对于每个排水批次完成状态：
  1. 设置已排水组为正常速度（15 m/s）
  2. 设置未排水组为积水速度（1.5 m/s）
  3. 运行独立仿真
  4. 在多个延迟点测量性能指标
     - 延迟点 = 批次完成时间 + 评估延迟
     - 例如：批次2完成于1200秒，评估点为1230s、1260s、1320s
  5. 记录累计通过量、排队长度、平均速度
```

## 输出结果说明

### 策略文件 (`*_strategy.json`)
```json
{
  "strategy_name": "best",
  "description": "按交通流量排序（高到低）",
  "traffic_flow": {
    "g5": 5234,  # 流量最高
    "g6": 4123,
    ...
  },
  "batches": [
    ["g5", "g6", "g8"],  # 第1批
    ["g1", "g2", "g3"],  # 第2批
    ...
  ],
  "drainage_order": ["g5", "g6", "g8", "g1", ...]
}
```

### 评估结果 (`evaluation_*.json`)
```json
{
  "strategy_name": "best",
  "batch_results": [
    {
      "batch_index": 0,  # 全部积水状态
      "num_drained": 0,
      "delay_measurements": [
        {
          "delay_steps": 30,
          "cumulative_throughput": 1234,  # 累计通过量
          "queue_length": 345.67,         # 平均排队长度
          "avg_speed": 5.23               # 平均速度（m/s）
        },
        ...
      ]
    },
    {
      "batch_index": 1,  # 完成第1批排水
      "num_drained": 3,
      ...
    }
  ]
}
```

### 对比报告 (`comparison_report.txt`)
```
================================================================================
                  内涝排水策略对比报告
================================================================================
生成时间: 2026-02-03 10:30:00
对比策略: best, worst

批次    策略       已排水  累计通过量      排队长度        平均速度
--------------------------------------------------------------------------------
1       best       3       2345            123.45          8.23
1       worst      3       1987            234.56          6.12
...

改进分析:
  批次1  累计通过量  +358 (+18.0%)
         排队长度    -111 (-47.3%)
         平均速度    +2.11 (+34.5%)
```

## 自定义模拟器对接

如果您使用自研交通仿真器（而非SUMO），请参考 `SIMULATOR_INTEGRATION.md` 文档，了解：
- 必须实现的接口函数
- 数据格式要求
- 示例代码

关键接口：
- `start_simulation()` - 启动仿真
- `simulation_step()` - 单步推进
- `get_lane_vehicle_ids()` - 查询车道上的车辆
- `set_vehicle_max_speed()` - 设置车辆限速
- `close_simulation()` - 关闭仿真

## 常见问题

### Q1: 为什么使用"静态评估"而非"连续仿真"？
**A:** 静态评估对每个排水完成状态运行独立仿真，避免了历史状态影响，能更客观地对比不同策略在相同排水进度下的效果。类似于雪地铲雪的评估方法。

### Q2: 如何调整积水区域的速度限制？
**A:** 修改 `config.json` 中的 `flooded_speed`（积水速度）和 `normal_speed`（正常速度）参数。

### Q3: 可以增加更多策略吗？
**A:** 可以。在 `src/generate_strategy.py` 中添加新函数（如随机策略、基于地理位置的策略等），并在 `config.json` 的 `strategies` 部分启用。

### Q4: 如何修改积水点分组？
**A:** 编辑 `config.json` 的 `waterlogging_points` 部分，添加/删除/修改积水点组。每个组是一个edge ID列表。

### Q5: 评估延迟点是什么意思？
**A:** 评估延迟是指在排水批次完成后等待多久再测量性能。例如，`[30, 60, 120]` 表示在批次完成后30秒、60秒、120秒各测量一次，观察交通恢复情况。

## 技术支持

- **问题反馈**：提交Issue到项目仓库
- **功能建议**：欢迎提交Pull Request
- **文档改进**：docs/ 目录下包含更多详细文档

## 许可证

本项目遵循 MIT 许可证。详见 LICENSE 文件。

---

**最后更新**：2026-02-03  
**版本**：v1.0
