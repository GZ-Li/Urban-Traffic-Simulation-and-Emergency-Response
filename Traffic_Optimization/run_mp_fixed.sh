#!/bin/bash
# MP优化后固定配时 - 完整示例
# 第一次仿真：运行MaxPressure并统计相位占比
# 第二次仿真：使用固化配时方案运行

python3 /home/nkk/work/src/python/run_incremental.py \
  --task road_opt \
  --scenario fixed_from_mp \
  --cycle_seconds 50 \
  --min_green_seconds 5 \
  --mp_warmup_cycles 1 \
  --mp_collect_cycles 10 \
  --min_phase_seconds 10 \
  --mongo_uri mongodb://root:qZ7ILv0Xs6VnJcPg12KU3AoYhWKb4Cla@172.16.40.166:27017 \
  --map_db tsingroc \
  --map_coll map_pku_wuhan_demo_1015c_rl \
  --agent_db tsingroc \
  --agent_coll person_test_20250724_1015cc \
  --total_steps 120 \
  --interval 30 \
  --output_sql_dsn postgres://postgres:QSo084HA7Sji9jsm73KjRUcTGWynUsxu@172.16.40.166:5432/simulation \
  --output_bbox 114,30.3,115,30.7
