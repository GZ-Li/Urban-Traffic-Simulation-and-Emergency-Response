# 基于 OD 矩阵的城市交通高峰模拟

基于 OD（Origin-Destination）矩阵的微观交通流生成系统，将宏观的交通需求矩阵映射为微观路网的车辆生成参数。

## 项目简介

本项目通过将宏观 OD 矩阵数据转化为微观车辆行程数据，生成真实的高峰期交通模式。使用基于交通流量的加权采样替代均匀随机采样，创建更真实的交通分布。

## 核心功能

- **OD 矩阵解析**：读取区域间的交通流量需求
- **车道映射**：建立交通小区（TAZ）与路网车道（Lane）的对应关系
- **加权采样**：基于流量权重的随机采样，替代均匀分布
- **微观轨迹生成**：生成符合宏观 OD 特征的车辆行程数据

## 算法原理

### 加权采样方法

将默认的均匀采样概率修改为加权采样：

$$P_{weighted}(l_i) = \frac{w_i}{\sum_{j \in L} w_j}$$

其中 $w_i$ 是根据 OD 矩阵推算的车道流量权重。

### 技术实现方案

- 修改 `mosstool/trip/generator/random.py` 的 `_rand_position` 函数
- 使用 `random.choices(lanes, weights=weights)` 进行加权采样
- 使高流量区域的车道更容易被选为起点/终点

## 项目结构

```
Peak_Hour_Traffic_Simulation/
├── README.md                     # 英文说明文档
├── README_CN.md                  # 中文说明文档（本文件）
└── docs/
    └── technical_design.md       # 详细技术设计文档
```

## 当前状态

- **部署状态**：Pending（待部署）
- **原因**：当前环境尚未提供完整的 OD 数据接口模块
- **计划**：代码注入方案已拟定，待环境更新后上线

## 工作流程设计

### 数据流

```
OD 矩阵（宏观需求）
    │
    ▼
TAZ-车道映射
    │
    ▼
车道流量权重计算
    │
    ▼
加权随机采样
    │
    ▼
微观车辆行程数据
```

### 集成接入点

1. **输入**：来自交通调查或模型的 OD 矩阵数据
2. **处理**：在 `mosstool` 中修改权重计算和采样逻辑
3. **输出**：兼容 SUMO/自研仿真器的车辆行程数据

## 核心代码修改说明

### 修改位置

`mosstool/trip/generator/random.py` 中的 `_rand_position` 函数

### 修改前（均匀采样）

```python
lane = random.choice(lanes)  # 均匀分布
```

### 修改后（加权采样）

```python
lane = random.choices(lanes, weights=weights, k=1)[0]  # 基于OD的加权分布
```

### 权重计算

```python
# 从OD矩阵推算各车道的流量权重
for taz_id, lanes in taz_lane_mapping.items():
    flow = od_matrix.get_flow(origin=taz_id)  # 获取该TAZ的出发流量
    weight_per_lane = flow / len(lanes)         # 均分到各车道
    for lane in lanes:
        weights[lane] = weight_per_lane
```

## 依赖

- Python 3.8+
- mosstool（交通仿真工具包）
- numpy

## 参考

- OD 矩阵理论与交通需求建模
- mosstool 框架文档
