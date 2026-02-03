"""
生成Baseline扫雪策略记录
假设所有道路在0时刻就已经清扫完成（理想baseline场景）
复刻snow_plow_project的JSON格式
"""
import xml.etree.ElementTree as ET
import json
from pathlib import Path

# 配置
NET_FILE = "E:\\Traffic_Simulation\\snow_plow_project\\net\\core_withshape_with_light_changing.net.xml"
OUTPUT_JSON = "snowplow_baseline_time_steps_record.json"

def get_all_edges(net_file):
    """获取路网中所有边的ID"""
    tree = ET.parse(net_file)
    root = tree.getroot()
    
    all_edges = []
    for edge in root.findall('edge'):
        edge_id = edge.get('id')
        # 跳过内部边
        if not edge_id.startswith(':'):
            all_edges.append(edge_id)
    
    return all_edges

def generate_baseline_record(all_edges, time_points_hours=[0, 1, 2, 3, 4, 5]):
    """
    生成baseline记录：所有道路在0时刻就已清扫完成
    在每个时间点都保持所有道路已清扫状态
    """
    record = {}
    
    for i, hour in enumerate(time_points_hours):
        time_minutes = hour * 60
        time_seconds = time_minutes * 60
        
        step_key = f"step_{i}_time_{time_minutes}min"
        
        record[step_key] = {
            "time_seconds": time_seconds,
            "time_minutes": float(time_minutes),
            "total_cleaned_edges": all_edges.copy(),
            "regions": {
                "region1": {
                    "cleaned_edges": [],
                    "num_cleaned": 0
                },
                "region2": {
                    "cleaned_edges": [],
                    "num_cleaned": 0
                },
                "region3": {
                    "cleaned_edges": [],
                    "num_cleaned": 0
                },
                "region4": {
                    "cleaned_edges": [],
                    "num_cleaned": 0
                },
                "region5": {
                    "cleaned_edges": [],
                    "num_cleaned": 0
                }
            },
            "num_total_cleaned": len(all_edges)
        }
    
    return record

def main():
    print("="*60)
    print("生成Baseline扫雪策略记录".center(60))
    print("="*60)
    
    # 获取所有边
    print(f"\n正在读取路网文件: {NET_FILE}")
    all_edges = get_all_edges(NET_FILE)
    print(f"  找到 {len(all_edges)} 条道路")
    
    # 生成baseline记录
    print("\n正在生成baseline记录...")
    baseline_record = generate_baseline_record(all_edges)
    print(f"  生成 {len(baseline_record)} 个时间步记录")
    
    # 保存JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(baseline_record, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Baseline记录已保存: {OUTPUT_JSON}")
    print(f"   所有 {len(all_edges)} 条道路在0时刻已清扫完成")
    print("="*60)

if __name__ == "__main__":
    main()
