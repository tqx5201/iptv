import hashlib
import time
import requests
from datetime import datetime
import pytz
from xml.etree import ElementTree as ET
from xml.dom import minidom

# 配置参数
SECRET_KEY = "6ca114a836ac7d73"
LIVE_API_URL = "https://pubmod.hntv.tv/program/getAuth/live/class/program/11"
VOD_API_BASE = "https://pubmod.hntv.tv/program/getAuth/vod/originStream/program/"
PLAY_URL_TEMPLATE = "http://A/PLTV/ku9/js/dxxw.js?id={cid}"
TIMEZONE = pytz.timezone("Asia/Shanghai")

# 多组名称替换映射
name_map = {
    "新闻频道": "河南新闻",
    "都市频道": "河南都市",
    "民生频道": "河南民生",
    "法治频道": "河南法治",
    "公共频道": "河南公共",
    "河南乡村频道": "河南乡村",
    "电视剧频道": "河南电视剧"
}




# 动态获取频道列表
def fetch_channel_list():
    """获取频道基础信息列表"""
    timestamp = int(time.time())
    signature = hashlib.sha256(f"{SECRET_KEY}{timestamp}".encode()).hexdigest()
    
    try:
        response = requests.get(
            LIVE_API_URL,
            headers={'timestamp': str(timestamp), 'sign': signature},
            timeout=10
        )
        response.raise_for_status()
        return [{"cid": str(item["cid"]), "name": item["name"]} for item in response.json()]
    except Exception as e:
        print(f"频道列表获取失败: {str(e)}")
        exit(1)

def generate_txt(channels):
    """生成直播源文件"""
    with open("./jiaoben/epg_cache/dxxw.txt", "w", encoding="utf-8") as f:
        for chan in channels:
            f.write(f"{chan['name']},{PLAY_URL_TEMPLATE.format(cid=chan['cid'])}\n")

# 原有 EPG 生成函数（保持完全不变）
def generate_signature():
    timestamp = int(time.time())
    return {
        'timestamp': str(timestamp),
        'sign': hashlib.sha256(f"{SECRET_KEY}{timestamp}".encode()).hexdigest()
    }

def fetch_channel_data(channel_id):
    headers = generate_signature()
    try:
        response = requests.get(f"{VOD_API_BASE}{channel_id}/{headers['timestamp']}", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "name": name_map.get(data["name"], data["name"]),
            "programs": [{
                "beginTime": int(p["beginTime"]),
                "endTime": int(p["endTime"]),
                "title": p["title"]
            } for p in data["programs"]]
        }
    except Exception as e:
        print(f"频道 {channel_id} 节目数据获取失败: {str(e)}")
        return None

def convert_timestamp(timestamp):
    dt = datetime.fromtimestamp(timestamp, TIMEZONE)
    return dt.strftime("%Y%m%d%H%M%S %z")

def generate_epg(channel_ids):
    tv = ET.Element("tv", attrib={
        "info-name": "by spark",
        "info-url": "https://epg.112114.xyz"
    })
    
    for cid in channel_ids:
        data = fetch_channel_data(cid)
        if not data: 
            continue

        # 修正频道定义部分
        channel_elem = ET.SubElement(tv, "channel", id=cid)
        display_name = ET.SubElement(channel_elem, "display-name", lang="zh")
        display_name.text = data['name']

        # 修正节目单部分
        for program in data["programs"]:
            programme = ET.SubElement(tv, "programme", {
                "channel": cid,
                "start": convert_timestamp(program["beginTime"]),
                "stop": convert_timestamp(program["endTime"])
            })
            title = ET.SubElement(programme, "title", lang="zh")
            title.text = program["title"]
    
    with open("./jiaoben/epg_cache/epg_dxxw.xml", "w", encoding="utf-8") as f:
        f.write(minidom.parseString(ET.tostring(tv)).toprettyxml(indent="  "))


if __name__ == "__main__":
    # 第一步：获取频道列表并生成 tv.txt
    channels = fetch_channel_list()
    
    # 多组名称替换映射
    name_map = {
         "新闻频道": "河南新闻",
         "都市频道": "河南都市",
         "民生频道": "河南民生",
         "法治频道": "河南法治",
         "公共频道": "河南公共",
         "河南乡村频道": "河南乡村",
         "电视剧频道": "河南电视剧"
     }
    
    # 就地修改data里每个字典的name值
    for d in channels:
        d["name"] = name_map.get(d["name"], d["name"])

    # 替换完成后，data本身就是更新好的新data，直接使用即可
    print(channels)


    generate_txt(channels)
    
    # 第二步：提取 CID 列表用于 EPG 生成
    CHANNEL_IDS = [chan["cid"] for chan in channels]
    
    # 第三步：生成 EPG（原有逻辑完全不变）
    generate_epg(CHANNEL_IDS)
    
    print("文件生成成功")
    print("EPG 文件: dxxw.xml")
    print("直播源文件: dxxw.txt")
