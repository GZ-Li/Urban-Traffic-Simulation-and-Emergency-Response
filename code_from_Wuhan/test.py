# import pdb
# pdb.set_trace()

from collections import defaultdict
from re import *
from typing import TypeVar
import json


# import stringcase
from google.protobuf import json_format
from google.protobuf.message import Message
# from pymongo.collection import Collection
# import pymongo
from pycityproto.city.map.v2 import map_pb2
# from pycityproto.city.person.v2 import person_pb2
from pycityproto.city.person.v2.person_pb2 import Persons, Person

# MONGO_URI = "mongodb://root:****@172.16.40.166:27017"  # MongoDB 连接URI
# MONGO_DB = "tsingroc"                                   # 数据库名称
# MONGO_COLL = "map_pku_wuhan_demo_0408"                 # 集合名称
# GEOJSON_FILE = "map.geojson"                           # 输出文件路径

def pb2json(pb: Message):
    """
    Convert a protobuf message to a JSON string.

    Args:
    - pb: The protobuf message to be converted.

    Returns:
    - The JSON string.
    """
    return json_format.MessageToJson(
        pb,
        including_default_value_fields=True,
        preserving_proto_field_name=True,
        use_integers_for_enums=True,
    )
 
    
T = TypeVar("T", bound=Message)
def json2pb(json: str, pb: T) -> T:
    """
    Convert a JSON string to a protobuf message.

    Args:
    - json: The JSON string to be converted.
    - pb: The protobuf message to be filled.

    Returns:
    - The protobuf message.
    """
    return json_format.Parse(json, pb, ignore_unknown_fields=True)


def dict2pb(d: dict, pb: T) -> T:
    """
    Convert a Python dictionary to a protobuf message.

    Args:
    - d: The Python dict to be converted.
    - pb: The protobuf message to be filled.

    Returns:
    - The protobuf message.
    """
    return json_format.ParseDict(d, pb, ignore_unknown_fields=True)

# map = map_pb2.Map()
# with open("E:\\Traffic_Simulation\\code_from_Wuhan\\map_07311617.pb", "rb") as f:
#     map.ParseFromString(f.read())
# map2 = pb2json(map)
# with open("map_test_1624.json", "w", encoding="utf-8") as f:
#     json.dump(json.loads(map2), f, indent=2, ensure_ascii=False)


# with open("E:\\Traffic_Simulation\\code_from_Wuhan\\tsingroc.person_test_20250724_1015cc.json", "r", encoding="utf-8") as f:
#     json_data = f.read()
# person2 = json2pb(json_data, person_pb2.Person())
# with open("test.pb", "wb") as f:
#     f.write(person2.SerializeToString())


# with open("E:\\Traffic_Simulation\\code_from_Wuhan\\test_single_vehicle_od.json", "r", encoding="utf-8") as f:
#     json_data = f.read()
# pb = json2pb(json_data, Persons())

# # print(type(pb))

# with open("test_person.pb", "wb") as f:
#     f.write(pb.SerializeToString())

person = Persons()
with open("test_person_08011120.pb", "rb") as f:
    person.ParseFromString(f.read())
person2 = pb2json(person)
with open("test_person_08011120.json", "w", encoding="utf-8") as f:
    json.dump(json.loads(person2), f, indent=2, ensure_ascii=False)