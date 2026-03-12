# 高峰期交通模拟 - 技术设计文档

## 1. 背景

现有的交通流量生成工具（如 mosstool）使用均匀随机采样生成车辆起终点，无法体现城市交通中不同区域流量差异显著的特征。高峰时段，商业区、交通枢纽等区域流量远高于住宅区，需要一种基于 OD 矩阵的加权采样方法。

## 2. 设计目标

- 基于 OD 矩阵数据，将宏观交通需求映射到微观路网
- 保持与现有仿真框架的兼容性
- 最小化代码改动，通过注入方式修改采样逻辑

## 3. 核心设计

### 3.1 OD 矩阵 → 车道权重

```
OD矩阵: {(origin_taz, dest_taz): flow_count}
    ↓
TAZ-Lane映射: {taz_id: [lane_id_1, lane_id_2, ...]}
    ↓
车道权重: {lane_id: weight}
```

### 3.2 加权采样公式

对于起点选择：
$$P(l_i | origin\_taz) = \frac{w_i^{out}}{\sum_{j \in L_{taz}} w_j^{out}}$$

对于终点选择：
$$P(l_i | dest\_taz) = \frac{w_i^{in}}{\sum_{j \in L_{taz}} w_j^{in}}$$

### 3.3 代码修改点

#### 修改文件
`mosstool/trip/generator/random.py`

#### 修改函数
`_rand_position(self, lanes, ...)`

#### 修改逻辑
```python
# 原始代码（均匀采样）
def _rand_position(self, lanes):
    lane = random.choice(lanes)
    ...

# 修改后（加权采样）
def _rand_position(self, lanes):
    if self._lane_weights:
        weights = [self._lane_weights.get(lane.id, 1.0) for lane in lanes]
        lane = random.choices(lanes, weights=weights, k=1)[0]
    else:
        lane = random.choice(lanes)
    ...
```

## 4. 数据接口需求

### 4.1 OD 矩阵格式
```json
{
  "od_pairs": [
    {"origin": "TAZ_001", "destination": "TAZ_002", "flow": 1500},
    {"origin": "TAZ_001", "destination": "TAZ_003", "flow": 800},
    ...
  ],
  "time_period": "07:30-08:30",
  "unit": "vehicles/hour"
}
```

### 4.2 TAZ-Lane 映射格式
```json
{
  "TAZ_001": ["lane_10001", "lane_10002", "lane_10003"],
  "TAZ_002": ["lane_20001", "lane_20002"],
  ...
}
```

## 5. 待解决问题

1. OD 数据接口模块尚未提供
2. TAZ 划分与路网车道的精确映射关系待确认
3. 需要验证加权采样后的交通分布是否符合实际观测

## 6. 实施计划

1. 环境更新后获取 OD 数据接口
2. 实现 TAZ-Lane 映射模块
3. 注入加权采样逻辑到 mosstool
4. 对比验证：均匀采样 vs 加权采样的流量分布差异
