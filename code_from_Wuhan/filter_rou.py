import json
import random

with open('map.json', 'r', encoding='utf-8') as f:
    map_data = json.load(f)
with open('convert_update_from_GZ.json', 'r', encoding='utf-8') as f:
    rou_data = json.load(f)
print(len(rou_data))
    
# road_lst = []
# for road in map_data['roads']:
#     road_lst.append(road['id'])

# rou_lst = []
# flag = True
# for element in rou_data:
#     route = element['data']['schedules'][0]['trips'][0]['routes'][0]['driving']['road_ids']
#     for edge in route:
#         if edge not in road_lst:
#             flag = False
#             break
#     if flag == True:
#         rou_lst.append(element)
# print(len(rou_lst))

connection_dict = {}
for junction in map_data['junctions']:
    for connection in junction['driving_lane_groups']:
        if connection['in_road_id'] in list(connection_dict.keys()):
            connection_dict[connection['in_road_id']].append(connection['out_road_id'])
        else:
            connection_dict[connection['in_road_id']] = [connection['out_road_id']]

in_road_list = list(connection_dict.keys())

rou_lst = []
for element in rou_data:
    route = element['data']['schedules'][0]['trips'][0]['routes'][0]['driving']['road_ids']
    flag = True
    for i in range(len(route) - 1):
        route_pair = [route[i], route[i+1]]
        if route_pair[0] in list(connection_dict.keys()):
            if route_pair[1] in connection_dict[route_pair[0]]:
                flag = True
            else:
                flag = False
                break
    if flag == True:
        rou_lst.append(element)
print(len(rou_lst))