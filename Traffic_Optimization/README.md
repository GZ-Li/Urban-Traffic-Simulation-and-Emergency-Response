# 基于 MaxPressure 算法的交通信号优化

基于 MaxPressure 算法的信号灯固定配时方案生成系统，采用"动态生成-静态固化"策略。

## 项目简介

本项目通过 MaxPressure 算法动态学习最优相位时长，再转化为可部署的固定配时方案，实现交通信号优化。系统对比两种方案：

- **Webster（基准方案）**：基于流量采样的经典交通工程配时方法
- **MaxPressure → 固定配时（优化方案）**：基于实时交通压力的自适应学习算法

## 核心功能

- **动态策略生成**：运行 MaxPressure 算法，实时计算各相位压力
- **静态配时固化**：统计相位运行时长占比，生成固定配时方案
- **策略验证**：对比 Webster 基准方案，评估优化效果
- **标准化输出**：生成可部署的静态配时表（JSON 格式）

## 项目结构

```
Traffic_Optimization/
├── README.md                              # 英文说明文档
├── README_CN.md                           # 中文说明文档（本文件）
├── run_webster.sh                         # Webster 基准实验脚本
├── run_mp_fixed.sh                        # MaxPressure 优化实验脚本
├── src/                                   # 源代码
│   ├── road_opt/
│   │   ├── runner.py                     # 实验主调度器
│   │   ├── max_pressure.py              # MaxPressure 核心算法
│   │   ├── webster_timing.py            # Webster 配时计算器
│   │   ├── fixed_timing.py              # 固定配时部署器
│   │   ├── phase_collector.py           # 相位时长数据收集器
│   │   └── phase_ratio.py              # 相位比例估算器
│   ├── metrics/
│   │   └── evaluator.py                 # 性能指标评估器
│   └── runtime/
│       └── sim_runner.py                # 仿真运行器封装
└── results/                              # 输出目录
    └── sample_road_opt_20260116/         # 实验结果示例
        ├── metrics.json                  # 性能指标
        └── experiment_config.json        # 实验配置
```

## 算法原理

### MaxPressure 算法

基于 Varaiya (2013) 提出的自适应信号控制算法，选择压力最大的相位：

$$Pressure(Phase_i) = \sum_{l \in Incoming} w_l \cdot q_l - \sum_{l \in Outgoing} w_l \cdot q_l$$

**目标**：最小化全网总压力 $\sum |Pressure|$

### 两阶段优化流程

1. **阶段 1 - 策略生成**：运行 MaxPressure 动态控制，统计各相位累计运行时长
   - 热身阶段（`mp_warmup_cycles`）：让交通流稳定
   - 统计阶段（`mp_collect_cycles`）：收集相位占比数据
2. **阶段 2 - 策略验证**：加载固化的固定配时方案，运行仿真并与 Webster 方案对比

### Webster 配时算法

基于经典交通工程理论：
1. 采样各车道的排队车辆数
2. 计算各相位的流量比 $y_i = q_i / s_i$
3. 按 Webster 公式分配绿灯时长：$g_i = (y_i / \sum Y) \times (C - n \times L)$

## 配置参数

### Webster 基准方案 (`run_webster.sh`)

```bash
--scenario webster              # 使用 Webster 算法
--cycle_seconds 30              # 信号灯周期（秒）
--min_green_seconds 5           # 单相位最小绿灯时间（秒）
--total_steps 120               # 评估阶段总步数
--interval 30                   # 每步时长（秒）
```

### MaxPressure 优化方案 (`run_mp_fixed.sh`)

```bash
--scenario fixed_from_mp        # 使用 MP 学习固定配时
--cycle_seconds 50              # 信号灯周期（秒）
--min_green_seconds 5           # 单相位最小绿灯时间（秒）
--mp_warmup_cycles 1            # MP 热身周期数
--mp_collect_cycles 10          # MP 统计周期数
--min_phase_seconds 10          # 固定配时的单相位最小时长（秒）
--total_steps 120               # 评估阶段总步数
--interval 30                   # 每步时长（秒）
```

## 使用方法

### 运行 Webster 基准实验

```bash
bash run_webster.sh
```

### 运行 MaxPressure 优化实验

```bash
bash run_mp_fixed.sh
```

### 对比实验流程

```bash
# 1. 运行基准方案
bash run_webster.sh

# 2. 运行优化方案
bash run_mp_fixed.sh

# 3. 对比结果
# 查看 results/ 下两个最新文件夹的 metrics.json
```

## 输出结果

结果保存在 `results/road_opt/YYYYMMDD-HHMMSS/`：
- `metrics.json` - 性能指标
- `fixed_timing_from_mp.json` / `fixed_timing_webster.json` - 配时方案
- `experiment_config.json` - 实验配置
- `mp_phase_statistics.json` - MP 学习阶段的相位统计数据

### 指标示例

```json
{
  "avg_speed": 12.63,
  "avg_travel_time": 200.93,
  "avg_queue": 0.0098,
  "queue_p95": 0.0119,
  "queue_max": 0.0122
}
```

## 性能指标说明

| 指标 | 含义 | 单位 |
|------|------|------|
| `avg_speed` | 平均车速 | m/s |
| `avg_travel_time` | 平均通行时间 | 秒 |
| `avg_queue` | 平均排队长度（拥堵指数） | 归一化 |
| `queue_p95` | 排队长度 95 分位数 | 归一化 |
| `queue_max` | 最大排队长度 | 归一化 |

## 常用参数调整

### 调整仿真时长

```bash
--total_steps 240    # 加倍仿真时长（120→240 步）
--interval 10        # 减小步长（30秒→10秒），提高时间分辨率
```

### 调整信号周期

```bash
--cycle_seconds 60   # 缩短周期会让固定配时更"僵硬"，有利于凸显动态算法优势
```

### 设置随机种子

```bash
--seed 42            # 固定随机种子，确保结果可复现
```

## 依赖

- Python 3.8+
- numpy
- pymongo
- 自研交通仿真引擎（`trafficlight_rl`）

## 算法参考

- **Webster 方法**：经典交通工程配时理论，基于流量比计算最优周期和相位时长
- **MaxPressure**：Varaiya, P. (2013). Max pressure control of a network of signalized intersections. *Transportation Research Part C*, 36, 177-195.
