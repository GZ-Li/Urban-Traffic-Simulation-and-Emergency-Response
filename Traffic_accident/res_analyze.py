result_dict = {'ambulance_96': 180, 'ambulance_97': 200, 'ambulance_99': 200, 'ambulance_100': 210, 'ambulance_84': 240, 'ambulance_81': 250, 'ambulance_77': 320, 'ambulance_78': 350, 'ambulance_143': 360, 'ambulance_76': 370, 'ambulance_79': 380, 'ambulance_80': 390, 'ambulance_9': 400, 'ambulance_31': 400, 'ambulance_35': 400, 'ambulance_108': 400, 'ambulance_142': 400, 'ambulance_6': 410, 'ambulance_32': 410, 'ambulance_110': 410, 'ambulance_7': 420, 'ambulance_10': 420, 'ambulance_106': 420, 'ambulance_33': 430, 'ambulance_109': 430, 'ambulance_144': 430, 'ambulance_58': 450, 'ambulance_60': 450, 'ambulance_56': 460, 'ambulance_59': 470, 'ambulance_103': 470, 'ambulance_105': 470, 'ambulance_21': 480, 'ambulance_112': 480, 'ambulance_102': 490, 'ambulance_123': 490, 'ambulance_24': 500, 'ambulance_26': 500, 'ambulance_48': 500, 'ambulance_104': 500, 'ambulance_113': 500, 'ambulance_115': 500, 'ambulance_11': 510, 'ambulance_23': 510, 'ambulance_47': 510, 'ambulance_50': 510, 'ambulance_74': 510, 'ambulance_111': 510, 'ambulance_121': 510, 'ambulance_29': 520, 'ambulance_46': 520, 'ambulance_51': 520, 'ambulance_53': 520, 'ambulance_71': 520, 'ambulance_73': 520, 'ambulance_124': 520, 'ambulance_27': 530, 'ambulance_36': 530, 'ambulance_52': 530, 'ambulance_61': 530, 'ambulance_75': 530, 'ambulance_125': 530, 'ambulance_5': 540, 'ambulance_28': 540, 'ambulance_54': 540, 'ambulance_4': 550, 'ambulance_88': 550, 'ambulance_94': 550, 'ambulance_101': 550, 'ambulance_140': 550, 'ambulance_39': 560, 'ambulance_62': 560, 'ambulance_92': 560, 'ambulance_1': 570, 'ambulance_12': 570, 'ambulance_30': 570, 'ambulance_37': 570, 'ambulance_40': 570, 'ambulance_63': 570, 'ambulance_95': 570, 'ambulance_13': 580, 'ambulance_15': 580, 'ambulance_127': 580, 'ambulance_14': 590, 'ambulance_22': 590, 'ambulance_38': 590, 'ambulance_64': 600, 'ambulance_139': 600, 'ambulance_65': 610, 'ambulance_116': 610, 'ambulance_91': 620, 'ambulance_120': 620, 'ambulance_138': 620, 'ambulance_49': 630, 'ambulance_129': 630, 'ambulance_66': 640, 'ambulance_119': 640, 'ambulance_126': 640, 'ambulance_128': 650, 'ambulance_43': 670, 'ambulance_68': 670, 'ambulance_18': 680, 'ambulance_16': 690, 'ambulance_19': 690, 'ambulance_67': 700, 'ambulance_89': 700, 'ambulance_137': 700, 'ambulance_87': 710, 'ambulance_134': 710, 'ambulance_135': 720, 'ambulance_130': 730, 'ambulance_114': 750, 'ambulance_131': 780, 'ambulance_55': 830, 'ambulance_117': 830, 'ambulance_2': 840, 'ambulance_3': 850, 'ambulance_44': 870, 'ambulance_150': 870, 'ambulance_136': 880, 'ambulance_148': 930, 'ambulance_133': 950, 'ambulance_149': 950, 'ambulance_132': 960, 'ambulance_147': 1040, 'ambulance_90': 1090}

import numpy as np

# 初始化矩阵
num_hospitals = 6
num_accidents = 5
routes_per_pair = 5

# 创建两个矩阵：最快时间矩阵和最小序号路线时间矩阵
fastest_time_matrix = np.full((num_hospitals, num_accidents), np.inf)
min_route_time_matrix = np.full((num_hospitals, num_accidents), np.inf)

# 用于存储每个医院-事故点对的所有路线信息
route_info_by_pair = {}

# 处理每条路线
for route_id, time in result_dict.items():
    # 提取路线编号（去掉'ambulance_'前缀）
    route_num = int(route_id.split('_')[1])
    
    # 计算对应的医院和事故点索引
    pair_index = (route_num - 1) // routes_per_pair  # 0-29
    hospital_idx = pair_index // num_accidents       # 医院索引 0-5
    accident_idx = pair_index % num_accidents        # 事故点索引 0-4
    
    # 确保索引在有效范围内
    if hospital_idx < num_hospitals and accident_idx < num_accidents:
        pair_key = (hospital_idx, accident_idx)
        
        # 更新最快时间矩阵
        if time < fastest_time_matrix[hospital_idx, accident_idx]:
            fastest_time_matrix[hospital_idx, accident_idx] = time
        
        # 存储路线信息用于找到最小序号路线
        if pair_key not in route_info_by_pair:
            route_info_by_pair[pair_key] = []
        route_info_by_pair[pair_key].append((route_num, time))

# 找到每个医院-事故点对的最小序号路线时间
for (hospital_idx, accident_idx), routes in route_info_by_pair.items():
    if routes:
        # 按路线序号排序，取最小序号路线的时间
        min_route_num, min_route_time = min(routes, key=lambda x: x[0])
        min_route_time_matrix[hospital_idx, accident_idx] = min_route_time

# 将无穷大值替换为-1（表示没有可用路线）
fastest_time_matrix[fastest_time_matrix == np.inf] = -1
min_route_time_matrix[min_route_time_matrix == np.inf] = -1

# 打印结果
print("最快时间矩阵（医院×事故点）：")
print(fastest_time_matrix)
print("\n最小序号路线时间矩阵（医院×事故点）：")
print(min_route_time_matrix)

# 转换为DataFrame（更清晰的显示）
import pandas as pd

hospitals = [f"医院{i+1}" for i in range(num_hospitals)]
accidents = [f"事故点{i+1}" for i in range(num_accidents)]

fastest_df = pd.DataFrame(fastest_time_matrix, index=hospitals, columns=accidents)
min_route_df = pd.DataFrame(min_route_time_matrix, index=hospitals, columns=accidents)

print("\n最快时间矩阵（DataFrame格式）：")
print(fastest_df)
print("\n最小序号路线时间矩阵（DataFrame格式）：")
print(min_route_df)