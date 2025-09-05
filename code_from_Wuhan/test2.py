import json
import random

with open('map.json', 'r', encoding='utf-8') as f:
    map_data = json.load(f)
with open('convert.json', 'r', encoding='utf-8') as f:
    rou_data = json.load(f)
    
print(map_data.keys())