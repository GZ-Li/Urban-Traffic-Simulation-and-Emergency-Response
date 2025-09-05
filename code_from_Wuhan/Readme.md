# 雨天参数搜索流程

## 1. 正常天气车速数据记录
- **功能**：记录在模拟中，在正常天气设定下，各路段的速度信息
- **脚本路径**: `/home/nkk/work/src/python/trafficlight_rl/normal_simulate_speed.py`
- **输出文件**: `rain_setting_adjustment/output/normal_speed_dict.json`
- **执行命令**:
  ```bash
  python3 ./normal_simulate_speed.py \
    --exp 20250731_max_pressure \
    --mongo_uri "数据库链接" \
    --map_db "数据库名称" \
    --map_coll "数据库集合" \
    --agent_db "agent数据库" \
    --agent_coll "agent数据库名称" \
    --output_sql_dsn "输出位置" \
    --output_bbox 114,30.3,115,30.7

## 2. 雨天天气车速数据记录
- **功能**：记录在模拟中，在极端天气的不同参数设定下，各路段的速度信息
- **脚本路径**: `/home/nkk/work/src/python/trafficlight_rl/rain_simulate_speed.py`
- **输出文件**: `rain_setting_adjustment/output/rain_speed_dict.json`
- **执行命令**:
  ```bash
  python3 ./rain_simulate_speed.py \
    --exp 20250731_max_pressure \
    --mongo_uri "数据库链接" \
    --map_db "数据库名称" \
    --map_coll "数据库集合" \
    --agent_db "agent数据库" \
    --agent_coll "agent数据库名称" \
    --output_sql_dsn "输出位置" \
    --output_bbox 114,30.3,115,30.7

## 3. 参数搜索执行
- **脚本路径**: `/home/nkk/work/src/python/rain_setting_adjustment/adverse_weather_setting_adjustment.py`
得到雨天和正常天气下的车速文件后，运行参数搜索执行脚本（注意保证其用到的车速信息与前两步记录得到的车速信息一致），即可搜索得到最优参数，其中的recall_factor可用于设定搜索目标中，召回率和准确率的比例（recall_factor在0到1之间，1代表只考虑召回率，0代表只考虑准确率）；