# 扫雪算法仿真系统

基于交通流量的智能扫雪路径规划与SUMO仿真评估系统。支持多种策略对比。

## 📁 文件结构

```
snow_plowing/
├── config.json                      # 主配置文件
├── regions.json                     # 区域划分配置
├── main.py                          # 主程序入口
├── generate_strategies.py           # 策略生成器
├── evaluate_strategies.py           # 策略评估器
├── compare_results.py               # 策略对比工具
├── strategies/                      # 策略模块
│   ├── __init__.py
│   ├── greedy_strategy.py          # 贪心策略（全局分治+局部贪心）
│   └── random_strategy.py          # 随机策略（对比基准）
├── generate_baseline_strategy.py   # Baseline策略生成
├── evaluate_baseline.py             # Baseline评估
└── results/                         # 输出结果目录（不要手动修改）
    ├── snowplow_<strategy>_time_steps_record.json
    ├── strategy_<strategy>_details.json
    ├── sumo_evaluation_<strategy>_results.json
    ├── evaluation_<strategy>_plots.png
    └── strategy_comparison_*.png
```

## 🚀 快速开始

### 1. 配置文件

**主配置 (config.json)**
- 网络文件路径
- SUMO配置
- 扫雪车参数
- 评估时间点

**区域配置 (regions.json)**
- 5个区域的边界定义
- 每个区域的起始边
- 区域颜色标识

### 2. 运行方式

#### 方式1: 完整流程（推荐）
```bash
# 运行greedy策略
python main.py --full

# 运行random策略
python main.py --full -s random --seed 42
```

#### 方式2: 分步运行

**步骤1: 生成策略**
```bash
# 生成greedy策略
python main.py --generate -s greedy

# 生成random策略（带随机种子）
python main.py --generate -s random --seed 42
```

**步骤2: 评估策略**
```bash
# 评估greedy策略
python main.py --evaluate -s greedy

# 评估random策略
python main.py --evaluate -s random
```

**步骤3: 对比策略**
```bash
# 对比greedy和random策略
python main.py --compare -s "greedy random"
```

#### 方式3: Baseline对比
```bash
# 生成并评估baseline（所有道路0时刻清扫完成）
python main.py --baseline
```

### 3. 直接调用模块
```bash
# 生成策略
python generate_strategies.py -s greedy
python generate_strategies.py -s random --seed 42

# 评估策略
python evaluate_strategies.py -s greedy

# 对比策略
python compare_results.py -s greedy random
```

## 📊 策略说明

### 1. Greedy策略（贪心策略）

**算法原理**:
- **全局分治**: 将路网划分为5个区域，每个区域分配一辆扫雪车
- **局部贪心**: 每辆车优先清扫交通流量大的道路
- **路径规划**: 使用Dijkstra算法寻找最短路径连接未清扫道路

**优势**:
- 优先清扫高流量道路，减少交通拥堵影响
- 考虑双向/单向车道的不同处理方式
- 支持传送机制应对孤立路段

**实现文件**: `strategies/greedy_strategy.py`

### 2. Random策略（随机策略）

**算法原理**:
- **全局分治**: 同样划分5个区域
- **随机选择**: 随机选择未清扫道路
- **路径规划**: 使用相同的路径规划算法

**用途**:
- 作为对比基准，验证贪心策略的优势

**实现文件**: `strategies/random_strategy.py`

### 3. Baseline（理想场景）

**场景设定**:
- 所有道路在0时刻就已清扫完成
- 用于评估无积雪情况下的交通指标
- 作为性能上限参考

## 🔧 核心模块

### generate_strategies.py - 策略生成器

**功能**:
1. 加载路网和交通流量数据
2. 将道路分配到5个区域
3. 调用指定策略生成清扫路径
4. 计算时间步记录（每30分钟）
5. 保存策略详情和时间步记录

**输出**:
- `snowplow_<strategy>_time_steps_record.json`: 时间步清扫记录
- `strategy_<strategy>_details.json`: 策略详细信息

### evaluate_strategies.py - 策略评估器

**功能**:
1. 加载策略时间步记录
2. 在SUMO中模拟不同时间点的交通
3. 根据道路清扫状态动态设置车辆参数
   - 已清扫: 正常道路参数
   - 未清扫: 积雪道路参数（低速、低加速度）
4. 统计全局平均速度、车辆数等指标
5. 生成可视化图表

**输出**:
- `sumo_evaluation_<strategy>_results.json`: 评估结果
- `evaluation_<strategy>_plots.png`: 可视化图表

### compare_results.py - 策略对比工具

**功能**:
1. 加载多个策略的评估结果
2. 生成对比图表（4个子图）:
   - 平均速度对比 (m/s)
   - 平均速度对比 (km/h)
   - 清扫进度对比
   - 综合性能指标
3. 计算对比指标
4. 生成对比报告

**输出**:
- `strategy_comparison_<timestamp>.png`: 对比图表
- `strategy_comparison_report_<timestamp>.json`: 对比报告

## ⚙️ 配置说明

### config.json 关键配置

```json
{
  "network": {
    "net_file": "路网文件路径",
    "regions_file": "regions.json"
  },
  "snowplow": {
    "num_trucks": 5,
    "speed_kmh": 25,
    "cleaning_rate_per_lane": 0.015
  },
  "road_parameters": {
    "cleaned": {
      "max_speed": 33,
      "accel": 2.6,
      "decel": 4.5
    },
    "unclean": {
      "max_speed": 4,
      "accel": 1.5,
      "decel": 2.5
    }
  },
  "sumo_config": {
    "use_scaled": true,
    "simulation_steps": 200,
    "evaluation_hours": [0, 1, 2, 3, 4, 5]
  }
}
```

### regions.json 区域配置

```json
{
  "regions": {
    "region1": {
      "name": "区域1",
      "min_x": 7500,
      "max_x": 12469.37,
      "start_edge": "200082260"
    },
    ...
  }
}
```

## 📈 输出结果说明

### 1. 时间步记录
```json
{
  "step_0_time_0min": {
    "time_minutes": 0,
    "total_cleaned_edges": [],
    "num_total_cleaned": 0
  }
}
```

### 2. 评估结果
```json
{
  "strategy_name": "greedy",
  "results": {
    "hour_0": {
      "global_avg_speed_ms": 15.6,
      "num_cleaned_edges": 245
    }
  }
}
```

### 3. 对比报告
```json
{
  "strategies_compared": ["greedy", "random"],
  "metrics": {
    "greedy": {
      "avg_speed_kmh": 56.2,
      "final_cleaned_roads": 2450
    }
  },
  "summary": {
    "best_avg_speed": "greedy"
  }
}
```

## 🛠️ 扩展新策略

### 步骤1: 创建策略类
在 `strategies/` 目录下创建新文件，继承策略接口：

```python
class MyStrategy:
    def __init__(self, network_data, regions_config, traffic_flow):
        # 初始化
        pass
    
    def generate(self, **kwargs):
        # 生成清扫路径
        return car_states
    
    def get_name(self):
        return "my_strategy"
    
    def get_description(self):
        return "我的策略描述"
```

### 步骤2: 注册策略
在 `strategies/__init__.py` 中注册：

```python
from .my_strategy import MyStrategy

STRATEGY_REGISTRY = {
    'greedy': GreedyStrategy,
    'random': RandomStrategy,
    'my_strategy': MyStrategy,  # 新增
}
```

### 步骤3: 使用新策略
```bash
python main.py --full -s my_strategy
```

## 📝 参考文献

- 原始贪心策略: `snow_plow_project/strateg5.py`
- 原始评估脚本: `snow_plow_project/evaluate_snowplow.py`
- 对比分析: `snow_plow_project/compare_strategies.py`

## 🔬 实验建议

### 实验1: 单策略评估
```bash
python main.py --full -s greedy
python main.py --full -s random --seed 42
```

### 实验2: 策略对比
```bash
python main.py --compare -s "greedy random"
```

### 实验3: Baseline对比
```bash
python main.py --baseline
python main.py --compare -s "greedy random baseline"
```

## 🐛 故障排查

1. **配置文件错误**: 检查 config.json 和 regions.json 路径
2. **SUMO连接失败**: 确保SUMO环境变量设置正确，SUMO-GUI未占用端口
3. **策略记录不存在**: 先运行 `--generate` 再运行 `--evaluate`
4. **对比失败**: 确保所有待对比策略都已经过评估

## 📧 技术支持

遇到问题请检查：
- Python 3.7+
- NetworkX, SUMO (with TraCI), Matplotlib, NumPy
- 配置文件路径正确性
- results文件夹权限
