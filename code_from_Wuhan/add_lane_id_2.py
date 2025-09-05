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

    target_id_1 = "***"
    target_id_2 = "***"
    for road in map_data['roads']:
        if road['id'] == start_point:
            target_id_1 = random.choice(road['lane_ids'])
            break
    for road in map_data['roads']:
        if road['id'] == end_point:
            target_id_2 = random.choice(road['lane_ids'])
            break
    
    if target_id_1 != "***" and target_id_2 != "***":
        test_rou_data['data']['home']['lane_position']['lane_id'] = target_id_1
        test_rou_data['data']['schedules'][0]['trips'][0]['end']['lane_position']['lane_id'] = target_id_2
    
        for lane in map_data['lanes']:
            if lane['id'] == target_id_2:
                if lane['length'] - 0.1 > 0:
                    test_rou_data['data']['home']['lane_position']['s'] = lane['length'] - 0.1
                else:
                    test_rou_data['data']['home']['lane_position']['s'] = lane['length'] - 0.1
        rou_lst.append(test_rou_data)
        break
        
with open('convert_update_from_GZ_test_1610_filtered_single_vehicle.json', 'w', encoding='utf-8') as f:
    json.dump(rou_lst, f, ensure_ascii=False, indent=4)