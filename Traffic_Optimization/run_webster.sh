#!/bin/bash
# Webster配时方案
# 基于交通流量（排队数）计算固定配时

python3 /home/nkk/work/src/python/run_incremental.py \
  --task road_opt \
  --scenario webster \
  --cycle_seconds 30 \
  --min_green_seconds 5 \
  --mongo_uri mongodb://root:qZ7ILv0Xs6VnJcPg12KU3AoYhWKb4Cla@172.16.40.166:27017 \
  --map_db tsingroc \
  --map_coll map_pku_wuhan_demo_1015c_rl \
  --agent_db tsingroc \
  --agent_coll person_test_20250724_1015cc \
  --total_steps 120 \
  --interval 30 \
  --output_sql_dsn postgres://postgres:QSo084HA7Sji9jsm73KjRUcTGWynUsxu@172.16.40.166:5432/simulation \
  --output_bbox 114,30.3,115,30.7
