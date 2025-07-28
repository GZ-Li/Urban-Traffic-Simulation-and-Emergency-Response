import xml.etree.ElementTree as ET

# 输入和输出文件
input_route_file = "E:\\Traffic_Simulation\\snowplow_routing\\rou\\toy_origin.rou.xml"
output_route_file = "E:\\Traffic_Simulation\\snowplow_routing\\rou\\toy.rou.xml"

# 定义统一的 vType 属性
vtype_attrs = {
    "id": "snow_car",
    "accel": "1.0",      # 加速度 (m/s²)
    "decel": "2.0",      # 减速度 (m/s²)
    "maxSpeed": "10",    # 最大速度 (m/s)
    "minGap": "5",     # 最小车距 (m)
}

def add_vtype_to_routes(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    existing_vtypes = [elem for elem in root if elem.tag == "vType"]
    if not existing_vtypes:
        vtype_elem = ET.Element("vType", attrib=vtype_attrs)
        root.insert(0, vtype_elem) 
    for vehicle in root.findall("vehicle"):
        vehicle.set("type", "snow_car")
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"已生成新路由文件: {output_route_file}")

add_vtype_to_routes(input_route_file, output_route_file)