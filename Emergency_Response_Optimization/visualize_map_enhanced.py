"""
增强版地图可视化：支持最优解、贪心解、Multi_Accident数据
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import os
import argparse

def load_edge_coordinates(net_file):
    """加载边的坐标信息（从SUMO网络文件）"""
    import xml.etree.ElementTree as ET
    
    tree = ET.parse(net_file)
    root = tree.getroot()
    
    edge_coords = {}
    all_edges = []
    
    for edge in root.findall('edge'):
        edge_id = edge.get('id')
        if ':' in edge_id:  # 跳过junction内部边
            continue
        
        lane = edge.find('lane')
        if lane is not None:
            shape = lane.get('shape')
            if shape:
                # 解析坐标点 "x1,y1 x2,y2 ..."
                points = []
                for point_str in shape.split():
                    x, y = map(float, point_str.split(','))
                    points.append((x, y))
                edge_coords[edge_id] = points
                all_edges.append(points)
    
    return edge_coords, all_edges

def visualize_test_results(result_folder, strategy='optimal', net_file=None):
    """
    可视化test_using_test3_config.py的结果
    strategy: 'optimal' 或 'greedy'
    """
    print(f"\n正在处理结果文件夹: {result_folder}")
    print(f"绘制策略: {strategy}")
    
    # 选择对应的路径文件
    if strategy == 'optimal':
        paths_file = os.path.join(result_folder, 'optimal_paths.json')
        title = '应急响应最优分配方案'
        output_file = os.path.join(result_folder, 'assignment_map_optimal.png')
    else:  # greedy
        paths_file = os.path.join(result_folder, 'greedy_paths.json')
        title = '应急响应贪心分配方案'
        output_file = os.path.join(result_folder, 'assignment_map_greedy.png')
    
    if not os.path.exists(paths_file):
        print(f"错误: 找不到文件 {paths_file}")
        return None
    
    # 加载分配结果
    with open(paths_file, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
    print(f"已加载 {len(assignments)} 条分配")
    
    # 加载医院位置
    hospital_df = pd.read_csv('data/Hospital_Location.csv')
    print(f"已加载 {len(hospital_df)} 个医院")
    
    # 使用默认网络文件
    if net_file is None:
        net_file = r"E:\Traffic_Simulation\Traffic_accident\full_net\new_add_light.net.xml"
    
    # 加载边坐标
    print(f"正在加载SUMO网络: {net_file}")
    edge_coords, all_edges = load_edge_coordinates(net_file)
    print(f"已加载 {len(edge_coords)} 条边的坐标")
    
    # 事故点字典
    accident_spots = {
        0: "200042649",
        1: "200040849", 
        2: "200063134",
        3: "200040901"
    }
    
    # 获取医院坐标
    hospital_coords = {}
    for idx, row in hospital_df.iterrows():
        road_id = str(row['road_id'])
        if road_id in edge_coords and edge_coords[road_id]:
            points = edge_coords[road_id]
            mid_idx = len(points) // 2
            x, y = points[mid_idx]
            hospital_coords[idx] = {
                'name': row['name'],
                'x': x,
                'y': y,
                'road_id': road_id
            }
    print(f"成功定位 {len(hospital_coords)} 个医院")
    
    # 获取事故点坐标
    accident_coords = {}
    for idx, road_id in accident_spots.items():
        if road_id in edge_coords and edge_coords[road_id]:
            points = edge_coords[road_id]
            mid_idx = len(points) // 2
            x, y = points[mid_idx]
            accident_coords[idx] = {
                'x': x,
                'y': y,
                'road_id': road_id
            }
    print(f"成功定位 {len(accident_coords)} 个事故点")
    
    # 创建图形
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # 绘制路网
    print("正在绘制路网...")
    for edge_points in all_edges:
        xs = [p[0] for p in edge_points]
        ys = [p[1] for p in edge_points]
        ax.plot(xs, ys, color='gray', linewidth=0.5, alpha=0.3, zorder=1)
    
    # 定义颜色
    hospital_colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']
    
    # 绘制分配关系
    print(f"\n{title}:")
    for assignment in assignments:
        accident_idx = assignment['accident_idx']
        hospital_idx = assignment['hospital_idx']
        time = assignment['time']
        
        hospital_name = hospital_coords.get(hospital_idx, {}).get('name', f'医院{hospital_idx+1}')
        
        print(f"  事故点{accident_idx+1} <- {hospital_name}, 时间: {time}秒")
        
        if hospital_idx in hospital_coords and accident_idx in accident_coords:
            h_coord = hospital_coords[hospital_idx]
            a_coord = accident_coords[accident_idx]
            
            # 绘制箭头
            ax.annotate('', xy=(a_coord['x'], a_coord['y']), 
                       xytext=(h_coord['x'], h_coord['y']),
                       arrowprops=dict(arrowstyle='->', 
                                     color=hospital_colors[hospital_idx],
                                     lw=3, alpha=0.8),
                       zorder=3)
            
            # 在箭头中点添加时间标注
            mid_x = (h_coord['x'] + a_coord['x']) / 2
            mid_y = (h_coord['y'] + a_coord['y']) / 2
            ax.text(mid_x, mid_y, f"{time}s", 
                   ha='center', va='center',
                   fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='white', alpha=0.8),
                   zorder=4)
    
    # 绘制医院位置
    for idx, coords in hospital_coords.items():
        ax.scatter(coords['x'], coords['y'], 
                  c=hospital_colors[idx], s=300, 
                  marker='s', edgecolors='black', linewidths=2,
                  label=coords['name'], zorder=5)
        ax.text(coords['x'], coords['y'], str(idx+1), 
               ha='center', va='center', color='white', 
               fontsize=12, fontweight='bold', zorder=6)
    
    # 绘制事故点位置
    for idx, coords in accident_coords.items():
        ax.scatter(coords['x'], coords['y'], 
                  c='red', s=400, marker='^', 
                  edgecolors='darkred', linewidths=2.5,
                  zorder=4)
        ax.text(coords['x'], coords['y']+80, f'事故{idx+1}', 
               ha='center', va='bottom', color='darkred',
               fontsize=11, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.9),
               zorder=4)
    
    # 设置图例
    legend_elements = []
    for idx in sorted(hospital_coords.keys()):
        legend_elements.append(
            mpatches.Patch(color=hospital_colors[idx], 
                         label=hospital_coords[idx]['name'])
        )
    legend_elements.append(
        mpatches.Patch(color='red', label='事故点')
    )
    
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=11, framealpha=0.95)
    
    ax.set_xlabel('X坐标 (m)', fontsize=12)
    ax.set_ylabel('Y坐标 (m)', fontsize=12)
    ax.set_title(f'{title} - 路网可视化', fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.2)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n地图已保存: {output_file}")
    plt.close()
    
    return output_file

def visualize_multi_accident(data_folder, strategy='optimal'):
    """
    可视化Multi_Accident文件夹的结果
    """
    print(f"\n正在处理Multi_Accident文件夹: {data_folder}")
    print(f"绘制策略: {strategy}")
    
    # 加载优化结果
    result_file = os.path.join(data_folder, 'optimization_vs_greedy.json')
    if not os.path.exists(result_file):
        print(f"错误: 找不到文件 {result_file}")
        return None
    
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 选择分配策略
    if strategy == 'optimal':
        assignment = data['optimized_assignment']
        title = 'Multi-Accident最优分配方案'
        output_file = os.path.join(data_folder, 'visualization', 'optimized_assignment_new.png')
    else:
        assignment = data['greedy_assignment']
        title = 'Multi-Accident贪心分配方案'
        output_file = os.path.join(data_folder, 'visualization', 'greedy_assignment_new.png')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"分配关系数: {len(assignment)}")
    
    # 使用Multi_Accident的网络文件
    net_file = os.path.join(data_folder, 'Shaped.net.xml')
    if not os.path.exists(net_file):
        print(f"错误: 找不到网络文件 {net_file}")
        return None
    
    # 加载边坐标
    print(f"正在加载SUMO网络: {net_file}")
    edge_coords, all_edges = load_edge_coordinates(net_file)
    print(f"已加载 {len(edge_coords)} 条边的坐标")
    
    # 创建图形
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # 绘制路网
    print("正在绘制路网...")
    for edge_points in all_edges:
        xs = [p[0] for p in edge_points]
        ys = [p[1] for p in edge_points]
        ax.plot(xs, ys, color='gray', linewidth=0.5, alpha=0.3, zorder=1)
    
    # 定义颜色
    accident_colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred']
    
    # 获取事故点和医院坐标
    accident_coords = {}
    hospital_coords = {}
    
    accident_ids = list(assignment.keys())
    for i, acc_id in enumerate(accident_ids):
        if acc_id in edge_coords and edge_coords[acc_id]:
            points = edge_coords[acc_id]
            mid_idx = len(points) // 2
            x, y = points[mid_idx]
            accident_coords[acc_id] = {'x': x, 'y': y, 'idx': i}
    
    all_hospital_ids = set()
    for hospitals in assignment.values():
        all_hospital_ids.update(hospitals)
    
    for hosp_id in all_hospital_ids:
        if hosp_id in edge_coords and edge_coords[hosp_id]:
            points = edge_coords[hosp_id]
            mid_idx = len(points) // 2
            x, y = points[mid_idx]
            hospital_coords[hosp_id] = {'x': x, 'y': y}
    
    print(f"成功定位 {len(accident_coords)} 个事故点")
    print(f"成功定位 {len(hospital_coords)} 个医院")
    
    # 绘制分配关系
    print(f"\n{title}:")
    for acc_id, hospitals in assignment.items():
        if acc_id not in accident_coords:
            continue
        
        acc_coord = accident_coords[acc_id]
        acc_idx = acc_coord['idx']
        color = accident_colors[acc_idx % len(accident_colors)]
        
        print(f"  事故点 {acc_id}: 分配了 {len(hospitals)} 个医院")
        
        for hosp_id in hospitals:
            if hosp_id not in hospital_coords:
                continue
            
            h_coord = hospital_coords[hosp_id]
            
            # 绘制箭头
            ax.annotate('', xy=(acc_coord['x'], acc_coord['y']), 
                       xytext=(h_coord['x'], h_coord['y']),
                       arrowprops=dict(arrowstyle='->', 
                                     color=color,
                                     lw=2.5, alpha=0.7),
                       zorder=3)
    
    # 绘制医院位置
    for hosp_id, coords in hospital_coords.items():
        ax.scatter(coords['x'], coords['y'], 
                  c='green', s=250, 
                  marker='s', edgecolors='darkgreen', linewidths=2,
                  zorder=5)
        ax.text(coords['x'], coords['y']+50, hosp_id[-4:], 
               ha='center', va='bottom',
               fontsize=8, 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8),
               zorder=5)
    
    # 绘制事故点位置
    for acc_id, coords in accident_coords.items():
        idx = coords['idx']
        color = accident_colors[idx % len(accident_colors)]
        ax.scatter(coords['x'], coords['y'], 
                  c=color, s=400, marker='^', 
                  edgecolors='black', linewidths=2.5,
                  zorder=4)
        ax.text(coords['x'], coords['y']-50, acc_id[-4:], 
               ha='center', va='top', color='black',
               fontsize=9, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.9),
               zorder=4)
    
    # 设置图例
    legend_elements = [
        mpatches.Patch(color='green', label='医院'),
        mpatches.Patch(color='red', label='事故点')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', 
             fontsize=11, framealpha=0.95)
    
    ax.set_xlabel('X坐标 (m)', fontsize=12)
    ax.set_ylabel('Y坐标 (m)', fontsize=12)
    ax.set_title(f'{title} - 路网可视化', fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.2)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n地图已保存: {output_file}")
    plt.close()
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='绘制应急响应分配方案的路网地图')
    parser.add_argument('-f', '--folder', type=str, help='结果文件夹路径')
    parser.add_argument('-s', '--strategy', type=str, default='optimal', 
                       choices=['optimal', 'greedy', 'both'],
                       help='分配策略: optimal, greedy, 或 both')
    parser.add_argument('-m', '--multi', action='store_true',
                       help='处理Multi_Accident文件夹')
    
    args = parser.parse_args()
    
    if args.multi:
        # 处理Multi_Accident
        folder = args.folder if args.folder else 'Multi_Accident'
        if not os.path.isabs(folder):
            folder = os.path.join(os.getcwd(), folder)
        
        if args.strategy == 'both':
            visualize_multi_accident(folder, 'optimal')
            visualize_multi_accident(folder, 'greedy')
        else:
            visualize_multi_accident(folder, args.strategy)
    else:
        # 处理test结果
        if args.folder:
            folder = args.folder
        else:
            # 自动找最新的结果文件夹
            results_dir = 'results'
            folders = [f for f in os.listdir(results_dir) if f.startswith('test_run_')]
            if not folders:
                print("错误: 找不到结果文件夹")
                return
            folder = os.path.join(results_dir, sorted(folders)[-1])
        
        if args.strategy == 'both':
            visualize_test_results(folder, 'optimal')
            visualize_test_results(folder, 'greedy')
        else:
            visualize_test_results(folder, args.strategy)

if __name__ == '__main__':
    main()
