import xml.etree.ElementTree as ET
import requests

def download_xmltv(url):
    """
    从网址下载XMLTV文件并解析为ElementTree对象。
    
    :param url: XMLTV文件的网址
    :return: ElementTree对象
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"下载文件 {url} 时出错: {e}")
        return None

def merge_xmltv_files(output_file, channel_id_file, input_urls):
    """
    合并多个XMLTV文件到一个文件中，并将channel ID写入文本文件。
    
    :param output_file: 输出文件路径
    :param channel_id_file: 保存channel ID的文本文件路径
    :param input_urls: 输入文件网址列表
    """
    # 下载并解析第一个文件，作为基础结构
    if not input_urls:
        print("没有输入网址。")
        return
    
    first_url = input_urls[0]
    first_tree = download_xmltv(first_url)
    if first_tree is None:
        print("无法下载或解析第一个文件。")
        return
    
    root = first_tree
    
    # 用于存储channel ID和programme的集合，避免重复
    channel_ids = set()
    programme_keys = set()
    
    # 从第一个文件中提取channel ID和programme
    for channel in root.findall('channel'):
        channel_id = channel.get('id')
        if channel_id:
            channel_ids.add(channel_id)
    
    for programme in root.findall('programme'):
        programme_key = (programme.get('start'), programme.get('channel'))
        if programme_key:
            programme_keys.add(programme_key)
    
    # 遍历其余的网址并合并
    for url in input_urls[1:]:
        temp_tree = download_xmltv(url)
        if temp_tree is None:
            continue
        
        # 合并<channel>元素
        for channel in temp_tree.findall('channel'):
            channel_id = channel.get('id')
            if channel_id and channel_id not in channel_ids:
                channel_ids.add(channel_id)
                root.append(channel)
        
        # 合并<programme>元素
        for programme in temp_tree.findall('programme'):
            programme_key = (programme.get('start'), programme.get('channel'))
            if programme_key and programme_key not in programme_keys:
                programme_keys.add(programme_key)
                root.append(programme)
    
    # 写入到输出文件
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"合并完成，结果已保存到 {output_file}")
    
    # 将channel ID写入文本文件
    with open(channel_id_file, 'w', encoding='utf-8') as f:
        for channel_id in sorted(channel_ids):
            f.write(channel_id + '\n')
    print(f"Channel ID已保存到 {channel_id_file}")

# 定义输入网址和输出文件路径

epg_urls = [
    "http://epg.51zmt.top:8000/e.xml",
    #"https://e.erw.cc/e.xml",
    "https://ghfast.top/https://raw.githubusercontent.com/fanmingming/live/main/e.xml",
    #"https://assets.livednow.com/epg.xml",
    #"https://epg.pw/xmltv/epg_CN.xml",
    #"https://epg.pw/xmltv/epg_HK.xml",
    "https://epg.pw/xmltv/epg_TW.xml"
]
output_file = "output.xml"
channel_id_file = "channel_ids.txt"

# 调用函数
merge_xmltv_files(output_file, channel_id_file, epg_urls)
