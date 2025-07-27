import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dbfread import DBF
import geopandas as gpd
from shapely.geometry import LineString
import seaborn as sns


def read_dbf(file_path):
    dbf = DBF(file_path, encoding='utf-8')
    df = pd.DataFrame(iter(dbf))
    return df

def read_shapefile(file_path):
    return gpd.read_file(file_path, encoding='utf-8')

normal_weather = read_shapefile("real_traffic_situation_0718/Normal.shp")
rainy_weather = read_shapefile("real_traffic_situation_0718/Rain.shp")

# 过滤掉status=0的行
normal_weather = normal_weather[normal_weather['status'] != 0]
rainy_weather = rainy_weather[rainy_weather['status'] != 0]
print(rainy_weather)

# 重命名列
normal_weather = normal_weather.rename(columns={
    'speed': 'normal_speed',
})

rainy_weather = rainy_weather.rename(columns={
    'speed': 'rainy_speed',
})

merged_df = pd.merge(
    normal_weather[['direction', 'name', 'normal_speed', 'geometry']],
    rainy_weather[['direction', 'name', 'rainy_speed', 'geometry']],
    on=['direction', 'name', 'geometry'], 
    how='inner'
)

if merged_df.empty:
    print("警告：没有找到共有的路段！请检查方向(direction)和名称(name)列是否匹配。")
else:
    print(f"找到 {len(merged_df)} 条共有的路段（已过滤 status=0 的路段）。")

    # 计算速度差异百分比
    merged_df['speed_diff_percent'] = (
        (merged_df['rainy_speed'] - merged_df['normal_speed']) / 
        (merged_df['normal_speed'] + 1) * 100  # 避免除零
    )
    
    print(merged_df.shape)
    bins = range(-100, 30, 10) 
    labels = [f"{i}%-{i+10}%" for i in range(-10, 110, 10)]
    plt.figure(figsize=(12, 6))
    n, bins, patches = plt.hist(
        merged_df['speed_diff_percent'],
        bins=bins,
        edgecolor='black',
        alpha=0.7,
        color='skyblue',
        density=False  # 显示频数而非频率
    )
    sns.kdeplot(
        merged_df['speed_diff_percent'],
        color='red',
        linewidth=2,
        label='Trend Line'
    )
    mean_val = merged_df['speed_diff_percent'].mean()
    plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=1)
    plt.text(
        mean_val + 1,
        plt.ylim()[1] * 0.9,
        f'Average: {mean_val:.1f}%',
        color='red'
    )
    plt.xlabel('Speed Difference (%)')
    plt.ylabel('Road Count')
    plt.title('Rain\'s Effect on Speed (Binned by 10% Intervals)')
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    plt.show()
    # plt.savefig('speed_comparison_plot_0718.pdf', bbox_inches='tight')
    # plt.show()

    # # 保存为 CSV（不含几何列）和 Shapefile（含几何列）
    # merged_df.to_csv('actual_speed_variation_0718.csv', index=False) 
    # # 绘制直方图
    # plt.figure(figsize=(12, 6))
    # plt.hist(merged_df['speed_diff_percent'], bins=30, edgecolor='black', alpha=0.7, color='skyblue')
    # plt.xlabel('Speed Difference (%)')
    # plt.ylabel('Road Count')
    # plt.title('Rain\'s Effect on Speed')
    # plt.axvline(merged_df['speed_diff_percent'].mean(), color='red', linestyle='dashed', linewidth=1)
    # plt.text(
    #     merged_df['speed_diff_percent'].mean() + 1,
    #     plt.ylim()[1] * 0.9,
    #     f'Average: {merged_df["speed_diff_percent"].mean():.1f}%',
    #     color='red'
    # )
    # plt.savefig('speed_comparison_plot_0718.pdf')
    # plt.show()