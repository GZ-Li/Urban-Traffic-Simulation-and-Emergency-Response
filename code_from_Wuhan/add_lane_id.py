import json
import random

with open('map_test_1610.json', 'r', encoding='utf-8') as f:
    map_data = json.load(f)
with open('convert.json', 'r', encoding='utf-8') as f:
    rou_data = json.load(f)


rou_lst = []
for test_rou_data in rou_data:
    route = test_rou_data['data']['schedules'][0]['trips'][0]['routes'][0]['driving']['road_ids']
    start_point = route[0]
    end_point = route[-1]
    print(route)

    target_id_1 = start_point
    target_id_2 = end_point
    for road in map_data['roads']:
        if road['id'] == start_point:
            print(road)
            target_id_1 = random.choice(road['lane_ids'])
            break
    for road in map_data['roads']:
        if road['id'] == end_point:
            print(road)
            target_id_2 = random.choice(road['lane_ids'])
            break

    test_rou_data['data']['home']['lane_position']['lane_id'] = target_id_1
    test_rou_data['data']['schedules'][0]['trips'][0]['end']['lane_position']['lane_id'] = target_id_2
    
    for lane in map_data['lanes']:
        if lane['id'] == target_id_2:
            if lane['length'] - 0.1 > 0:
                test_rou_data['data']['home']['lane_position']['s'] = lane['length'] - 0.1
            else:
                test_rou_data['data']['home']['lane_position']['s'] = lane['length'] - 0.1
with open('convert_update_from_GZ__test_1610.json', 'w', encoding='utf-8') as f:
    json.dump(rou_data, f, ensure_ascii=False, indent=4)