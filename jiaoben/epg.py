import xml.etree.ElementTree as ET
import requests

def download_xmltv(url):
    """
    从网址下载XMLTV文件并解析为ElementTree对象。
    
    :param url: XMLTV文件的网址
    :return: ElementTree对象
    """
    try:
        response = requests.get(url,timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"下载文件 {url} 时出错: {e}")
        return None


def extract_channels_from_url(url):
    """
    从指定的网络地址获取内容，并提取频道名称。
    去除空行和含有"#genre#"的行。

    :param url: 网络地址
    :return: 频道名称列表
    """
    try:
        # 发送请求获取内容
        response = requests.get(url)
        response.encoding = 'utf-8'  # 确保正确处理文本编码

        # 初始化一个空列表来存储频道名称
        channels = []

        # 按行处理内容
        for line in response.text.splitlines():
            # 去除行首和行尾的空白字符
            line = line.strip()
            # 判断是否为空行或包含"#genre#"，如果不是，则添加到频道列表中
            if line and "#genre#" not in line:
                # 假设频道名称在逗号之前
                channel_name = line.split(',')[0]
                channels.append(channel_name)
        
        print("获取我的频道成功")
        return channels

    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return []


def format_programme(programme):
    """
    格式化 programme 元素，并返回一个新的 programme 元素。

    :param programme: ElementTree.Element 对象，表示原始的 programme 元素
    :return: ElementTree.Element 对象，表示格式化后的新 programme 元素
    """
    # 创建一个新的 programme 元素
    new_programme = ET.Element('programme')

    # 获取原始的 start 和 stop 属性，并去掉时区偏移量
    start = programme.get('start', '').split()[0]  # 只取前面部分
    stop = programme.get('stop', '').split()[0]   # 只取前面部分

    # 转换 start 时间
    if start:
        new_start = start + ' +0800'
        new_programme.set('start', new_start)

    # 转换 stop 时间
    if stop:
        new_stop = stop + ' +0800'
        new_programme.set('stop', new_stop)

    # 添加 channel 属性
    new_programme.set('channel', programme.get('channel', ''))

    # 添加 title 子元素
    title = programme.find('title')
    new_title = ET.SubElement(new_programme, 'title')
    if title is not None and title.text is not None:
        new_title.text = title.text.strip()
    else:
        new_title.text = '未知标题'
        
    """
    # 添加 desc 子元素
    desc = programme.find('desc')
    new_desc = ET.SubElement(new_programme, 'desc')
    if desc is not None and desc.text is not None:
        new_desc.text = desc.text.strip()
    else:
        new_desc.text = '无描述'
    """
    
    return new_programme



def merge_xmltv_files(input_urls,output_file, display_name_file, channel_url):
    # 收集我需要的名称
    channels = extract_channels_from_url(channel_url)
    #print(channels)
    """
    合并多个XMLTV文件到一个文件中，并将唯一的display-name写入文本文件。
    
    :param output_file: 输出文件路径
    :param display_name_file: 保存唯一display-name的文本文件路径
    :param input_urls: 输入文件网址列表
    """
    if not input_urls:
        print("没有输入网址。")
        return

    # 初始化根元素
    root = ET.Element('tv', attrib={'generator-info-name': 'My EPG Generator', 'generator-info': 'TXPP'})

    # 用于存储display-name的集合，避免重复
    display_names = set()

    # 用于存储programme的集合，避免重复
    programme_keys = set()

    # 遍历所有输入文件
    for url in input_urls:
        print(f"正在获取{url}的数据")
        temp_tree = download_xmltv(url)
        if temp_tree is None:
            continue

        # 合并<channel>元素
        for channel in temp_tree.findall('channel'):
            for display_name in channel.findall('display-name'):
                if display_name.text and display_name.text in channels and display_name.text not in display_names:
                    display_names.add(display_name.text)
                    existing_channel = next((c for c in root.findall('channel') if c.find('display-name').text == display_name.text), None)
                    if existing_channel is None:
                        root.append(channel)
                    else:
                        # 合并其他信息，例如 icon 和 url
                        for child in channel:
                            if child.tag not in [c.tag for c in existing_channel]:
                                existing_channel.append(child)

        # 合并<programme>元素
        for programme in temp_tree.findall('programme'):
            programme_key = (programme.get('start'), programme.get('channel'))
            if programme_key and programme_key not in programme_keys:
                # 获取programme对应的channel的display-name
                channel_display_name = next((c.find('display-name').text for c in root.findall('channel') if c.get('id') == programme.get('channel')), None)
                # 判断channel的display-name是否在channels中
                if channel_display_name in channels:
                    programme_keys.add(programme_key)
                    root.append(format_programme(programme))

    # 写入到输出文件
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"合并完成，结果已保存到 {output_file}")

    # 将唯一的display-name写入文本文件
    with open(display_name_file, 'w', encoding='utf-8') as f:
        for display_name in sorted(display_names):
            f.write(display_name + '\n')
    print(f"唯一的display-name已保存到 {display_name_file}")


# 示例调用
channel_url = 'https://remix.7259.dpdns.org/list/yd.txt'


# 定义输入网址和输出文件路径
    
input_urls = [
    "http://epg.51zmt.top:8000/e.xml",
    #"https://e.erw.cc/e.xml",
    #"https://raw.bgithub.xyz/fanmingming/live/main/e.xml",
    "https://assets.livednow.com/epg.xml",
    "https://epg.pw/xmltv/epg_CN.xml",
    "https://epg.pw/xmltv/epg_HK.xml",
    "https://epg.pw/xmltv/epg_TW.xml"
]
output_file = "e.xml"
display_name_file = "display_names.txt"

# 调用函数
merge_xmltv_files(input_urls,output_file, display_name_file, channel_url)
