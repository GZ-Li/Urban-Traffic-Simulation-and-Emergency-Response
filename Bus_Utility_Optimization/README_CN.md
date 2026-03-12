# 基于加权 MaxPressure 的公交车利用率优化

基于加权 MaxPressure 算法的公交优先信号控制系统，通过调整车辆类型权重提升公交通行效率。

## 项目简介

本项目通过在 MaxPressure 算法中为公交车所在车道赋予更高权重，生成公交优先的信号配时方案，提升公交车利用率。系统对比两种方案：

- **Webster（基准方案）**：传统固定配时 + 公交利用率评估
- **公交加权 MaxPressure → 固定配时（优化方案）**：公交优先的动态优化

## 核心功能

- **多模态感知**：区分车道上的公交车辆与社会车辆
- **加权压力计算**：为公交车辆赋予更高权重（如 2.0-5.0）
- **方案固化**：生成标准信号机配时表（JSON 格式）
- **效能验证**：评估公交利用率提升效果

## 项目结构

```
Bus_Utility_Optimization/
├── README.md                              # 英文说明文档
├── README_CN.md                           # 中文说明文档（本文件）
├── run_bus_webster.sh                     # Webster 基准实验脚本
├── run_bus_weighted_mp.sh                 # 公交加权 MP 实验脚本
├── src/                                   # 源代码
│   ├── bus_opt/
│   │   ├── runner.py                     # 实验主调度器
│   │   ├── weighted_pressure.py         # 公交加权 MaxPressure 控制器
│   │   └── bus_selector.py              # 公交车选择器
│   ├── road_opt/
│   │   ├── max_pressure.py              # 基础 MaxPressure 算法
│   │   ├── fixed_timing.py              # 固定配时部署器
│   │   ├── phase_collector.py           # 相位时长数据收集器
│   │   └── phase_ratio.py              # 相位比例估算器
│   ├── metrics/
│   │   └── evaluator.py                 # 性能指标 & 公交利用率评估器
│   └── runtime/
│       └── sim_runner.py                # 仿真运行器封装
└── results/                              # 输出目录
    └── sample_bus_opt_20260116/          # 实验结果示例
        ├── metrics.json                  # 性能指标
        ├── experiment_config.json        # 实验配置
        ├── bus_ids.json                  # 公交车 ID 列表
        └── fixed_timing_bus_weighted_mp.json  # 公交优先配时方案
```

## 算法原理

### 加权压力最大化模型

$$Pressure(p) = \sum_{l \in Incoming(p)} (W_{bus} \cdot N_{bus}^l + W_{car} \cdot N_{car}^l) - \sum_{l \in Outgoing(p)} (W_{bus} \cdot N_{bus}^l + W_{car} \cdot N_{car}^l)$$

其中：
- $W_{bus}$：公交权重系数（通常 > 1.0，如 2.0）
- $W_{car}$：社会车辆权重系数（通常 = 1.0）
- $N_{bus}^l, N_{car}^l$：车道上的公交车和社会车辆数量

### 两阶段优化流程

1. **阶段 1 - 学习**：运行公交加权 MaxPressure，统计各路口相位占比
   - 实时查询公交车位置，判断各车道是否有公交
   - 有公交的车道压力乘以权重系数 `bus_weight_alpha`
2. **阶段 2 - 评估**：使用固化的配时方案运行仿真，评估公交利用率和整体性能

### 公交利用率定义

$$公交利用率 = \frac{公交车速度 > 阈值的时间}{公交车启动后的总运行时间}$$

## 配置参数

### Webster 基准方案 (`run_bus_webster.sh`)

```bash
--scenario webster              # Webster 算法
--cycle_seconds 60              # 信号灯周期（秒）
--add_bus_count 30              # 新增公交车数量
--bus_speed_threshold 5.0       # 公交速度阈值（m/s）
--total_steps 120               # 总步数
--interval 30                   # 每步时长（秒）
```

### 公交加权 MaxPressure 优化方案 (`run_bus_weighted_mp.sh`)

```bash
--scenario bus_weighted_mp_fixed  # 公交加权 MP 两阶段
--add_bus_count 30                # 新增公交车数量
--bus_speed_threshold 5.0         # 公交速度阈值（m/s）
--bus_weight_alpha 2.0            # 公交权重系数（越大越优先公交）
--cycle_seconds 90                # 信号灯周期（秒）
--min_green_seconds 30            # 单相位最小绿灯时间（秒）
--mp_warmup_cycles 1              # MP 热身周期数
--mp_collect_cycles 10            # MP 统计周期数
--min_phase_seconds 15            # 固定配时的单相位最小时长（秒）
--total_steps 120                 # 评估阶段总步数
--interval 30                     # 每步时长（秒）
```

### 公交权重参数说明

| 值 | 效果 |
|----|------|
| 1.0 | 不优先公交（等同于普通 MaxPressure） |
| 2.0 | 中等优先（公交车所在车道的压力翻倍） |
| 5.0+ | 强公交优先 |

## 使用方法

### 运行 Webster 基准实验

```bash
bash run_bus_webster.sh
```

### 运行公交加权 MaxPressure 优化实验

```bash
bash run_bus_weighted_mp.sh
```

### 对比实验流程

```bash
# 1. 运行基准方案
bash run_bus_webster.sh

# 2. 运行公交优先方案
bash run_bus_weighted_mp.sh

# 3. 对比公交利用率
# 重点关注 bus_utilization 指标的提升
```

## 输出结果

结果保存在 `results/bus_opt/YYYYMMDD-HHMMSS/`：
- `metrics.json` - 性能指标（包含 `bus_utilization`）
- `fixed_timing_bus_weighted_mp.json` - 学习到的固定配时
- `phase1_mp_collection/` - 第一阶段公交加权 MP 学习日志
- `bus_ids.json` - 使用的公交车 ID 列表
- `experiment_config.json` - 实验配置

### 指标示例

```json
{
  "avg_speed": 12.69,
  "avg_travel_time": 202.49,
  "avg_queue": 0.0109,
  "queue_p95": 0.0123,
  "queue_max": 0.0127,
  "bus_utilization": 0.2195,
  "time_above_threshold": 5400.0,
  "total_time": 24600.0,
  "num_buses": 30
}
```

## 性能指标说明

| 指标 | 含义 | 单位 |
|------|------|------|
| `avg_speed` | 平均车速 | m/s |
| `avg_travel_time` | 平均通行时间 | 秒 |
| `avg_queue` | 平均排队长度（拥堵指数） | 归一化 |
| `bus_utilization` | 公交利用率 | 比率 [0, 1] |
| `time_above_threshold` | 公交高速运行总时间 | 秒 |
| `total_time` | 公交总运行时间 | 秒 |
| `num_buses` | 公交车数量 | 辆 |

## 常用参数调整

### 调整公交优先级

```bash
--bus_weight_alpha 1.0   # 不优先公交
--bus_weight_alpha 2.0   # 中等优先
--bus_weight_alpha 5.0   # 强公交优先
```

### 调整公交车数量

```bash
--add_bus_count 50   # 新增 50 辆公交车（默认 30）
```

### 设置随机种子

```bash
--seed 42   # 固定随机种子，确保结果可复现
```
