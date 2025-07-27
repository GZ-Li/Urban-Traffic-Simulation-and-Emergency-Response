import json
import numpy as np

# 读取 JSON 文件
with open('E:\\Traffic_Simulation\\Adverse_weather_traffic\\simulation_results\\param_time_accuracy_initial_0720_test_scale.json', 'r') as file:
    data = json.load(file)

# 按准确率降序排序（返回列表，元素是 (参数组合, 准确率) 元组）
sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)

# 输出前10个
print("准确率排名前10的参数组合：")
for i, (params, accuracy) in enumerate(sorted_data[:10], 1):
    print(f"{i}. {params}: {accuracy}")
    

all_accuracies = [accuracy for _, accuracy in data.items()]
    
# 计算统计指标
average_accuracy = np.mean(all_accuracies)
median_accuracy = np.median(all_accuracies)
min_accuracy = min(all_accuracies)
max_accuracy = max(all_accuracies)

# 输出统计摘要
print("\n准确率统计摘要：")
print(f"参数组合总数: {len(data)}")
print(f"平均准确率: {average_accuracy:.4f}")
print(f"中位数准确率: {median_accuracy:.4f}")
print(f"最高准确率: {max_accuracy:.4f}")
print(f"最低准确率: {min_accuracy:.4f}")