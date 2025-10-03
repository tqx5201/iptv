#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取江苏OTT频道列表与当天EPG，生成 xmltv.xml.gz
"""
import gzip
import json
import sys
import time
from datetime import datetime, timezone, timedelta
import re
import requests
from dateutil.parser import parse as dtparse

# ========== 配置 ==========
CHANNEL_LIST_URL = (
    "http://looktvepg.jsa.bcs.ottcn.com:8080/"
    "ysten-lvoms-epg/epg/getChannelIndexs.shtml?templateId=02520"
)
CHANNEL_LIST_URL2 = "http://looktvepg.jsa.bcs.ottcn.com:8080/ysten-lvoms-epg/epg/getChannelIndexs.shtml?deviceGroupId=1697"
EPG_URL = (
    "http://lvpepg.uni.jsa.bcs.ottcn.com:8080/"
    "cms-lvp-epg/lvps/getAllProgramlist"
)
DATE_STR = "20251003"          # 需要抓取的日期
ABILITY_PAYLOAD = {            # 固定请求体
    "deviceGroupIds": ["5362"],
    "districtCode": "320900"
}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# ==========================


def indent_line(match):
    tag = match.group(1)          # channel 或 programme
    body = match.group(2)
    return f"{'    ' if tag == 'channel' else '  '}<{tag}{body}</{tag}>"
def ts_to_xmltv(t: int) -> str:
    """Unix 时间戳 -> XMLTV 时间串 20251003120000 +0800"""
    dt = datetime.fromtimestamp(t, tz=timezone.utc).astimezone(
        timezone(timedelta(hours=8)))
    return dt.strftime('%Y%m%d%H%M%S %z')

def get_channels(test: bool = True) -> dict:
    """返回 dict: uuid -> channelName"""
    print(">>> 正在抓取频道列表…")
    r = requests.get(CHANNEL_LIST_URL2, headers={"User-Agent": UA}, timeout=15)
    r.raise_for_status()
    data = r.json()
    ch_map = {}
    #for v in data.values():
    for idx, v in enumerate(data.values(), 1):
        ch_map[v["uuid"]] = v["channelName"]
        if test and idx == 5:  # 测试模式只拿 5 个
            break

    print(f">>> 共获取 {len(ch_map)} 个频道")
    return ch_map


def fetch_epg(uuid: str) -> list:
    """返回该 uuid 当天所有节目列表"""
    params = {
        "abilityString": json.dumps(ABILITY_PAYLOAD, separators=(",", ":")),
        "startDate": DATE_STR,
        "endDate": DATE_STR,
        "uuid": uuid
    }
    r = requests.get(EPG_URL, params=params, headers={"User-Agent": UA}, timeout=15)
    r.raise_for_status()
    return r.json()


def build_xmltv(ch_map: dict, epg_cache: dict) -> str:
    """生成 XMLTV 字符串"""
    from xml.etree.ElementTree import Element, SubElement, tostring

    tv = Element("tv", attrib={"generator-info-name": "js_ottdaily_grabber"})

    # 0. 预过滤：删掉没节目的频道
    epg_cache = {uuid: data for uuid, data in epg_cache.items() if data.get('content')}
    ch_map = {uuid: name for uuid, name in ch_map.items() if uuid in epg_cache}

    # 1. 写入频道信息
    for uuid, name in ch_map.items():
        chan = SubElement(tv, "channel", id=uuid)
        SubElement(chan, "display-name").text = name

    # 2. 写入节目信息
    for uuid, programmes in epg_cache.items():
        for prog in programmes['content'][0]['programs']:
            start_str = prog["startTime"]  # 格式：20251003000000 +0800
            end_str = prog["endTime"]
            title = prog.get("programName", "未知节目")
            #print(start_str)

            SubElement(tv, "programme", {
                "start": ts_to_xmltv(start_str),
                "stop": ts_to_xmltv(end_str),
                "channel": uuid
            }).text = title
    #print(tv)
    # 美化
    from xml.etree.ElementTree import tostring
    from xml.dom.minidom import parseString
    #rough = tostring(tv, encoding="utf-8")

    # 生成紧凑单行 XML
    rough = tostring(tv, encoding="utf-8").decode("utf-8")
    # 可选：把单标签也保持紧凑
    rough = rough.replace("><", ">\n<")

    # 3. 把 channel 内部压成一行：去掉 </channel> 前的换行
    rough = re.sub(r"(<channel[^>]*>)\s+(.*?)\s+(</channel>)", r"\1\2\3", rough, flags=re.S)

    # 4. 同理处理 programme
    rough = re.sub(r"(<programme[^>]*>)\s+(.*?)\s+(</programme>)", r"\1\2\3", rough, flags=re.S)

    # 2. 给 <channel 这一行加 4 空格（前面可能已有换行）
    rough = re.sub(r"(^|\n)(<channel)", r"\1    \2", rough)
    rough = re.sub(r"(^|\n)(<programme)", r"\1    \2", rough)

    return rough

    #reparsed = parseString(rough)
    #return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def main():
    ch_map = get_channels()
    epg_cache = {}

    total = len(ch_map)
    for idx, (uuid, name) in enumerate(ch_map.items(), 1):
        print(f"[{idx:>3}/{total}] 抓取 {name}  …", end="", flush=True)
        try:
            epg = fetch_epg(uuid)
            epg_cache[uuid] = epg
            print(" OK")
        except Exception as e:
            print(f" 失败: {e}")
        # 简单限速
        time.sleep(0.2)

    print(">>> 正在生成 e.xml …")
    xml_str = build_xmltv(ch_map, epg_cache)

    # 同时写 e.xml 和 e.xml.gz
    with open("e.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(">>> 正在压缩为 e.xml.gz …")
    with gzip.open("e.xml.gz", "wb") as f:
        f.write(xml_str.encode("utf-8"))

    print(">>> 完成！已保存 e.xml.gz")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled by user")
