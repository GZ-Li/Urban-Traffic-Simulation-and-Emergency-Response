# Map-tools Design Document

## map/

### OSM

OSM 模块用于从 OpenStreetMap (OSM) 下载原始数据并将其转换为 GeoJSON 格式，用于构建地图。该模块包含三个主要类：

#### 1. RoadNet 类

**功能概述**：处理 OSM 原始数据为道路网络和交叉口的 GeoJSON 格式

**主要构造函数**：
```python
def __init__(
    self,
    proj_str: Optional[str] = None,
    max_longitude: Optional[float] = None,
    min_longitude: Optional[float] = None,
    max_latitude: Optional[float] = None,
    min_latitude: Optional[float] = None,
    wikipedia_name: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None,
)
```

**核心方法**：

- `create_road_net()`: 主要接口函数，从 OSM 创建道路网络
  - 参数：osm_data_cache（可选的 OSM 数据缓存）、output_path（输出路径）、osm_cache_check（检查输入格式）
  - 返回：道路和交叉口的 GeoJSON 格式数据
  - 处理流程：获取 OSM 数据 → 去除冗余路段/节点 → 转换为单向道路 → 去除孤立道路 → 构建交叉口 → 合并交叉口 → 清理拓扑

- `_download_osm()`: 从 OpenStreetMap 获取原始数据
  - 使用 Overpass API 查询指定边界框内的道路数据
  - 支持通过 wikipedia_name 查询特定区域

- `_remove_redundant_ways()`: 去除冗余路段，合并可连接的相同道路

- `_remove_simple_joints()`: 去除简单连接点，简化道路网络拓扑

- `_make_all_one_way()`: 将双向道路转换为两条单向道路

- `_merge_junction_by_motif()`: 通过识别固定模式合并交叉口
  - 使用 `close_nodes()`、`suc_is_close_by_other_way()`、`motif_H()` 等算法识别需要合并的交叉口

- `_clean_topo()`: 清理拓扑结构
  - 去除重复道路（保留车道最多、长度最短的）
  - 去除平凡交叉口（入度和出度都为1的节点）

- `to_topo()`: 返回道路拓扑的 FeatureCollection 格式
  - way: LineString 表示，包含 id、lanes、highway、max_speed、name 等属性
  - junction: MultiPoint 表示，包含 id、in_ways、out_ways 等属性

**辅助工具函数**：
- `_way_length()`: 计算路段长度
- `_way_coords_xy()` / `_way_coords_lonlat()`: 获取路段坐标
- `_update_node_ways()`: 构建节点到路段的映射关系

#### 2. Building 类

**功能概述**：处理 OSM 原始数据为 AOI（Area of Interest，兴趣区域/建筑区域）的 GeoJSON 格式文件

**主要构造函数**：
```python
def __init__(
    self,
    proj_str: Optional[str] = None,
    max_longitude: Optional[float] = None,
    min_longitude: Optional[float] = None,
    max_latitude: Optional[float] = None,
    min_latitude: Optional[float] = None,
    wikipedia_name: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None,
)
```

**核心方法**：

- `create_building()`: 主要接口函数，从 OSM 创建建筑/AOI
  - 参数：osm_data_cache（可选的 OSM 数据缓存）、output_path（输出路径）、osm_cache_check（检查输入格式）
  - 返回：AOI 的 GeoJSON 格式数据
  - 处理流程：查询原始数据 → 构造 AOI → 转换坐标并输出

- `_query_raw_data()`: 从 OSM API 获取原始数据
  - 查询条件：排除高速公路、隧道、边界、铁路等，包含土地使用、建筑、休闲设施等
  - 支持 way 和 relation 两种类型的几何体

- `_make_raw_aoi()`: 从原始数据构造 AOI
  - 处理 ways_aoi：每个 way 是一个环形，无内部形状
  - 处理 relations：描述多个 way 组成的复杂多边形，可能包含内部空洞
  - 使用 shapely 库进行几何运算和验证

- `_transform_coordinate()`: 坐标变换函数，支持投影坐标系转换

#### 3. PointOfInterest 类

**功能概述**：处理 OSM 原始数据为 POI（Point of Interest，兴趣点）的 GeoJSON 格式文件

**主要构造函数**：
```python
def __init__(
    self,
    max_longitude: Optional[float] = None,
    min_longitude: Optional[float] = None,
    max_latitude: Optional[float] = None,
    min_latitude: Optional[float] = None,
    wikipedia_name: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None,
)
```

**核心方法**：

- `create_pois()`: 主要接口函数，从 OSM 创建兴趣点
  - 参数：osm_data_cache（可选的 OSM 数据缓存）、output_path（输出路径）、osm_cache_check（检查输入格式）
  - 返回：POI 的 GeoJSON 格式数据

- `_query_raw_data()`: 从 OSM API 获取所有节点数据

- `_make_raw_poi()`: 从原始 OSM 数据构造 POI
  - 根据 tags 分类：landuse、leisure、amenity、building
  - 过滤掉值为 "yes" 的无效字段
  - 为每个 POI 分配名称和类别

#### 辅助模块

**_motif.py**: 道路网络拓扑模式识别
- `close_nodes()`: 识别交叉口内的"□"型或"△"型结构
- `suc_is_close_by_other_way()`: 识别通过其他短路径可达的后继节点
- `motif_H()`: 识别 H 型拓扑模式

**_wayutil.py**: 路段处理工具
- `parse_osm_way_tags()`: 解析 OSM way 标签，提取车道数、限速等信息
- `merge_way_nodes()`: 合并两组节点，要求至少有一对端点相同

**osm_const.py**: OSM 常量定义
- `WAY_FILTER`: 道路类型过滤器
- `MAX_SPEEDS`: 各类型道路的最大限速
- `DEFAULT_LANES`: 各类型道路的默认车道数
- `TURN_CONFIG`: 转向配置
- `OVERPASS_FILTER`: Overpass API 查询过滤条件

### SUMO

SUMO 模块提供了从 SUMO 仿真器的路网文件格式转换为统一地图格式的功能。主要用于处理 SUMO .net.xml 文件和相关辅助文件，生成包含车道、道路、交叉口、AOI 和 POI 的完整地图数据。

#### MapConverter 类

**功能概述**：SUMO 地图转换工具的核心类，负责将 SUMO 格式的路网数据转换为标准化的地图格式。

**主要构造函数**：
```python
def __init__(
    self,
    net_path: str,
    default_lane_width: float = 3.2,
    green_time: float = 60.0,
    yellow_time: float = 5.0,
    poly_path: Optional[str] = None,
    additional_path: Optional[str] = None,
    traffic_light_path: Optional[str] = None,
    traffic_light_min_direction_group: int = 3,
    merge_aoi: bool = False,
    multiprocessing_chunk_size: int = 500,
    workers: int = cpu_count(),
)
```

**构造函数参数说明**：
- `net_path`: SUMO 路网文件路径（.net.xml）
- `default_lane_width`: 默认车道宽度（米）
- `green_time` / `yellow_time`: 交通信号灯的绿灯/黄灯时间
- `poly_path`: SUMO AOI/POI 文件路径（.poly.xml）
- `additional_path`: SUMO 附加文件路径（包含公交站等）
- `traffic_light_path`: SUMO 交通信号灯文件路径
- `traffic_light_min_direction_group`: 生成交通信号灯的最小方向组数
- `merge_aoi`: 是否合并邻近的 AOI
- `multiprocessing_chunk_size` / `workers`: 多进程处理参数

**核心方法**：

- `convert_map()`: 主要接口函数，执行完整的地图转换流程
  - 返回：转换后的地图数据字典，包含车道、道路、交叉口、AOI、POI 等信息
  - 处理流程：创建交叉口 → 添加车道连接 → 添加 AOI 到地图 → 生成输出地图

- `get_sumo_id_mappings()`: 获取 SUMO 原始 ID 到 UID 的映射关系
  - 返回：原始 ID 到新 UID 的映射字典

**内部处理方法**：

- `_create_junctions()`: 基于 SUMO 路网连接关系重构交叉口
  - 处理正常的车道连接关系
  - 添加双向道路的掉头连接
  - 区分车行道和人行道的连接类型

- `_connect_lane()`: 连接两个车道
  - 参数：输入车道 UID、输出车道 UID、原始车道 ID、转向类型、车道类型、交叉口 ID、最大速度
  - 功能：使用贝塞尔曲线连接车行道，直线连接人行道
  - 返回：新创建的连接车道的 UID

- `_add_lane_conn()`: 添加交叉口外的车道连接关系
  - 处理道路间的直接连接
  - 排除交叉口内部的车道

- `_add_aois_to_map()`: 将 AOI、POI 和公交站添加到地图中
  - 预处理读取 AOI、POI 和公交站数据
  - 生成车行道和人行道的匹配器
  - 使用多进程进行 AOI 匹配和合并

- `_get_output_map()`: 后处理，将地图数据转换为输出格式
  - 生成最终的车道、道路、交叉口数据结构
  - 添加车道的左右关系
  - 计算地图边界和投影信息

**辅助处理方法**：

- `_add_junc_lane_overlaps()`: 为交叉口车道添加重叠区域
- `_add_driving_lane_group()`: 为交叉口聚类车道组
- `_add_traffic_light()`: 添加交通信号灯控制

**内部工具函数**：

- `shape2array()`: 将 SUMO shape 字符串转换为坐标数组
- `get_lane_type()`: 根据交通限制确定车道类型（人行道/车行道）
- `get_turn_type()`: 根据连接方向确定转向类型
- `sort_lane_ids()`: 根据车道空间位置从左到右排序
- `line2nodes()`: 将 LineString 转换为节点格式

**数据结构**：

转换器内部维护以下主要数据结构：
- `_map_lanes`: 车道信息映射（UID → 车道数据）
- `_map_roads`: 道路信息映射（UID → 道路数据）
- `_map_junctions`: 交叉口信息映射（UID → 交叉口数据）
- `_map_aois` / `_map_pois`: AOI/POI 信息映射
- `_id2uid`: 原始 ID 到 UID 的映射关系

**输出格式**：

生成的地图数据包含以下主要组成部分：
- `header`: 地图元信息（名称、日期、边界、投影等）
- `lanes`: 车道列表，包含几何、类型、速度限制、连接关系等
- `roads`: 道路列表，包含车道 ID 列表和道路属性
- `junctions`: 交叉口列表，包含中心点和关联车道
- `aois` / `pois`: 兴趣区域和兴趣点列表

### Map Builder

Map Builder 模块提供了从 GeoJSON 格式文件构建完整地图的功能。该模块是整个地图工具链的核心组件，负责将道路网络拓扑数据转换为包含详细车道信息、交叉口、人行道、AOI 和 POI 的完整地图结构。

#### Builder 类

**功能概述**：从 GeoJSON 格式文件构建地图的核心类，支持复杂的交叉口处理、车道连接、人行道生成和多种地图元素集成。

**主要构造函数**：
```python
def __init__(
    self,
    net: Union[FeatureCollection, Map],
    proj_str: Optional[str] = None,
    aois: Optional[FeatureCollection] = None,
    pois: Optional[FeatureCollection] = None,
    public_transport: Optional[Dict[str, List]] = None,
    pop_tif_path: Optional[str] = None,
    landuse_shp_path: Optional[str] = None,
    traffic_light_min_direction_group: int = 3,
    default_lane_width: float = 3.2,
    gen_sidewalk_speed_limit: float = 0,
    gen_sidewalk_length_limit: float = 5.0,
    expand_roads: bool = False,
    road_expand_mode: Union[Literal["L"], Literal["M"], Literal["R"]] = "R",
    aoi_mode: Union[Literal["append"], Literal["overwrite"]] = "overwrite",
    traffic_light_mode: Union[
        Literal["green_red"],
        Literal["green_yellow_red"],
        Literal["green_yellow_clear_red"],
    ] = "green_yellow_clear_red",
    multiprocessing_chunk_size: int = 500,
    green_time: float = 30.0,
    yellow_time: float = 5.0,
    strict_mode: bool = False,
    merge_aoi: bool = True,
    correct_green_time: bool = False,
    split_too_long_walking_lanes: bool = False,
    max_walking_lane_length: float = 100.0,
    aoi_matching_distance_threshold: float = 30.0,
    output_lane_length_check: bool = False,
    workers: int = cpu_count(),
)
```

**核心方法**：

- `build(name: str)`: 主要构建接口函数
  - 功能：执行完整的地图构建流程
  - 参数：地图名称
  - 返回：完整的地图数据结构
  - 处理流程：
    1. 分类道路和交叉口（`_classify()`）
    2. 识别主干道和辅助道路（`_classify_main_way_ids()`）
    3. 创建 1-N 型交叉口（`_create_junction_for_1_n()`）
    4. 创建 N-N 型交叉口（`_create_junction_for_n_n()`）
    5. 创建人行道（`_create_walking_lanes()`）
    6. 扩展剩余道路（`_expand_remain_roads()`）
    7. 后处理和添加 AOI（`_post_process()`, `_add_all_aoi()`）

- `get_output_map(name: str)`: 生成最终的地图输出格式
  - 功能：将内部数据结构转换为标准化的地图格式
  - 返回：包含 header、lanes、roads、junctions、aois、pois 的地图字典

**道路和交叉口处理方法**：

- `_classify()`: 对进入和离开交叉口的道路进行分类
  - 使用 KMeans 聚类算法对道路角度进行聚类
  - 将道路按照方向分组，识别交叉口类型
  - 生成 in_way_groups 和 out_way_groups

- `_classify_main_way_ids()`: 识别主干道和辅助道路
  - 根据道路的空间位置和角度识别主要道路
  - 区分主干道和左右辅助道路

- `_create_junction_for_1_n()`: 创建 1 进 N 出型交叉口
  - 基本逻辑：识别主路、左转道、右转道和掉头道
  - 处理车道连接和转向配置
  - 支持复杂的车道分配策略

- `_create_junction_for_n_n()`: 创建 N 进 N 出型复杂交叉口
  - 处理多进多出的复杂交叉口拓扑
  - 支持多种转向组合和车道分配

- `_expand_roads()`: 道路扩展功能
  - 根据交叉口类型和道路类型扩展车道
  - 支持主干道、辅助道、左转道、右转道的不同扩展策略
  - 计算适当的道路缩进长度

**车道连接和处理方法**：

- `_connect_lane_group()`: 连接车道组
  - 参数：输入车道列表、输出车道列表、转向类型、车道类型、交叉口 ID
  - 功能：使用贝塞尔曲线连接车行道，直线连接人行道
  - 算法：基于中心对齐，连接到最近的车道

- `_delete_lane()`: 删除车道
  - 功能：删除指定车道并更新相关连接关系
  - 支持删除道路车道和交叉口车道

- `_reset_lane_uids()`: 重置车道 UID
  - 功能：批量更新车道 ID 并维护连接关系

**人行道处理方法**：

- `_create_walking_lanes()`: 创建人行道系统
  - 为道路自动生成左右人行道
  - 处理人行道的连接和合并

- `_add_sidewalk()`: 添加人行道
  - 在指定位置添加左侧或右侧人行道
  - 处理人行道的起始和结束点

- `_create_junction_walk_pairs()`: 创建交叉口人行道配对
  - 规则1：同方向进出道路在右侧构建人行道
  - 规则2：独立进出道路在左右两侧构建人行道

**辅助功能方法**：

- `_add_junc_lane_overlaps()`: 为交叉口车道添加重叠区域
- `_add_driving_lane_group()`: 添加车行道分组
- `_add_traffic_light()`: 添加交通信号灯控制
- `_add_public_transport()`: 添加公共交通系统
- `_add_all_aoi()`: 添加所有 AOI 和 POI

**可视化和调试方法**：

- `draw_junction()`: 绘制交叉口图像
  - 参数：交叉口 ID、保存路径、修剪长度
  - 功能：生成交叉口的可视化图像用于调试

- `draw_walk_junction()`: 绘制交叉口人行道图像
  - 专门用于可视化人行道连接情况

**数据输出方法**：

- `write2json()`: 将扩展后的道路写入 GeoJSON 文件
- `write2db()`: 将地图数据写入 MongoDB 数据库

**核心数据结构**：

Builder 类内部维护以下主要数据结构：
- `map_roads`: 道路信息映射（ID → 道路数据）
- `map_junctions`: 交叉口信息映射（ID → 交叉口数据）  
- `map_lanes`: 车道信息映射（ID → 车道几何）
- `lane2data`: 车道到数据的映射（几何 → 车道属性）
- `map_aois` / `map_pois`: AOI/POI 信息映射
- `public_transport_data`: 公共交通数据

**配置参数说明**：

- `expand_roads`: 是否根据交叉口类型扩展道路
- `road_expand_mode`: 道路扩展模式（左/中/右）
- `traffic_light_mode`: 交通信号灯生成模式
- `merge_aoi`: 是否合并邻近的 AOI
- `strict_mode`: 严格模式，遇到警告时退出程序
- `aoi_matching_distance_threshold`: AOI 匹配距离阈值

**输出格式**：

生成的地图数据包含以下主要组成部分：
- `header`: 地图元信息（名称、日期、边界、投影等）
- `lanes`: 详细的车道信息，包含几何、类型、速度、连接关系、左右车道关系等
- `roads`: 道路信息，包含车道 ID 列表和道路属性
- `junctions`: 交叉口信息，包含中心点和关联车道
- `aois` / `pois`: 兴趣区域和兴趣点
- `_sublines`: 公共交通线路信息

### Public Transport

Public Transport 模块提供了从多种数据源获取和处理公共交通数据的功能，包括公交和地铁系统。该模块支持从 Transitland API、高德地图 API 和 OpenStreetMap 获取数据，并将其转换为标准化的公共交通格式。

#### 主要类和功能

**1. TransitlandPublicTransport 类**

**功能概述**：从 Transitland 和 OSM 获取公共交通数据并处理为标准格式

**构造函数**：
```python
def __init__(
    self,
    proj_str: str,
    max_longitude: float,
    min_longitude: float,
    max_latitude: float,
    min_latitude: float,
    transitland_ak: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None,
    wikipedia_name: Optional[str] = None,
    from_osm: bool = False,
)
```

**核心方法**：

- `_query_raw_data_from_osm()`: 从 OpenStreetMap 获取原始公共交通数据
  - 查询公交、地铁路线和站点信息
  - 使用 Overpass API 进行数据查询
  - 支持通过 wikipedia_name 指定查询区域

- `_process_raw_data_from_osm()`: 处理 OSM 原始数据
  - 解析节点、路径和关系数据
  - 识别公交站点和地铁站
  - 构建路线和站点的关联关系

- `_fetch_raw_stops()`: 获取原始站点数据
  - 从 Transitland API 批量获取站点信息
  - 支持分区域查询以处理大范围数据

- `_fetch_raw_lines()`: 获取原始线路数据
  - 获取公交和地铁线路的详细信息
  - 包含路线几何和站点序列

- `process_raw_data()`: 处理原始数据
  - 清理和标准化站点和线路数据
  - 合并重复的站点和路线
  - 验证数据完整性

- `merge_raw_data()`: 合并原始数据
  - 合并相同名称的站点（基于距离阈值）
  - 地铁站合并距离：800 米
  - 公交站合并距离：30 米

- `get_output_data()`: 生成最终输出数据
  - 返回标准化的公共交通数据格式
  - 包含线路、站点和时刻表信息

**2. AmapBus 类**

**功能概述**：从高德地图获取公交数据

**构造函数**：
```python
def __init__(
    self,
    city_name_en_us: str,
    city_name_zh_cn: str,
    bus_heads: str,
    amap_ak: str,
)
```

**核心方法**：

- `_fetch_raw_data()`: 从 8684 公交网站爬取公交线路基础信息
  - 按照公交线路首字符分类获取
  - 获取线路名称、起终点站和途径站点

- `_fetch_amap_positions()`: 获取站点的高德地图坐标
  - 使用高德地图 API 查询站点精确位置
  - 获取站点的 BV 编码用于后续查询

- `_fetch_amap_lines()`: 获取高德地图线路详细信息
  - 基于 BV 编码获取线路 ID
  - 匹配爬取数据和高德 API 数据

- `_process_amap()`: 处理高德地图数据
  - 解析线路几何坐标
  - 坐标系转换（GCJ-02 转 WGS-84）
  - 生成标准化的线路数据

- `get_output_data()`: 输出处理后的公交数据

**3. AmapSubway 类**

**功能概述**：从高德地图获取地铁数据

**构造函数**：
```python
def __init__(
    self,
    city_name_en_us: str,
    proj_str: str,
    amap_ak: str,
)
```

**核心方法**：

- `_fetch_raw_data()`: 从高德地图获取地铁网络数据
  - 获取城市地铁线路列表
  - 解析地铁线路的基本信息

- `_fetch_amap_lines()`: 获取地铁线路详细信息
  - 获取每条线路的站点信息和几何路径
  - 处理地铁线路的方向和分段
  - 生成偏移几何以区分上下行

- `_merge_stations()`: 合并相近的地铁站
  - 基于距离阈值合并同名站点
  - 处理换乘站的多个入口

- `get_output_data()`: 输出处理后的地铁数据

**4. 数据后处理功能**

**public_transport_process() 函数**

**功能概述**：对公共交通数据进行后处理和路网集成

**主要参数**：
```python
def public_transport_process(
    m: dict,
    server_address: str,
    taz_length: float = 1500,
    workers: int = cpu_count(),
    multiprocessing_chunk_size: int = 500,
)
```

**核心处理流程**：

- `_fill_public_lines()`: 填充公共交通线路信息
  - 使用路由服务计算站点间的道路连接
  - 验证公交线路在道路网络中的可达性
  - 计算线路的预计到达时间（ETA）

- `_post_compute()`: 后处理计算
  - 计算交通分析区（TAZ）成本
  - 生成多进程并行计算任务
  - 优化公共交通路径

**辅助工具函数**：

- `cut()`: 基于站点分割路线
  - 将连续的路线按站点分段
  - 支持双向线路的处理
  - 使用投影坐标系进行精确计算

- `merge_geo()`: 合并几何数据
  - 合并相近的坐标点
  - 简化路线几何以减少数据量

- `_output_data_filter()`: 输出数据过滤
  - 过滤不合理的线路段
  - 验证站点间距和路线长度
  - 清理无效的公共交通线路

- `gps_distance()`: GPS 距离计算
  - 计算地理坐标间的实际距离
  - 支持批量距离计算

**数据格式和标准**：

**输出数据结构**：
- `lines`: 公共交通线路列表
  - 线路类型（公交/地铁）
  - 子线路信息（方向、站点序列）
  - 几何路径和时刻表
- `stations`: 站点信息列表
  - 站点位置和名称
  - 关联的线路信息
  - 站点类型（公交站/地铁站）

**坐标系转换**：
- 支持 GCJ-02（高德坐标系）到 WGS-84 的转换
- 使用投影坐标系进行几何计算
- 自动处理不同数据源的坐标差异

**质量控制**：
- 最小路线长度限制：200 米
- 最大站点距离检查：50 米（Transitland），15 米（OSM）
- 站点合并距离阈值：地铁 800 米，公交 30 米
- 路线长度合理性验证

### GMNS

gmns 模块提供了将 mosstool 地图格式转换为 GMNS（General Modeling Network Specification）标准格式的功能。GMNS 是一个开源的交通网络数据规范，广泛用于交通建模和仿真应用。

#### Convertor 类

**功能概述**：将 mosstool 内部地图格式转换为符合 GMNS 标准的节点和链路数据

**构造函数**：
```python
def __init__(self, m: Map):
```

**参数说明**：
- `m (Map)`: mosstool 内部地图数据结构

**初始化处理**：
- 设置投影转换器，用于坐标系转换
- 建立道路、车道、AOI 的索引映射
- 转换车道几何为 Shapely LineString 对象
- 转换 AOI 几何为 Shapely Point 或 Polygon 对象
- 筛选车行道数据（排除人行道）
- 初始化道路连接关系检查数据结构

**核心转换方法**：

**1. `_to_nodes()` - 转换节点数据**

**功能**：将交叉口和 AOI 转换为 GMNS 节点格式

**处理流程**：
- **交叉口处理**：
  - 检查道路连通性，验证车道组的完整性
  - 识别不完美的交叉口（缺少某些转向的车道组）
  - 计算交叉口中心点坐标（基于所有车道的几何中心）
  - 生成交叉口节点数据

- **AOI 处理**：
  - 为每个 AOI 创建起点和终点节点（{id}-start 和 {id}-end）
  - 计算 AOI 几何中心作为节点坐标
  - 支持点状和面状 AOI

**输出格式**：
- `name`: 节点名称
- `node_id`: 节点 ID
- `zone_id`: 交通分析区 ID
- `x_coord`: 经度坐标
- `y_coord`: 纬度坐标  
- `geometry`: WKT 格式的几何描述

**质量检查**：
- 检测缺少车道组的交叉口并发出警告
- 确保所有进出道路对都有对应的车道连接

**2. `_to_lines()` - 转换链路数据**

**功能**：将道路和车道转换为 GMNS 链路格式

**处理流程**：
- **道路处理**：
  - 识别每条道路的车行道
  - 确定道路的起始和结束节点
  - 为没有前驱/后继的道路创建虚拟节点
  - 计算道路长度、车道数、限速等属性
  - 生成 WKT 格式的几何描述

- **AOI 连接处理**：
  - 为 AOI 起点创建到后继交叉口的连接
  - 为 AOI 终点创建从前驱交叉口的连接
  - 基于车道位置计算连接长度
  - 设置较低的速度限制以反映 AOI 内部道路特性

**单位转换**：
- 长度：米 → 英里（除以 1609.34）
- 速度：米/秒 → 英里/小时（乘以 3.6 再除以 1.60934）

**容量计算**：
- 道路容量 = 30 × min(速度, 70)（经验公式）
- AOI 连接容量 = 30 × 30（固定值）

**输出格式**：
- `name`: 链路名称
- `link_id`: 链路 ID
- `from_node_id`: 起始节点 ID
- `to_node_id`: 终止节点 ID
- `length`: 链路长度（英里）
- `lanes`: 车道数
- `free_speed`: 自由流速度（英里/小时）
- `geometry`: WKT 格式的几何描述
- `capacity`: 容量（车辆/小时）
- `link_type`: 链路类型（1: 单向，2: 双向）

**3. `save()` - 保存 GMNS 数据**

**功能**：将转换后的数据保存为 GMNS 标准的 CSV 文件

**参数**：
```python
def save(self, work_dir: str):
```

**处理流程**：
1. 调用 `_to_nodes()` 生成节点数据
2. 调用 `_to_lines()` 生成链路数据和虚拟节点数据
3. 合并节点数据和虚拟节点数据
4. 保存为标准 GMNS 文件：
   - `node.csv`: 节点文件
   - `link.csv`: 链路文件

**数据结构映射**：

**Mosstool → GMNS 映射关系**：
- `Junction` → `Node` (交叉口转为节点)
- `AOI` → `Node` (起点/终点节点)
- `Road` → `Link` (道路转为链路)
- `Lane` → `Link属性` (车道信息聚合到链路属性)

**坐标系处理**：
- 自动从投影坐标系转换为地理坐标系（经纬度）
- 使用 pyproj 进行精确的坐标变换
- 支持各种投影坐标系

**质量控制**：
- 验证交叉口的车道组完整性
- 检测并报告不完美的交叉口
- 确保所有链路都有有效的起止节点
- 为孤立道路自动创建虚拟节点

**应用场景**：
- 交通仿真软件集成（如 SUMO、VISSIM）
- 交通分配模型输入
- 路网分析和可视化
- 与其他交通工具的数据交换

**标准兼容性**：
- 完全符合 GMNS 数据规范
- 支持标准的 CSV 输出格式
- 包含必要的几何信息（WKT 格式）
- 提供完整的网络拓扑关系

### Vis

Vis 模块提供了地图可视化功能，能够将 mosstool 内部地图格式转换为适合可视化的 GeoJSON 格式，并支持基于 PyDeck 的交互式地图可视化。该模块主要用于地图数据的调试、验证和展示。

#### VisMap 类

**功能概述**：地图可视化的核心类，负责将地图数据预处理为可视化格式并提供多种可视化接口

**构造函数**：
```python
def __init__(self, m: Map):
```

**参数说明**：
- `m (Map)`: mosstool 内部地图数据结构

**初始化处理**：
- 设置投影转换器，用于坐标系转换
- 计算地图中心点坐标
- 预处理所有地图元素为 GeoJSON 格式和 Shapely 几何对象
- 建立快速访问的索引映射

**核心属性**：

**1. `feature_collection` 属性**

**功能**：获取包含所有地图元素的 GeoJSON FeatureCollection

**返回值**：
```python
@property
def feature_collection(self) -> geojson.FeatureCollection:
```

**处理流程**：
- 合并所有车道、道路、AOI 和 POI 特征
- 返回标准的 GeoJSON FeatureCollection 格式
- 可直接用于 Web 地图或 GIS 软件

**核心数据构建方法**：

**1. `_get_center()` - 计算地图中心**

**功能**：基于地图边界计算地理中心点

**处理流程**：
- 从地图 header 获取边界信息（west, east, south, north）
- 计算投影坐标的中心点
- 转换为地理坐标（经纬度）
- 用于设置可视化的初始视角

**2. `_build_lanes()` - 构建车道特征**

**功能**：将车道数据转换为 GeoJSON LineString 特征

**处理流程**：
- 提取车道中心线坐标（支持 2D 和 3D）
- 投影坐标转换为地理坐标
- 构建 Shapely LineString 对象用于空间计算
- 生成包含完整属性的 GeoJSON 特征
- 清理不必要的几何数据以减少存储空间

**输出数据结构**：
- Features: `Dict[int, dict]` - 以车道 ID 为键的 GeoJSON 特征
- Shapely XYs: `Dict[int, LineString]` - 用于空间计算的几何对象

**3. `_build_roads()` - 构建道路特征**

**功能**：将道路数据转换为代表性的 GeoJSON 特征

**处理流程**：
- 识别道路中的车行道和人行道
- 选择中心车道作为道路的代表几何
- 优先选择车行道，若无车行道则选择人行道
- 复制车道的几何信息，替换为道路属性
- 进行数据完整性验证

**智能选择算法**：
- 车行道优先：`driving_lane_ids if len(driving_lane_ids) > 0 else walking_lane_ids`
- 中心选择：`main_lane_ids[len(main_lane_ids) // 2]`

**4. `_build_aois()` - 构建 AOI 特征**

**功能**：将兴趣区域转换为 GeoJSON Point 或 Polygon 特征

**处理流程**：
- 根据位置点数量自动判断几何类型
- 单点 AOI → Point 几何
- 多点 AOI → Polygon 几何  
- 投影坐标转换为地理坐标
- 构建对应的 Shapely 几何对象

**几何类型判断**：
```python
if len(lnglats) == 1:
    # Point AOI
    shapely_xys[id] = Point(xys[0])
    geometry = {"type": "Point", "coordinates": lnglats[0]}
else:
    # Polygon AOI
    shapely_xys[id] = Polygon(xys)
    geometry = {"type": "Polygon", "coordinates": [lnglats]}
```

**5. `_build_pois()` - 构建 POI 特征**

**功能**：将兴趣点转换为 GeoJSON Point 特征

**处理流程**：
- 提取 POI 位置坐标
- 投影坐标转换为地理坐标
- 构建 Point 类型的 Shapely 几何对象
- 生成包含完整属性的 GeoJSON 特征

**坐标转换和查询方法**：

**1. `position2lnglat()` - 位置转换**

**功能**：将 mosstool Position 对象转换为地理坐标

**参数**：
```python
def position2lnglat(self, position: Position) -> Tuple[float, float]:
```

**支持位置类型**：
- **AOI Position**: 基于 AOI 几何中心计算
- **Lane Position**: 基于车道插值计算精确位置
- 使用 Shapely 的 `interpolate()` 方法进行车道位置插值

**错误处理**：
- 对未知位置类型抛出 ValueError 异常
- 确保位置转换的准确性和鲁棒性

**2. `id2lnglats()` - ID 到坐标序列转换**

**功能**：根据车道或道路 ID 获取完整的坐标序列

**参数**：
```python
def id2lnglats(self, lane_id_or_road_id: int) -> np.ndarray:
```

**处理流程**：
- 优先查找车道几何，然后查找道路几何
- 提取 LineString 的所有坐标点
- 批量进行投影坐标转换
- 返回 NumPy 数组格式的经纬度序列

**可视化方法**：

**1. `visualize()` - 交互式可视化**

**功能**：使用 PyDeck 创建交互式地图可视化

**可视化特性**：
- **分层显示**：车道、AOI、POI 分别使用不同颜色
- **交互式工具提示**：悬停显示详细属性信息
- **自适应视角**：基于地图中心自动设置初始视角
- **样式定制**：支持颜色、透明度、线宽等样式配置

**颜色方案**：
- 车行道：蓝色 (#29A2FF)
- 人行道：橙色 (#FFBE1A)  
- AOI：浅粉色 (#FFD4CE)
- POI：红色 (#F7624D)

**工具提示信息**：
- 车道：类型、转向、父道路 ID
- AOI：土地利用类型
- POI：名称、类别

**PyDeck 配置**：
```python
layer = pdk.Layer(
    "GeoJsonLayer",
    features,
    stroked=True,
    filled=True,
    pickable=True,
    line_cap_rounded=True,
    get_fill_color="properties.color",
    get_line_color="properties.color",
    get_line_width=1,
    line_width_min_pixels=1,
    tooltip=True,
)
```

**技术特性**：

**坐标系处理**：
- 自动处理投影坐标系到地理坐标系的转换
- 使用 pyproj 进行精确的坐标变换
- 支持 2D 和 3D 坐标数据

**内存优化**：
- 预计算并缓存所有几何对象
- 删除不必要的几何数据以减少内存占用
- 使用 deepcopy 确保数据安全性

**数据完整性**：
- 完整的错误检查和异常处理
- 验证车道-道路关系的一致性
- 确保所有地图元素都能正确转换

**应用场景**：
- 地图数据质量检查和验证
- 交互式地图浏览和分析
- 地图构建过程的调试
- 演示和展示用途
- GIS 数据集成和转换

**输出格式支持**：
- GeoJSON FeatureCollection（标准地理数据格式）
- PyDeck Deck 对象（Web 可视化）
- NumPy 数组（数值计算）
- Shapely 几何对象（空间分析）

## trip/

### Generator

Generator 模块提供了多种行程生成策略，用于创建不同类型的出行需求数据。该模块包含五个主要的生成器类，支持从简单的随机生成到复杂的基于OD矩阵的行程生成。

#### 1. RandomGenerator 类

**功能概述**：基于随机采样的行程生成器，支持在指定位置模式序列下生成随机行程

**构造函数**：
```python
def __init__(
    self,
    m: Map,
    position_modes: List[PositionMode],
    trip_mode: TripMode,
    template_func: Callable[[], Person] = default_person_template_generator,
):
```

**参数说明**：
- `m (Map)`: 地图数据
- `position_modes (List[PositionMode])`: 位置模式序列，定义行程的位置类型序列
- `trip_mode (TripMode)`: 目标出行方式
- `template_func`: 人员模板生成函数

**PositionMode 枚举**：
- `PositionMode.AOI`: AOI 位置模式
- `PositionMode.LANE`: 车道位置模式

**初始化处理**：
- 根据出行方式筛选候选 AOI 和车道
- 对步行出行选择人行道和步行位置
- 对驾车出行选择车行道和驾驶位置
- 验证候选集的可用性

**核心方法**：

**`uniform()` - 均匀随机生成**

**功能**：通过均匀随机采样生成人员对象

**参数**：
```python
def uniform(
    self,
    num: int,
    first_departure_time_range: Tuple[float, float],
    schedule_interval_range: Tuple[float, float],
    seed: Optional[int] = None,
    start_id: Optional[int] = None,
) -> List[Person]:
```

**处理流程**：
1. 根据位置模式序列的第一个模式设置家庭位置
2. 为每个后续位置模式生成对应的行程
3. 随机采样出发时间和行程间隔
4. 构建完整的人员对象和行程计划

**位置生成算法**：
```python
def _rand_position(self, candidates: Union[List[Aoi], List[Lane]]):
    # AOI位置：直接使用AOI中心
    # 车道位置：在车道长度范围内随机采样距离s
```

#### 2. GravityGenerator 类

**功能概述**：基于重力模型的OD矩阵生成器，用于生成符合重力模型的出行需求

**构造函数**：
```python
def __init__(
    self,
    Lambda: float,
    Alpha: float,
    Beta: float,
    Gamma: float,
):
```

**重力模型参数**：
- `Lambda`: 模型比例系数
- `Alpha`: 起点吸引力指数  
- `Beta`: 终点吸引力指数
- `Gamma`: 距离阻抗指数

**核心方法**：

**`load_area()` - 加载区域数据**

**功能**：加载包含几何信息的区域数据

**参数**：
```python
def load_area(self, area: gpd.GeoDataFrame):
```

**`cal_distance()` - 计算距离矩阵**

**功能**：基于区域几何计算欧几里得距离矩阵

**处理流程**：
1. 获取第一个几何对象确定坐标系
2. 自动计算适合的 UTM 投影坐标系 EPSG 代码
3. 转换到 UTM 坐标系进行精确距离计算
4. 计算区域质心间的距离矩阵

**UTM坐标系自动选择**：
```python
def _calculate_utm_epsg(self, longitude: float, latitude: float):
    utm_zone = int((longitude + 180) / 6) + 1
    epsg_code = 32600 + utm_zone if latitude >= 0 else 32700 + utm_zone
```

**`generate()` - 生成OD矩阵**

**功能**：基于重力模型公式生成OD矩阵

**重力模型公式**：
```
OD[i,j] = λ * (N[i]^α) * (M[j]^β) / (D[i,j]^γ)
```

其中：
- N[i]: 起点i的人口规模
- M[j]: 终点j的人口规模  
- D[i,j]: 起点i到终点j的距离

#### 3. AigcGenerator 类

**功能概述**：基于AI生成的OD矩阵生成器，集成外部AI服务进行智能出行需求生成

**构造函数**：
```python
def __init__(self):
```

**核心方法**：

**`set_satetoken()` - 设置访问令牌**

**功能**：设置访问外部AI服务的认证令牌

**`load_area()` - 加载区域数据**

**功能**：加载区域几何数据供AI服务分析

**`generate()` - 生成OD矩阵**

**功能**：调用外部AI服务生成智能化的OD矩阵

#### 4. 模板生成器系列

**功能概述**：提供多种人员属性模板生成策略，用于创建具有不同行为特征的个体

**4.1 ProbabilisticTemplateGenerator 类**

**功能**：基于概率分布的人员属性生成

**支持的属性**：
- `max_speed`: 最大速度
- `max_acceleration`: 最大加速度
- `max_braking_acceleration`: 最大制动加速度
- `usual_braking_acceleration`: 常用制动加速度
- `headway`: 安全车头时距
- `min_gap`: 最小间距

**构造函数**：
```python
def __init__(
    self,
    max_speed_values: Optional[list[float]] = None,
    max_speed_probabilities: Optional[list[float]] = None,
    # ... 其他属性的值和概率列表
    seed: int = 0,
    template: Optional[Person] = None,
):
```

**4.2 GaussianTemplateGenerator 类**

**功能**：基于高斯分布的人员属性生成

**构造函数**：
```python
def __init__(
    self,
    max_speed_mean: Optional[float] = None,
    max_speed_std: Optional[float] = None,
    # ... 其他属性的均值和标准差
    seed: int = 0,
    template: Optional[Person] = None,
):
```

**4.3 UniformTemplateGenerator 类**

**功能**：基于均匀分布的人员属性生成

**构造函数**：
```python
def __init__(
    self,
    max_speed_min: Optional[float] = None,
    max_speed_max: Optional[float] = None,
    # ... 其他属性的最小值和最大值
    seed: int = 0,
    template: Optional[Person] = None,
):
```

**4.4 CalibratedTemplateGenerator 类**

**功能**：基于标定数据的人员属性生成，使用预设的概率分布

**特性**：
- 使用经过实际数据标定的参数分布
- 包含制动加速度、车头时距、最大加速度等关键参数
- 提供更真实的驾驶行为模拟

**默认模板函数**：

**`default_person_template_generator()` - 默认个人模板**

**生成属性**：
- 车辆属性：长度5m，宽度2m，最大速度150km/h
- 排放属性：重量2100kg，燃油车型，阻力系数0.251
- 行人属性：速度1.34m/s
- 自行车属性：速度5m/s

**`default_bus_template_generator()` - 默认公交模板**

**生成属性**：
- 车辆属性：长度15m，宽度2m，最大速度150km/h
- 排放属性：重量18000kg，燃油车型，阻力系数0.251
- 较大的正面面积和不同的燃油效率参数

#### 5. TripGenerator 类

**功能概述**：最复杂的行程生成器，基于OD矩阵、人口数据和活动分布生成详细的个人行程

**构造函数**：
```python
def __init__(
    self,
    m: Map,
    pop_tif_path: Optional[str] = None,
    activity_distributions: Optional[dict] = None,
    driving_speed: float = 30 / 3.6,
    parking_fee: float = 20.0,
    # ... 大量交通参数
    template_func: Callable[[], Person] = default_person_template_generator,
    add_pop: bool = False,
    multiprocessing_chunk_size: int = 500,
    workers: int = cpu_count(),
):
```

**核心功能模块**：

**数据预处理**：
- `_read_aois()`: 读取和分类AOI数据
- `_read_regions()`: 读取区域边界数据  
- `_read_od_matrix()`: 读取OD矩阵数据
- `_match_aoi2region()`: 匹配AOI到区域的空间关系

**出行方式选择模型**：

**`_get_mode_with_distribution()` - 基于效用的出行方式选择**

**效用函数**：
- 公交：V_bus = -0.0516 × 时间 - 0.4810 × 费用
- 地铁：V_subway = -0.0512 × 时间 - 0.0833 × 费用  
- 燃油车：V_fuel = -0.0705 × 时间 + 0.5680 × 年龄 - 0.8233 × 收入 - 0.0941 × 停车费
- 电动车：V_elec = -0.0339 × 时间 - 0.1735 × 停车费
- 自行车：V_bicycle = -0.1185 × 时间（距离≤15km）

**Logit选择模型**：选择概率 = exp(V_i) / Σexp(V_j)

**核心生成方法**：

**`generate_persons()` - 生成个人行程**

**功能**：基于OD矩阵和区域数据生成完整的个人行程数据

**参数**：
```python
def generate_persons(
    self,
    od_matrix: np.ndarray,
    areas: GeoDataFrame,
    available_trip_modes: list[str] = ["drive", "walk", "bus", "subway", "taxi"],
    departure_time_curve: Optional[list[float]] = None,
    area_pops: Optional[list] = None,
    person_profiles: Optional[list[dict]] = None,
    seed: int = 0,
    agent_num: Optional[int] = None,
) -> list[Person]:
```

**处理流程**：
1. 基于OD矩阵分配个体到起止区域
2. 生成个体的人口统计特征
3. 根据活动模式分配活动序列
4. 为每个活动分配具体的AOI位置
5. 计算出行时间和选择出行方式
6. 生成完整的行程计划

**`fill_person_schedules()` - 填充个人行程计划**

**功能**：为已有个人对象填充详细的行程计划

**`generate_public_transport_drivers()` - 生成公交司机**

**功能**：生成公交和地铁线路的司机行程

**`generate_taxi_drivers()` - 生成出租车司机**

**功能**：生成出租车司机的待客和载客行程

**高级特性**：

**多进程处理**：
- 支持大规模个体生成的并行处理
- 可配置的分块大小和工作进程数
- 内存优化的数据处理流程

**活动模式识别**：
- 支持H（家庭）、W（工作）、E（教育）、O（其他）活动类型
- 基于人口统计特征的活动模式分配
- 动态的出发时间生成

**空间匹配算法**：
- AOI到区域的高效空间匹配
- 基于人口密度的位置选择
- 多类型几何体的处理支持

**应用场景**：
- 大规模交通仿真的需求生成
- 城市交通规划的情景分析
- 交通政策影响评估
- 新区开发的交通需求预测

**输出数据格式**：
- 标准的 Person 对象列表
- 包含完整的个人属性、车辆属性、行程计划
- 支持多种出行方式的混合使用
- 时空精确的位置和时间信息

### SUMO

SUMO 模块提供了将 SUMO 路径文件转换为 mosstool 标准行程格式的功能。该模块能够解析 SUMO 的 .route.xml 文件，并将其中的车辆、路径、流量和行程信息转换为统一的 Person 对象格式。

#### RouteConverter 类

**功能概述**：SUMO 路径转换器的核心类，负责将 SUMO 格式的路径数据转换为 mosstool 标准格式

**构造函数**：
```python
def __init__(
    self,
    converted_map: Map,
    sumo_id_mappings: dict,
    route_path: str,
    additional_path: Optional[str] = None,
    seed: Optional[int] = 0,
):
```

**参数说明**：
- `converted_map (Map)`: 从 SUMO 网络转换得到的地图数据
- `sumo_id_mappings (dict)`: SUMO ID 到统一 ID 的映射关系
- `route_path (str)`: SUMO 路径文件(.route.xml)的路径
- `additional_path (Optional[str])`: 包含公交站、充电站、停车场的附加文件路径
- `seed (Optional[int])`: 随机种子

**初始化处理**：

**地图数据索引构建**：
- 构建车道字典：包含类型、几何、前驱后继、父道路、长度等信息
- 构建交叉口字典：包含车道ID列表
- 构建道路字典：区分车行道和人行道，计算道路长度

**SUMO文件解析**：
- 解析车辆类型 (`vType`): 提取加速度、减速度、长度、最大速度、宽度、最小间距等属性
- 解析路径 (`route`): 道路边序列定义
- 解析行程 (`trip`): 起止点定义的行程
- 解析流量 (`flow`): 批量车辆生成定义
- 解析时间间隔 (`interval`): 包含多个流量的时间段
- 解析车辆 (`vehicle`): 单个车辆定义

**附加设施处理**：
- 公交站 (`busStop`): 解析位置、起止位置、名称
- 充电站 (`chargingStation`): 电动车充电设施
- 停车场 (`parkingArea`): 停车设施
- 位置验证和坐标转换

**核心转换方法**：

**1. `convert_route()` - 主转换接口**

**功能**：执行完整的 SUMO 路径到 mosstool 格式的转换

**转换流程**：
1. **初始化默认属性**：设置默认的个体、车辆、行人、自行车属性
2. **处理 trips**：转换单个行程定义
3. **处理 flows**：转换流量定义和时间间隔流量
4. **处理 vehicles**：转换具体车辆定义
5. **生成 Person 对象**：输出标准格式的个体数据

**2. 时间转换方法**

**`_convert_time()` - 时间格式转换**

**功能**：将 SUMO 时间字符串转换为数值格式

**支持格式**：
- 秒数格式："3600.0" → 3600.0
- 时分秒格式："01:00:00" → 3600.0
- 自动处理浮点数和整数

**3. 路径转换方法**

**`_convert_route_trips()` - 路径行程转换**

**功能**：将 SUMO 边序列转换为行程序列

**参数**：
```python
def _convert_route_trips(
    self, 
    edges: list, 
    repeat: int, 
    cycle_time: np.float64, 
    rid2stop: dict
):
```

**处理逻辑**：
- 验证边的有效性并转换为道路ID
- 处理重复循环 (`repeat`) 和循环时间 (`cycle_time`)
- 集成停靠点信息
- 生成完整的路径序列

**4. 个体类型处理**

**`_process_agent_type()` - 个体类型识别**

**功能**：根据车辆类型确定出行方式和速度参数

**类型映射**：
- `AGENT_TYPE_PERSON` → 步行模式，速度1.34m/s
- `AGENT_TYPE_PRIVATE_CAR` → 驾车模式，使用车辆最大速度
- `AGENT_TYPE_BUS` → 公交模式，使用车辆最大速度
- `AGENT_TYPE_BIKE` → 自行车模式，速度5.0m/s

**车道类型选择**：
- 车辆类型 → `driving_lane_ids` (车行道)
- 行人类型 → `walking_lane_ids` (人行道)

**5. 位置转换方法**

**`_get_trip_position()` - 行程位置获取**

**功能**：根据 SUMO 定义获取精确的车道位置

**参数**：
```python
def _get_trip_position(
    self,
    t: minidom.Element,
    trip_id: int,
    road: dict,
    road_id: int,
    ROAD_LANE_TYPE: Union[Literal["walking_lane_ids"], Literal["driving_lane_ids"]],
    trip_type: Union[Literal["trip"], Literal["flow"], Literal["vehicle"]],
    attribute: Union[Literal["departLane"], Literal["arrivalLane"]],
):
```

**位置计算逻辑**：
- 支持指定车道索引或随机选择
- 支持指定位置或随机位置（0.1-0.9范围）
- 自动处理负数位置（从道路末端计算）
- 位置范围限制确保安全性

**6. 停靠点转换**

**`_convert_stops()` - 停靠点转换**

**功能**：转换 SUMO 停靠点为标准格式

**支持属性**：
- 停靠时间 (`duration`)
- 到达时间 (`arrival`)
- 停靠位置 (`startPos`, `endPos`)
- 停靠设施ID引用

**7. 流量生成算法**

**Flow 类型支持**：

**按数量生成** (`number` 属性)：
```python
departure_times = np.linspace(begin, end, number)
```

**按周期生成** (`period` 属性)：
```python
number = int((end - begin) / period)
departure_times = np.linspace(begin, end, number)
```

**按小时流量生成** (`vehsPerHour` 属性)：
```python
number = int(vehs_per_hour * (end_time - begin_time) / 3600)
departure_times = np.linspace(begin, end, number)
```

**按概率生成** (`probability` 属性)：
```python
for i in range(int(end - begin) + 1):
    if random.random() < prob:
        departure_times.append(i + begin)
```

**8. 复杂行程处理**

**`_convert_trips_with_route()` - 带路径的行程转换**

**功能**：处理包含完整路径定义的行程

**`_convert_flows_with_from_to()` - 起止点流量转换**

**功能**：处理仅定义起止点的流量，自动生成中间路径

**`_route_trips_to_person()` - 路径到个体转换**

**功能**：将路径序列转换为完整的 Person 对象

**转换特性**：

**车辆属性转换**：
- **默认属性**：长度5m，宽度2m，最大速度150km/h
- **SUMO属性映射**：加速度、减速度、车头时距、最小间距等
- **车辆类型识别**：私家车、公交车、自行车、行人

**时空精度**：
- **精确时间计算**：基于距离和速度的ETA估算
- **精确位置定位**：车道级别的位置定义
- **路径验证**：确保路径的连通性和有效性

**数据完整性**：
- **错误处理**：无效路径、缺失数据的处理
- **数据验证**：车道存在性、位置合理性检查
- **日志记录**：详细的转换过程日志

**高级功能**：

**循环路径支持**：
- 支持 `repeat` 属性的重复路径
- 支持 `cycleTime` 的循环时间控制
- 自动计算循环间隔和总时长

**多模式出行**：
- 支持步行、驾车、公交、自行车等多种出行方式
- 根据车辆类型自动选择合适的基础设施
- 保持出行方式的一致性

**批量处理**：
- 高效的XML解析和数据提取
- 内存优化的大规模数据处理
- 并行化潜力（通过数据分块）

**输出格式**：

**Person 对象结构**：
```python
{
    "id": agent_uid,
    "home": trip_home,
    "attribute": agent_attribute,
    "vehicle_attribute": vehicle_attribute,
    "pedestrian_attribute": pedestrian_attribute,
    "bike_attribute": bike_attribute,
    "schedules": schedules,
}
```

**应用场景**：
- SUMO 仿真结果的后处理分析
- 跨平台仿真数据迁移
- 交通流模式的标准化转换
- 多尺度交通模型集成

### Route

Route 模块提供了路径规划和导航服务的客户端功能，支持通过 gRPC 协议与路径规划服务进行通信，并为行程数据预填充详细的路径信息。该模块包含路径服务客户端和预路径规划功能。

#### 1. RoutingClient 类

**功能概述**：路径规划服务的客户端接口，提供与远程路径规划服务的异步通信能力

**构造函数**：
```python
def __init__(self, server_address: str, secure: bool = False):
```

**参数说明**：
- `server_address (str)`: 路径规划服务器地址
- `secure (bool)`: 是否使用安全连接，默认为 False

**连接管理**：

**`_create_aio_channel()` - 创建异步通道**

**功能**：创建 gRPC 异步通信通道

**参数**：
```python
def _create_aio_channel(server_address: str, secure: bool = False) -> grpc.aio.Channel:
```

**地址处理逻辑**：
- **HTTP协议处理**：自动移除 "http://" 前缀，确保不使用安全连接
- **HTTPS协议处理**：自动移除 "https://" 前缀，自动启用安全连接
- **安全性验证**：检查协议与安全设置的一致性

**连接类型**：
- **安全连接**：使用 SSL/TLS 加密的 gRPC 连接
- **非安全连接**：明文 gRPC 连接，适用于内网环境

**核心方法**：

**`GetRoute()` - 异步路径规划请求**

**功能**：向路径规划服务发送导航请求并获取结果

**参数**：
```python
async def GetRoute(
    self,
    req: GetRouteRequest,
) -> GetRouteResponse:
```

**请求格式**：
- 遵循 CityProto 规范的 GetRouteRequest 格式
- 包含起点、终点、出行方式、出发时间等信息
- 支持多种路径类型和约束条件

**响应格式**：
- 返回 GetRouteResponse 对象
- 包含完整的路径序列和行程信息
- 提供时间、距离、代价等路径属性

#### 2. pre_route 函数

**功能概述**：为 Person 对象的所有行程预填充详细的路径信息，移除无法规划路径的行程

**函数签名**：
```python
async def pre_route(
    client: RoutingClient,
    person: Person,
    filter_walking_pt_persons: bool = False,
    in_place: bool = False,
) -> Person:
```

**参数说明**：
- `client (RoutingClient)`: 路径规划服务客户端
- `person (Person)`: 需要进行路径规划的个人对象
- `filter_walking_pt_persons (bool)`: 过滤公交地铁模式但仅返回步行路径的个体
- `in_place (bool)`: 是否原地修改 Person 对象

**出行方式映射**：

**`_TYPE_MAP` - 出行方式转换映射**

```python
_TYPE_MAP = {
    TripMode.TRIP_MODE_DRIVE_ONLY: RouteType.ROUTE_TYPE_DRIVING,
    TripMode.TRIP_MODE_TAXI: RouteType.ROUTE_TYPE_TAXI,
    TripMode.TRIP_MODE_BIKE_WALK: RouteType.ROUTE_TYPE_WALKING,
    TripMode.TRIP_MODE_BUS_WALK: RouteType.ROUTE_TYPE_BUS,
    TripMode.TRIP_MODE_SUBWAY_WALK: RouteType.ROUTE_TYPE_SUBWAY,
    TripMode.TRIP_MODE_BUS_SUBWAY_WALK: RouteType.ROUTE_TYPE_BUS_SUBWAY,
    TripMode.TRIP_MODE_WALK_ONLY: RouteType.ROUTE_TYPE_WALKING,
}
```

**核心处理流程**：

**1. 初始化和数据准备**
- 根据 `in_place` 参数决定是否创建 Person 对象副本
- 设置起始位置为个体的家庭位置
- 清空原有行程计划，准备重新填充

**2. 行程计划遍历**
- 逐个处理每个 Schedule 对象
- 提取出发时间信息
- 验证行程的可行性

**3. 循环行程处理**
```python
if schedule.loop_count != 1:
    # 非一次性行程，出发时间不准确，跳过预计算
    logging.warning("Schedule is not a one-time trip...")
    continue
```

**4. 单个行程处理**

**出发时间管理**：
- 支持行程级别和 Trip 级别的出发时间设置
- 自动处理出发时间的继承和覆盖
- 对无明确出发时间的行程进行特殊处理

**路径请求构建**：
```python
res = await client.GetRoute(
    GetRouteRequest(
        type=_TYPE_MAP[trip.mode],
        start=start,
        end=trip.end,
        time=departure_time,
    )
)
```

**5. 路径结果处理**

**无效路径处理**：
- 记录无法找到路径的行程
- 恢复之前的出发时间状态
- 移除无效行程

**公交步行过滤**：
```python
if (
    filter_walking_pt_persons
    and trip.mode in {TRIP_MODE_BUS_WALK, TRIP_MODE_SUBWAY_WALK, TRIP_MODE_BUS_SUBWAY_WALK}
    and len(res.journeys) == 1
    and res.journeys[0].type == JourneyType.JOURNEY_TYPE_WALKING
):
    # 过滤公交地铁模式但仅返回步行的行程
    departure_time = last_departure_time
```

**有效路径处理**：
- 清空原有路径信息
- 合并新的路径信息 (`trip.routes.MergeFrom(res.journeys)`)
- 更新起始位置为当前行程的终点
- 重置出发时间状态

**6. 行程计划重构**
- 只保留包含有效行程的 Schedule
- 重新构建 Person 对象的行程计划
- 确保数据的完整性和一致性

**高级功能特性**：

**异步处理**：
- 使用 `async/await` 模式进行异步路径规划
- 支持并发处理多个路径请求
- 提高大规模数据处理的效率

**错误处理和日志**：
- 详细的错误日志记录
- 优雅的异常处理机制
- 便于调试和问题定位

**数据完整性保证**：
- 自动移除无法规划路径的行程
- 保持数据的逻辑一致性
- 防止无效数据的传播

**智能过滤机制**：
- 支持公交地铁行程的智能过滤
- 避免虚假的公交需求（实际只能步行）
- 提高交通分析的准确性

**内存管理**：
- 支持原地修改和副本操作
- 灵活的内存使用策略
- 适应不同的应用场景

**技术规范**：

**通信协议**：
- 基于 gRPC 的高性能 RPC 通信
- 支持 HTTP/2 多路复用
- 自动处理连接管理和重试

**数据格式**：
- 遵循 CityProto 数据规范
- 跨平台的数据交换格式
- 向前兼容的版本控制

**安全性**：
- 支持 SSL/TLS 加密通信
- 灵活的认证机制
- 适应企业级安全要求

**应用场景**：

**行程预处理**：
- 大规模行程数据的预路径规划
- 交通仿真前的数据准备
- 行程可行性验证

**数据质量控制**：
- 移除无效和不可达的行程
- 提高仿真数据的质量
- 减少仿真过程中的错误

**多模式出行支持**：
- 支持步行、驾车、公交、地铁等多种出行方式
- 智能的出行方式选择和组合
- 符合实际出行行为的路径规划

**性能优化**：
- 异步并发处理提高效率
- 智能缓存和批量处理
- 适应大规模城市交通数据

**集成能力**：
- 与多种路径规划服务兼容
- 支持云端和本地部署
- 灵活的服务发现和负载均衡

### STA

STA (Static Traffic Assignment) 模块提供了基于 GMNS 格式的静态交通分配功能。该模块能够将地图和个体行程数据转换为 GMNS 标准格式，利用 path4gmns 库进行静态交通分配计算，并将结果反馈到原始的行程数据中。

#### STA 类

**功能概述**：在 GMNS 地图上对个体行程进行静态交通分配的核心类，支持时间分片处理和路径结果回填

**构造函数**：
```python
def __init__(self, map: Map, work_dir: str):
```

**参数说明**：
- `map (Map)`: mosstool 内部地图数据结构
- `work_dir (str)`: 工作目录，用于存储中间文件和结果

**初始化处理**：
- 创建地图转换器 (`MapConvertor`) 实例
- 设置工作目录用于 GMNS 文件的读写

**核心方法**：

#### 1. `run()` - 主要执行接口

**功能**：对个体行程数据执行静态交通分配

**参数**：
```python
def run(
    self,
    persons: Persons,
    time_interval: int = 60,
    reset_routes: bool = False,
    column_gen_num: int = 10,
    column_update_num: int = 10,
):
```

**参数说明**：
- `persons (Persons)`: 包含行程信息的个体数据
- `time_interval (int)`: 时间分片间隔（分钟），建议设置大于行程的出行时间
- `reset_routes (bool)`: 是否重置个体的现有路径
- `column_gen_num (int)`: 列生成算法的迭代次数
- `column_update_num (int)`: 列更新算法的迭代次数

**返回值**：
- `Persons`: 包含路径结果的个体数据
- `dict`: 静态交通分配的统计信息

**核心处理流程**：

**步骤 1：地图转换**
```python
self._map_convertor.save(self._work_dir)
```
- 将 mosstool 地图格式转换为 GMNS 标准格式
- 生成 node.csv 和 link.csv 文件

**步骤 2：行程数据提取**
```python
from_trips = []  # (pi, si, ti, departure_time, start, end)
```

**行程筛选条件**：
- 具有确定出发时间的行程
- 驾车出行模式 (`TRIP_MODE_DRIVE_ONLY`)
- 一次性行程 (`loop_count == 1`)
- 没有现有路径或需要重置路径

**数据结构**：每个行程记录包含：
- `pi`: 个体索引
- `si`: 行程计划索引  
- `ti`: 单次行程索引
- `departure_time`: 出发时间
- `start, end`: 起止位置

**步骤 3：时间分片处理**

**分片策略**：
```python
start_t = from_trips[from_trips_i][3]
end_t = start_t + time_interval * 60
```

**需求聚合**：
```python
demands = defaultdict(int)  # (origin, destination) -> count
```

**OD矩阵生成**：
```python
od_df = pd.DataFrame([
    {
        "o_zone_id": o,
        "d_zone_id": d,
        "volume": volume,
    }
    for (o, d), volume in demands.items()
])
```

**步骤 4：静态交通分配**

**网络读取**：
```python
network = pg.read_network(
    input_dir=self._work_dir, length_unit="km", speed_unit="kph"
)
```

**需求加载**：
```python
pg.load_demand(network, input_dir=self._work_dir, demand_period_str="AM")
```

**列生成算法**：
```python
pg.perform_column_generation(column_gen_num, column_update_num, network)
```

**结果输出**：
```python
pg.output_columns(network, output_geometry=False, output_dir=self._work_dir)
```

**步骤 5：路径结果处理**

**结果读取**：
```python
agent_df = pd.read_csv(os.path.join(self._work_dir, "agent.csv"))
```

**路径解析和验证**：
```python
link_sequence = row["link_sequence"].split(";")
start_with_aoi = link_sequence[0].find("start") != -1
end_with_aoi = link_sequence[-1].find("end") != -1
```

**路径回填**：
```python
t.routes.append(
    Journey(
        type=JourneyType.JOURNEY_TYPE_DRIVING,
        driving=DrivingJourneyBody(road_ids=road_ids),
    )
)
```

#### 2. `_get_od()` - 起止点获取

**功能**：将位置对象转换为 GMNS 节点 ID

**参数**：
```python
def _get_od(self, start: Position, end: Position):
```

**位置类型处理**：

**AOI 位置**：
- 起点：`{aoi_id}-start`
- 终点：`{aoi_id}-end`

**车道位置**：
- 起点：选择道路的后继节点作为起点
- 终点：选择道路的前驱节点作为终点

**实现逻辑**：
```python
if start.HasField("aoi_position"):
    oid = f"{start.aoi_position.aoi_id}-start"
elif start.HasField("lane_position"):
    lane = self._map_convertor._lanes[start.lane_position.lane_id]
    _, oid = self._map_convertor._road2nodes[lane.parent_id]
```

#### 3. `_check_connection()` - 连通性检查

**功能**：检查两个道路段是否相连

**参数**：
```python
def _check_connection(self, start_road_id: int, end_road_id: int):
```

**实现**：
```python
return (start_road_id, end_road_id) in self._map_convertor._connected_road_pairs
```

**用途**：
- 验证静态交通分配结果的路径有效性
- 过滤无效的断开路径
- 确保路径的拓扑一致性

**高级功能特性**：

#### 时间分片管理

**智能分片**：
- 按时间顺序处理行程
- 避免时间跨度过大的分配问题
- 平衡计算效率和精度

**分片大小建议**：
- 设置为大于典型行程时间
- 避免行程跨越多个时间片
- 考虑网络容量和计算资源

#### 路径质量控制

**多层次验证**：
1. **AOI 连接验证**：确保 AOI 与道路网络的正确连接
2. **道路连通性验证**：检查相邻道路的拓扑关系
3. **路径完整性验证**：确保起止点的正确连接

**错误处理**：
```python
if bad:
    disjointed_cnt += volume
    continue
```

#### 统计信息收集

**返回统计**：
```python
{
    "trip_cnt": len(from_trips),           # 总行程数
    "total_volumes": total_volumes,        # 总交通量
    "valid_volumes": valid_volumes,        # 有效交通量
    "successful_cnt": success_cnt,         # 成功分配数
    "disjointed_cnt": disjointed_cnt,      # 断开路径数
}
```

**性能指标**：
- **成功率**：`successful_cnt / trip_cnt`
- **有效率**：`valid_volumes / total_volumes`
- **连通性**：`1 - disjointed_cnt / total_volumes`

#### 算法特性

**列生成算法**：
- 基于 path4gmns 的高效实现
- 支持大规模网络的路径搜索
- 动态列生成和更新机制

**静态分配模型**：
- 用户均衡原理 (User Equilibrium)
- 考虑路段容量约束
- 流量-延误关系建模

**路径选择**：
- 基于广义出行成本
- 考虑时间和距离因素
- 支持多路径分配

#### 技术限制和注意事项

**实验性功能**：
- 目前仅支持确定出发时间的行程
- 其他情况的行程会被跳过
- 建议在生产环境前进行充分测试

**数据要求**：
- 行程必须是一次性执行 (`loop_count == 1`)
- 仅处理驾车出行模式
- 需要明确的起止位置定义

**性能考虑**：
- 时间分片大小影响计算效率
- 大型网络可能需要更多计算资源
- 建议根据实际情况调整参数

#### 应用场景

**交通规划**：
- 道路网络容量分析
- 交通流分布预测
- 基础设施需求评估

**政策评估**：
- 交通管理措施影响分析
- 新建道路的流量预测
- 收费政策的交通影响

**仿真验证**：
- 动态仿真的初始状态设定
- 路径选择行为的验证
- 交通分配模型的标定

**数据质量控制**：
- 行程数据的合理性检验
- 网络连通性验证
- 出行需求的空间分布分析

## type/

type 模块提供了 mosstool 中常用的 Protobuf 类型定义和类型别名。该模块作为 pycityproto 库的封装层，为开发者提供了统一的类型导入接口，简化了类型引用并确保了版本一致性。

### 功能概述

**类型整合**：将分散在不同 pycityproto 模块中的常用类型集中导出

**版本管理**：提供统一的版本控制和兼容性检查入口

**开发便利**：简化类型导入，提高开发效率

### 核心类型分类

#### 1. 地图相关类型

**Map 类型组**：
```python
from pycityproto.city.map.v2.map_pb2 import (
    Map,        # 完整地图数据结构
    Lane,       # 车道对象
    Aoi,        # 兴趣区域对象
)
```

**功能说明**：
- **Map**: 完整的地图数据结构，包含道路、交叉口、AOI、POI 等所有地图元素
- **Lane**: 车道级别的详细信息，包含几何、属性、连接关系等
- **Aoi**: 兴趣区域定义，支持住宅、商业、工业等不同用途

**枚举类型**：
```python
from pycityproto.city.map.v2.map_pb2 import (
    AoiType,    # AOI 类型枚举
    LaneType,   # 车道类型枚举  
    LaneTurn,   # 车道转向枚举
)
```

**枚举值说明**：
- **AoiType**: `RESIDENTIAL`, `COMMERCIAL`, `INDUSTRIAL`, `EDUCATION` 等
- **LaneType**: `LANE_TYPE_DRIVING`, `LANE_TYPE_WALKING` 等
- **LaneTurn**: `LANE_TURN_LEFT`, `LANE_TURN_STRAIGHT`, `LANE_TURN_RIGHT` 等

#### 2. 地理位置类型

**Position 类型组**：
```python
from pycityproto.city.geo.v2.geo_pb2 import (
    Position,           # 通用位置对象
    AoiPosition,        # AOI 位置
    LanePosition,       # 车道位置
    LongLatPosition,    # 经纬度位置
)
```

**功能说明**：
- **Position**: 统一的位置表示，支持多种位置类型的 Union
- **AoiPosition**: AOI 内的位置，通过 AOI ID 指定
- **LanePosition**: 车道上的精确位置，包含车道 ID 和距离参数 s
- **LongLatPosition**: 地理坐标位置，使用经纬度表示

**使用模式**：
```python
# AOI 位置
position = Position(aoi_position=AoiPosition(aoi_id=123))

# 车道位置  
position = Position(lane_position=LanePosition(lane_id=456, s=100.0))

# 经纬度位置
position = Position(longlat_position=LongLatPosition(lng=116.4, lat=39.9))
```

#### 3. 个体和人口类型

**Person 类型组**：
```python
from pycityproto.city.person.v2.person_pb2 import (
    Person,         # 个体对象
    Persons,        # 个体集合
    PersonProfile,  # 个体档案
)
```

**功能说明**：
- **Person**: 完整的个体定义，包含属性、行程计划、车辆属性等
- **Persons**: 个体集合的容器类，用于批量处理
- **PersonProfile**: 个体的人口统计特征和社会经济属性

**枚举和属性类型**：
```python
from pycityproto.city.person.v2.person_pb2 import (
    PersonType,     # 个体类型枚举
    Gender,         # 性别枚举
    Education,      # 教育水平枚举
    Consumption,    # 消费水平枚举
)
```

**个体属性分类**：
- **PersonType**: `PERSON_TYPE_NORMAL`, `PERSON_TYPE_SPECIAL` 等
- **Gender**: `GENDER_MALE`, `GENDER_FEMALE`, `GENDER_OTHER`
- **Education**: `EDUCATION_PRIMARY`, `EDUCATION_SECONDARY`, `EDUCATION_TERTIARY`
- **Consumption**: `CONSUMPTION_LOW`, `CONSUMPTION_MEDIUM`, `CONSUMPTION_HIGH`

#### 4. 行程和出行类型

**Trip 类型组**：
```python
from pycityproto.city.trip.v2.trip_pb2 import (
    Schedule,   # 行程计划
    Trip,       # 单次行程
    TripMode,   # 出行方式枚举
)
```

**功能说明**：
- **Schedule**: 个体的日程安排，包含多个 Trip 和时间信息
- **Trip**: 单次出行的详细定义，包含起止点、方式、路径等
- **TripMode**: 出行方式的枚举定义

**出行方式类型**：
```python
TripMode.TRIP_MODE_WALK_ONLY        # 仅步行
TripMode.TRIP_MODE_BIKE_WALK        # 自行车+步行  
TripMode.TRIP_MODE_DRIVE_ONLY       # 仅驾车
TripMode.TRIP_MODE_BUS_WALK         # 公交+步行
TripMode.TRIP_MODE_SUBWAY_WALK      # 地铁+步行
TripMode.TRIP_MODE_BUS_SUBWAY_WALK  # 公交+地铁+步行
TripMode.TRIP_MODE_TAXI             # 出租车
```

#### 5. 路径规划类型

**Routing 类型组**：
```python
from pycityproto.city.routing.v2.routing_pb2 import (
    Journey,            # 路径段
    JourneyType,        # 路径类型枚举
    DrivingJourneyBody, # 驾车路径体
)
```

**功能说明**：
- **Journey**: 路径的基本单元，表示一段连续的出行
- **JourneyType**: 路径类型，如驾车、步行、公交等
- **DrivingJourneyBody**: 驾车路径的具体内容，包含道路序列

**路径类型**：
```python
JourneyType.JOURNEY_TYPE_WALKING    # 步行路径
JourneyType.JOURNEY_TYPE_DRIVING    # 驾车路径
JourneyType.JOURNEY_TYPE_BUS        # 公交路径
JourneyType.JOURNEY_TYPE_SUBWAY     # 地铁路径
```

**服务接口类型**：
```python
from pycityproto.city.routing.v2.routing_service_pb2 import (
    GetRouteRequest,    # 路径请求
    GetRouteResponse,   # 路径响应
)
```

**功能说明**：
- **GetRouteRequest**: 路径规划服务的请求格式
- **GetRouteResponse**: 路径规划服务的响应格式

### 类型使用模式

#### 导入便利性

**统一导入**：
```python
from mosstool.type import Map, Person, Trip, Position, TripMode
```

**分类导入**：
```python
# 地图相关
from mosstool.type import Map, Lane, Aoi, LaneType

# 个体相关  
from mosstool.type import Person, Persons, PersonType

# 行程相关
from mosstool.type import Schedule, Trip, TripMode

# 位置相关
from mosstool.type import Position, AoiPosition, LanePosition
```

#### 类型检查和验证

**位置类型检查**：
```python
if position.HasField("aoi_position"):
    aoi_id = position.aoi_position.aoi_id
elif position.HasField("lane_position"):
    lane_id = position.lane_position.lane_id
    s = position.lane_position.s
```

**出行方式判断**：
```python
if trip.mode == TripMode.TRIP_MODE_DRIVE_ONLY:
    # 处理驾车出行
elif trip.mode in [TripMode.TRIP_MODE_BUS_WALK, TripMode.TRIP_MODE_SUBWAY_WALK]:
    # 处理公共交通出行
```

#### 数据构建模式

**个体数据构建**：
```python
person = Person(
    id=1,
    home=Position(aoi_position=AoiPosition(aoi_id=100)),
    schedules=[
        Schedule(
            departure_time=28800,  # 8:00 AM
            trips=[
                Trip(
                    mode=TripMode.TRIP_MODE_DRIVE_ONLY,
                    end=Position(aoi_position=AoiPosition(aoi_id=200))
                )
            ]
        )
    ]
)
```

### 版本兼容性

**版本检查**：
```python
# TODO: pycityproto version checking
```

**向前兼容**：
- 所有类型定义遵循 Protocol Buffers 的向前兼容原则
- 新增字段使用可选属性，不破坏现有代码
- 枚举值保持向后兼容

### 扩展性设计

**模块化组织**：
- 按功能域分组导入，便于维护和扩展
- 明确的依赖关系，避免循环引用
- 统一的命名规范和文档标准

**类型安全**：
- 强类型定义，减少运行时错误
- 明确的字段类型和约束
- 完整的枚举覆盖

### 应用场景

**地图构建**：
- 使用 Map、Lane、Aoi 等类型构建完整地图
- 利用位置类型精确定位地图元素
- 通过枚举确保数据一致性

**行程生成**：
- 使用 Person、Schedule、Trip 构建出行需求
- 利用出行方式枚举支持多模式出行
- 通过位置类型实现精确的起止点定义

**路径规划**：
- 使用 GetRouteRequest/Response 进行服务通信
- 利用 Journey 类型表示复杂路径
- 支持多种出行方式的路径组合

**数据交换**：
- 统一的数据格式，支持跨平台交换
- 标准化的类型定义，便于集成
- 完整的元数据支持，提高数据质量

## utils/

utils 模块提供了 mosstool 中的通用工具函数和实用程序，包括格式转换、地图操作、人口匹配、颜色处理等核心功能。这些工具为其他模块提供了基础支持，简化了开发流程并提高了代码复用性。

### 功能概述

**格式转换**：提供 Protobuf 与 JSON、Dict、MongoDB 之间的双向转换

**地图操作**：支持地图合并、分割等复杂操作

**人口匹配**：基于地理信息和人口数据的智能匹配算法

**颜色工具**：提供颜色格式转换功能

**数据处理**：支持多进程、批量处理等高效数据操作

### 核心模块

#### 1. format_converter.py

格式转换器提供了 Protobuf 消息与其他数据格式之间的转换功能，支持 JSON、Dictionary 和 MongoDB 集合的双向转换。

**主要转换函数**：

**pb2json(pb: Message) -> str**
```python
def pb2json(pb: Message):
    """
    Convert a protobuf message to a JSON string.
    
    Args:
    - pb: The protobuf message to be converted.
    
    Returns:
    - The JSON string.
    """
```
**功能说明**：
- 将 Protobuf 消息转换为 JSON 字符串
- 包含默认值字段
- 保持原始字段名称
- 枚举值使用整数表示

**pb2dict(pb: Message) -> dict**
```python
def pb2dict(pb: Message):
    """
    Convert a protobuf message to a Python dictionary.
    
    Args:
    - pb: The protobuf message to be converted.
    
    Returns:
    - The Python dict.
    """
```
**功能说明**：
- 将 Protobuf 消息转换为 Python 字典
- 配置选项与 pb2json 相同
- 便于数据操作和处理

**pb2coll(pb: Message, coll: Collection, insert_chunk_size: int = 0, drop: bool = False)**
```python
def pb2coll(pb: Message, coll: Collection, insert_chunk_size: int = 0, drop: bool = False):
    """
    Convert a protobuf message to a MongoDB collection.
    
    Args:
    - pb: The protobuf message to be converted.
    - coll: The MongoDB collection to be inserted.
    - insert_chunk_size: The chunk size for inserting the collection. If it is 0, insert all the data at once.
    - drop: Drop the MongoDB collection or not. True for drop, False for not.
    """
```
**功能说明**：
- 将 Protobuf 消息存储到 MongoDB 集合
- 支持批量插入优化
- 自动生成文档结构：`{"class": class_name, "data": data}`
- 支持重复字段和单一字段的处理

**反向转换函数**：

**json2pb(json: str, pb: T) -> T**
```python
def json2pb(json: str, pb: T) -> T:
    """
    Convert a JSON string to a protobuf message.
    
    Args:
    - json: The JSON string to be converted.
    - pb: The protobuf message to be filled.
    
    Returns:
    - The protobuf message.
    """
```

**dict2pb(d: dict, pb: T) -> T**
```python
def dict2pb(d: dict, pb: T) -> T:
    """
    Convert a Python dictionary to a protobuf message.
    
    Args:
    - d: The Python dict to be converted.
    - pb: The protobuf message to be filled.
    
    Returns:
    - The protobuf message.
    """
```

**coll2pb(coll: Collection, pb: T) -> T**
```python
def coll2pb(coll: Collection, pb: T) -> T:
    """
    Convert a MongoDB collection to a protobuf message.
    
    Args:
    - coll: The MongoDB collection to be converted.
    - pb: The protobuf message to be filled.
    
    Returns:
    - The protobuf message.
    """
```

**使用模式**：
```python
# Protobuf 转换为其他格式
json_str = pb2json(map_pb)
map_dict = pb2dict(map_pb)
pb2coll(map_pb, mongodb_collection)

# 其他格式转换为 Protobuf
map_pb = json2pb(json_str, Map())
map_pb = dict2pb(map_dict, Map())
map_pb = coll2pb(mongodb_collection, Map())
```

#### 2. map_merger.py

地图合并器提供了将多个地图合并为一个完整地图的功能，支持投影统一、边界计算和数据验证。

**核心函数**：

**merge_map(partial_maps: List[Map], output_path: Optional[str] = None, output_lane_length_check: bool = False) -> Map**
```python
def merge_map(
    partial_maps: List[Map],
    output_path: Optional[str] = None,
    output_lane_length_check: bool = False,
) -> Map:
    """
    Args:
    - partial_maps (list[Map]): maps to be merged.
    - output_path (str): merged map output path.
    - output_lane_length_check (bool): whether to check lane length.
    
    Returns:
    - merged map.
    """
```

**功能特性**：
- **投影验证**：确保所有输入地图使用相同的投影系统
- **数据合并**：整合 lanes、roads、junctions、aois、pois 等所有地图元素
- **边界计算**：自动计算合并后地图的地理边界
- **数据过滤**：移除无效连接和孤立元素
- **格式验证**：确保输出地图符合格式要求

**辅助函数**：

**_filter_map(map_dict: dict) -> dict**
```python
def _filter_map(map_dict: dict):
    """
    Filter invalid values in output map
    """
```
**功能说明**：
- 过滤无效的 AOI 连接
- 验证车道引用的完整性
- 移除未连接到路网的 AOI
- 确保位置和门禁数据的一致性

**处理流程**：
1. 验证输入地图的投影一致性
2. 合并所有地图元素到统一结构
3. 生成新的地图头信息（边界、时间戳等）
4. 过滤无效数据和连接
5. 执行格式检查和验证
6. 序列化输出到文件（可选）

**使用示例**：
```python
# 合并多个部分地图
merged_map = merge_map(
    partial_maps=[map1, map2, map3],
    output_path="merged_map.pb",
    output_lane_length_check=True
)
```

#### 3. map_splitter.py

地图分割器根据给定的地理边界将大地图分割为多个小地图，支持基于多边形的空间分割。

**核心函数**：

**split_map(geo_data: FeatureCollection, map: Map, output_path: Optional[str] = None, distance_threshold: float = 50.0) -> Dict[Any, Map]**
```python
def split_map(
    geo_data: FeatureCollection,
    map: Map,
    output_path: Optional[str] = None,
    distance_threshold: float = 50.0,
) -> Dict[Any, Map]:
    """
    Args:
    - geo_data (FeatureCollection): polygon geo files.
    - map (Map): the map.
    - output_path (str): splitted map output path.
    - distance_threshold (float): maximum distance considered to be contained in a bounding box.
    
    Returns:
    - List of splitted maps.
    """
```

**功能特性**：
- **空间索引**：使用 STRtree 进行高效的空间查询
- **智能分配**：基于中心点距离将地图元素分配到对应区域
- **完整性保证**：确保分割后每个地图包含完整的关联数据
- **投影转换**：支持经纬度坐标到投影坐标的转换
- **批量输出**：支持同时输出多个分割地图文件

**辅助函数**：

**_center_point(lanes_dict: Dict[int, dict], lane_ids: List[int]) -> Point**
```python
def _center_point(lanes_dict: Dict[int, dict], lane_ids: List[int]) -> Point:
    """计算车道集合的中心点"""
```

**_gen_header(map_name: str, poly_id: int, proj_str: str, lanes: List[dict]) -> dict**
```python
def _gen_header(map_name: str, poly_id: int, proj_str: str, lanes: List[dict]) -> dict:
    """生成分割地图的头信息"""
```

**分割流程**：
1. 解析地理边界多边形数据
2. 建立空间索引树结构
3. 计算道路和交叉口的中心点
4. 基于距离阈值分配地图元素
5. 补充关联的车道、AOI、POI 数据
6. 生成新的地图头信息
7. 验证数据完整性并输出

**使用示例**：
```python
# 根据区域边界分割地图
split_maps = split_map(
    geo_data=boundary_geojson,
    map=large_map,
    output_path="./split_maps/",
    distance_threshold=100.0
)
```

#### 4. geo_match_pop.py

地理人口匹配器提供了基于地理信息和人口栅格数据的智能人口分配算法，支持高精度的人口估算。

**核心函数**：

**geo2pop(geo_data: Union[GeoDataFrame, FeatureCollection], pop_tif_path: str, upsample_factor: int = 4, pop_in_aoi_factor: float = 0.7, multiprocessing_chunk_size: int = 500) -> Union[GeoDataFrame, FeatureCollection]**
```python
def geo2pop(
    geo_data: Union[GeoDataFrame, FeatureCollection],
    pop_tif_path: str,
    upsample_factor: int = 4,
    pop_in_aoi_factor: float = 0.7,
    multiprocessing_chunk_size: int = 500,
) -> Union[GeoDataFrame, FeatureCollection]:
    """
    Args:
    - geo_data (GeoDataFrame | FeatureCollection): polygon geo files.
    - pop_tif_path (str): path to population tif file.
    - upsample_factor (int): scaling factor for dividing the raw population data grid.
    - pop_in_aoi_factor (float): the proportion of the total population within the AOI.
    - multiprocessing_chunk_size (int): the maximum size of each multiprocessing chunk
    
    Returns:
    - geo_data (GeoDataFrame | FeatureCollection): geo files with population.
    """
```

**核心算法特性**：
- **多重上采样**：两阶段像素细分提高精度
- **智能分配**：基于 AOI 覆盖的智能人口分配
- **多进程处理**：高效的并行计算支持
- **多数据源支持**：兼容 GeoDataFrame 和 GeoJSON 格式
- **质量控制**：人口总量平衡和比例校正

**辅助函数**：

**_gps_distance(LON1, LAT1, LON2=None, LAT2=None) -> float**
```python
def _gps_distance(
    LON1: Union[float, Tuple[float, float]],
    LAT1: Union[float, Tuple[float, float]],
    LON2: Optional[float] = None,
    LAT2: Optional[float] = None,
) -> float:
    """GPS distance calculation using Haversine formula"""
```

**_get_pixel_info(band, x_left, y_upper, x_step, y_step, bbox, padding=20) -> dict**
```python
def _get_pixel_info(band, x_left, y_upper, x_step, y_step, bbox, padding=20):
    """
    Get the information of each WorldPop pixel within the latitude and longitude range
    Returns: {idx(i,j) : (Point(lon, lat), population)}
    """
```

**_upsample_pixels_unit(arg) -> List**
```python
def _upsample_pixels_unit(arg):
    """
    第一阶段上采样：基于 AOI 覆盖的智能人口分配
    原始像素约 100m×100m，等分为 (100/n)×(100/n)
    人口按覆盖 AOI 的网格单元均匀分配
    """
```

**_upsample_pixels_idiot_unit(arg) -> List**
```python
def _upsample_pixels_idiot_unit(arg):
    """
    第二阶段上采样：等比例人口分配
    人口在所有网格单元中均匀分配
    """
```

**处理流程**：
1. 解析地理数据和人口栅格文件
2. 计算地理边界和坐标转换参数
3. 提取边界内的人口像素信息
4. 执行两阶段上采样处理
5. 计算每个多边形内的人口总和
6. 应用人口比例校正因子
7. 将结果写回地理数据结构

**使用示例**：
```python
# 为地理区域匹配人口数据
geo_with_pop = geo2pop(
    geo_data=aoi_geojson,
    pop_tif_path="worldpop_2020.tif",
    upsample_factor=4,
    pop_in_aoi_factor=0.7
)
```

#### 5. color.py

颜色工具提供了颜色格式转换功能，主要用于可视化和界面开发。

**核心函数**：

**hex_to_rgba(hex: str, alpha: Union[float, int] = 255) -> list[int]**
```python
def hex_to_rgba(hex: str, alpha: Union[float, int] = 255) -> list[int]:
    """
    Convert a hex color code to an rgba color code.
    
    Args:
    - hex: The hex color code to be converted.
    - alpha: The alpha value of the rgba color code.
    
    Returns:
    - The rgba color code [r, g, b, a].
    """
```

**功能特性**：
- **格式支持**：支持带或不带 # 前缀的十六进制颜色
- **透明度控制**：可自定义 alpha 通道值
- **标准化输出**：返回标准的 RGBA 整数数组

**使用示例**：
```python
# 十六进制转 RGBA
rgba = hex_to_rgba("#FF5733", alpha=128)  # [255, 87, 51, 128]
rgba = hex_to_rgba("00FF00")              # [0, 255, 0, 255]
```

### 应用场景

#### 数据集成

**多源地图合并**：
```python
# 合并来自不同数据源的地图
osm_map = create_road_net(osm_data)
cad_map = convert_cad_to_map(cad_data)
merged_map = merge_map([osm_map, cad_map])
```

**格式标准化**：
```python
# 统一数据格式
json_data = pb2json(map_pb)
dict_data = pb2dict(map_pb)
pb2coll(map_pb, mongodb_collection)
```

#### 大规模处理

**地图分区处理**：
```python
# 将大地图分割为可管理的小块
admin_boundaries = load_geojson("admin_boundaries.geojson")
split_maps = split_map(admin_boundaries, large_map)
```

**人口数据集成**：
```python
# 为 AOI 添加人口属性
aoi_with_pop = geo2pop(
    geo_data=aoi_data,
    pop_tif_path="worldpop.tif"
)
```

#### 可视化支持

**颜色处理**：
```python
# 为可视化准备颜色数据
colors = [hex_to_rgba(color) for color in color_palette]
```

### 性能优化

#### 并行处理

**多进程支持**：
- geo2pop 使用多进程池进行人口计算
- 支持自定义批次大小和进程数
- 自动负载均衡和内存管理

**批量处理**：
- 支持大数据集的分批处理
- 内存友好的流式处理
- 进度监控和错误恢复

#### 算法优化

**空间索引**：
- 使用 STRtree 进行高效空间查询
- 减少 O(n²) 复杂度到 O(n log n)
- 支持大规模地理数据处理

**缓存机制**：
- 像素信息缓存减少重复计算
- 坐标转换结果复用
- 内存池管理优化

### 扩展性

#### 格式扩展

**新格式支持**：
- 易于添加新的数据格式转换器
- 统一的转换接口设计
- 向后兼容的版本管理

**自定义处理**：
- 可扩展的处理管道
- 插件式的算法替换
- 配置驱动的参数调整

#### 算法改进

**人口分配算法**：
- 支持不同的人口分配策略
- 可配置的上采样参数
- 多种数据源的融合算法

**地图处理算法**：
- 可扩展的地图合并策略
- 自定义的分割算法
- 智能的数据验证规则

## UE converter（geojson2map_for_ue_fixz.py, map2geojson_for_ue_fixz.py）

UE 转换器模块提供了与 Unreal Engine (UE) 集成的地图数据转换功能，支持地图数据的导出到 UE 以及从 UE 校准后数据的回流。该模块专门处理 Z 坐标校准问题，确保地图数据在 UE 环境中的准确性和一致性。

### 功能概述

**双向转换**：支持地图数据导出到 UE 和从 UE 回流校准数据

**Z 坐标校准**：专门处理高程数据的精确校准和修正

**数据库集成**：与 MongoDB 无缝集成，支持批量数据处理

**格式兼容**：支持 GeoJSON 格式的标准化导入导出

**地图重建**：支持校准后的完整地图重建和验证

### 核心模块

#### 1. map2geojson_for_ue_fixz.py

地图到 GeoJSON 导出器，将 MongoDB 中存储的地图数据导出为适用于 UE Z 坐标校准的 GeoJSON 格式。

**主要功能**：

**main() 函数**
```python
def main():
    """
    主执行函数：从 MongoDB 导出地图数据为 GeoJSON 格式
    
    处理流程：
    1. 连接 MongoDB 数据库
    2. 加载地图数据到 Protobuf 格式
    3. 创建可视化地图对象
    4. 提取车道特征数据
    5. 生成 GeoJSON 特征集合
    6. 输出到文件
    """
```

**核心处理流程**：

**数据库连接和加载**：
```python
client = pymongo.MongoClient(MONGO_URI)
coll = client[MONGO_DB][MONGO_COLL]
m = Map()
coll2pb(coll, m)
```
- 建立 MongoDB 连接
- 加载指定集合的地图数据
- 转换为 Protobuf Map 格式

**地图可视化处理**：
```python
vis = VisMap(m)
features = list(vis.lane_features.values())
```
- 创建地图可视化对象
- 提取所有车道的几何特征
- 转换为 GeoJSON 特征格式

**文件输出**：
```python
fc = geojson.FeatureCollection(features)
with open(GEOJSON_FILE, "w") as f:
    geojson.dump(fc, f, indent=2)
```
- 构建 GeoJSON FeatureCollection
- 格式化输出到文件
- 支持标准 GeoJSON 格式

**配置参数**：
```python
MONGO_URI = "mongodb://root:****@172.16.40.166:27017"  # MongoDB 连接URI
MONGO_DB = "tsingroc"                                   # 数据库名称
MONGO_COLL = "map_pku_wuhan_demo_0408"                 # 集合名称
GEOJSON_FILE = "map.geojson"                           # 输出文件路径
```

**输出格式**：
- 标准 GeoJSON FeatureCollection 格式
- 包含车道的完整几何信息
- 保留车道 ID 和属性信息
- 兼容 UE 坐标系统

#### 2. geojson2map_for_ue_fixz.py

GeoJSON 到地图导入器，将 UE 校准后的 GeoJSON 文件重新导入到地图数据库，更新 Z 坐标信息。

**主要功能**：

**main() 函数**
```python
def main():
    """
    主执行函数：将 UE 校准后的 GeoJSON 数据导入地图数据库
    
    处理流程：
    1. 加载原始地图数据
    2. 读取校准后的 GeoJSON 文件
    3. 验证数据一致性
    4. 更新车道 Z 坐标
    5. 保存到新数据库集合
    6. 可选地图重建
    """
```

**核心处理流程**：

**原始数据加载**：
```python
client = pymongo.MongoClient(MONGO_URI)
coll = client[MONGO_DB][MONGO_COLL]
m = Map()
coll2pb(coll, m)
projector = pyproj.Proj(m.header.projection)
lane_map = {lane.id: lane for lane in m.lanes}
```
- 加载原始地图数据
- 获取投影坐标系统
- 建立车道 ID 映射字典

**校准数据读取**：
```python
features = []
for file in FIXED_GEOJSON_FILES:
    with open(file, "r") as f:
        calz = json.load(f)
        features += calz["features"]
```
- 读取多个校准后的 GeoJSON 文件
- 合并所有特征数据
- 支持批量文件处理

**数据一致性验证**：
```python
feature_ids = set()
for one in features:
    id = one["id"]
    if id in feature_ids:
        raise ValueError(f"ID重复: {id}")
    feature_ids.add(id)
```
- 检查特征 ID 的唯一性
- 防止数据重复和冲突
- 确保数据完整性

**Z 坐标更新**：
```python
for one in features:
    id = one["id"]
    target_lane = lane_map[id]
    coordinates = one["geometry"]["coordinates"]
    nodes = []
    for lng, lat, z in coordinates:
        x, y = projector(lng, lat)
        nodes.append(XYPosition(x=x, y=y, z=z))
    target_lane.center_line.CopyFrom(Polyline(nodes=nodes))
```
- 遍历所有校准后的特征
- 提取经纬度和高程坐标
- 转换为投影坐标系统
- 更新车道中心线的 Z 坐标

**数据库更新**：
```python
m.ClearField("lanes")
m.lanes.extend(lane_map.values())
pb2coll(m, client[FIXED_MONGO_DB][FIXED_MONGO_COLL], drop=True)
```
- 清除原有车道数据
- 添加更新后的车道数据
- 保存到新的数据库集合

**可选地图重建**：
```python
if REBUILD_MAP:
    builder = Builder(
        net=m,
        proj_str=m.header.projection,
        gen_sidewalk_speed_limit=50 / 3.6,
        aoi_mode="append",
        road_expand_mode="M",
    )
    rebuild_m = builder.build(m.header.name)
    rebuild_pb = dict2pb(rebuild_m, Map())
    with open("data/temp/rebuild_fixz_m.pb", "wb") as f:
        f.write(rebuild_pb.SerializeToString())
```
- 使用 Builder 重建完整地图
- 配置人行道生成参数
- 保持 AOI 数据完整性
- 输出重建后的地图文件

**配置参数**：
```python
MONGO_URI = "mongodb://****"                           # MongoDB 连接URI
MONGO_DB = "tsingroc"                                  # 原始数据库名称
MONGO_COLL = "pku_wuhan_demo_20240408"                # 原始集合名称
FIXED_GEOJSON_FILES = ["map.geojson"]                 # 校准后的文件列表
FIXED_MONGO_DB = "tsingroc"                           # 修正后数据库名称
FIXED_MONGO_COLL = "pku_wuhan_demo_20240408_fixz"    # 修正后集合名称
REBUILD_MAP = True                                     # 是否重建地图
```

### 技术特性

#### 坐标系统处理

**投影转换**：
- 支持经纬度与投影坐标的双向转换
- 使用 pyproj 库进行精确坐标变换
- 保持坐标精度和一致性

**高程校准**：
- 专门处理 Z 坐标的精确校准
- 支持 UE 环境下的高程修正
- 确保地形与道路的正确匹配

#### 数据验证

**完整性检查**：
- ID 唯一性验证
- 特征数据完整性检查
- 坐标数据有效性验证

**一致性保证**：
- 原始数据与校准数据的映射验证
- 几何拓扑关系的保持
- 属性信息的一致性维护

#### 性能优化

**批量处理**：
- 支持多文件批量导入
- 高效的内存管理
- 优化的数据库操作

**增量更新**：
- 仅更新变化的坐标信息
- 保持其他属性不变
- 减少数据传输量

### 应用场景

#### UE 集成工作流

**数据导出流程**：
1. 使用 `map2geojson_for_ue_fixz.py` 导出地图数据
2. 在 UE 中加载 GeoJSON 文件
3. 进行地形匹配和高程校准
4. 导出校准后的坐标数据

**数据回流流程**：
1. 从 UE 获取校准后的 GeoJSON 数据
2. 使用 `geojson2map_for_ue_fixz.py` 导入校准数据
3. 更新数据库中的地图信息
4. 重建完整的地图结构

#### 质量控制

**数据验证**：
```python
# 检查导出数据的完整性
exported_features = vis.lane_features
assert len(exported_features) == len(m.lanes), "车道数量不匹配"

# 验证校准后数据的一致性
for feature in calibrated_features:
    assert feature["id"] in lane_map, f"未找到车道 ID: {feature['id']}"
```

**精度验证**：
```python
# 验证坐标精度
for coord in coordinates:
    lng, lat, z = coord
    assert -180 <= lng <= 180, "经度超出范围"
    assert -90 <= lat <= 90, "纬度超出范围"
    assert z is not None, "高程值缺失"
```

### 扩展功能

#### 自定义校准算法

**高程插值**：
- 支持不同的高程插值算法
- 可配置的插值参数
- 边界条件处理

**平滑处理**：
- 坐标序列的平滑算法
- 去除异常值和噪声
- 保持道路几何特征

#### 批量处理优化

**并行处理**：
- 多文件并行读取
- 坐标转换并行计算
- 数据库并行写入

**内存管理**：
- 大文件流式处理
- 内存使用优化
- 临时数据清理

### 使用示例

#### 基本使用流程

**导出地图到 UE**：
```bash
# 配置数据库连接信息
python map2geojson_for_ue_fixz.py
# 输出: map.geojson
```

**从 UE 导入校准数据**：
```bash
# 将校准后的文件放置到指定位置
# 配置输入文件列表
python geojson2map_for_ue_fixz.py
# 输出: 更新的数据库集合和重建地图文件
```

#### 自定义配置

**修改数据库配置**：
```python
# 自定义数据库连接
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "custom_db"
MONGO_COLL = "custom_collection"
```

**调整重建参数**：
```python
# 自定义地图重建配置
builder = Builder(
    net=m,
    proj_str=m.header.projection,
    gen_sidewalk_speed_limit=60 / 3.6,  # 调整人行道限速
    aoi_mode="append",                   # AOI 处理模式
    road_expand_mode="L",                # 道路拓展模式
)
```

### 注意事项

#### 数据安全

**敏感信息保护**：
- 数据库连接信息需要安全存储
- 避免在代码中硬编码密码
- 使用环境变量或配置文件

**数据备份**：
- 处理前备份原始数据
- 使用新集合存储修正数据
- 保留数据处理历史记录

#### 兼容性

**版本兼容**：
- 确保 UE 版本与数据格式兼容
- 验证 GeoJSON 格式标准符合性
- 测试不同操作系统下的兼容性

**数据格式**：
- 严格遵循 GeoJSON 标准
- 保持坐标精度要求
- 确保属性数据完整性
