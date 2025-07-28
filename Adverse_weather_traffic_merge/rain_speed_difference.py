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

normal_weather = read_shapefile("real_traffic_situation/Normal.shp")
rainy_weather = read_shapefile("real_traffic_situation/Rain.shp")

normal_weather = normal_weather[normal_weather['status'] != 0]
rainy_weather = rainy_weather[rainy_weather['status'] != 0]
# print(rainy_weather)

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
    print("Warning: No common segments!")
else:
    print(f"{len(merged_df)} common segments (except status 0)")
    merged_df['speed_diff_percent'] = (
        (merged_df['rainy_speed'] - merged_df['normal_speed']) / 
        (merged_df['normal_speed'] + 1) * 100
    )
    merged_df.to_csv('actual_speed_variation.csv', index=False) 
    bins = range(-100, 30, 10) 
    labels = [f"{i}%-{i+10}%" for i in range(-10, 110, 10)]
    plt.figure(figsize=(12, 6))
    n, bins, patches = plt.hist(
        merged_df['speed_diff_percent'],
        bins=bins,
        edgecolor='black',
        alpha=0.7,
        color='skyblue',
        density=True  # 显示频数而非频率
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