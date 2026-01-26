import xml.etree.ElementTree as ET
import requests
import gzip
import io
import os

def download_xmltv(url):
    """
    从网址下载XMLTV文件并解析为ElementTree对象。
    如果文件是 gzip 压缩的，则解压后再解析。
    
    :param url: XMLTV文件的网址
    :return: ElementTree对象
    """
    url = url.replace('bgithub.xyz','githubusercontent.com')
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功

        if url.endswith('.gz'):
            # 如果是 gzip 文件，解压内容
            with gzip.open(io.BytesIO(response.content), 'rt', encoding='utf-8') as f:
                content = f.read()
        else:
            # 如果不是 gzip 文件，直接使用内容
            content = response.content.decode('utf-8')

        return ET.fromstring(content)
    except requests.RequestException as e:
        print(f"下载文件 {url} 时出错: {e}")
    except ET.ParseError as e:
        print(f"解析文件 {url} 时出错: {e}")
    return None

def extract_channels_from_url(url):
    """
    从指定的网络地址获取内容，并提取频道名称。
    去除空行和含有"#genre#"的行。

    :param url: 网络地址
    :return: 频道名称列表
    """
    try:
        response = requests.get(url)
        response.encoding = 'utf-8'  # 确保正确处理文本编码

        channels = []
        for line in response.text.splitlines():
            line = line.strip()
            if line and "#genre#" not in line:
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
    new_programme = ET.Element('programme')

    start = programme.get('start', '').split()[0]  # 只取前面部分
    stop = programme.get('stop', '').split()[0]   # 只取前面部分

    new_start = start + ' +0800'
    new_stop = stop + ' +0800'

    new_programme.set('start', new_start)
    new_programme.set('stop', new_stop)
    new_programme.set('channel', programme.get('channel', ''))

    title = programme.find('title')
    new_title = ET.SubElement(new_programme, 'title')
    new_title.text = title.text.strip() if title is not None and title.text is not None else '未知标题'
    """
    desc = programme.find('desc')
    new_desc = ET.SubElement(new_programme, 'desc')
    new_desc.text = desc.text.strip() if desc is not None and desc.text is not None else '无描述'
    """
    return new_programme


def format_channel(channel, matched_name):
    """
    格式化 channel 元素，并返回一个新的 channel 元素。
    只提取 display-name，并将 display-name 替换为 matched_name。
    注释掉 icon 和 url 的处理部分。

    :param channel: ElementTree.Element 对象，表示原始的 channel 元素
    :param matched_name: 匹配到的频道名称
    :return: ElementTree.Element 对象，表示格式化后的新 channel 元素
    """
    new_channel = ET.Element('channel')
    new_channel.set('id', channel.get('id', ''))

    # 替换 display-name 为 matched_name
    new_display_name = ET.SubElement(new_channel, 'display-name')
    new_display_name.text = matched_name

    """
    # 注释掉 icon 的处理部分
    for icon in channel.findall('icon'):
        new_icon = ET.SubElement(new_channel, 'icon')
        new_icon.set('src', icon.get('src', ''))
    
    # 注释掉 url 的处理部分
    for url in channel.findall('url'):
        new_url = ET.SubElement(new_channel, 'url')
        new_url.text = url.text.strip() if url.text is not None else ''
    """

    return new_channel


def check_display_name(display_name_text, channels):
    """
    检查 display-name.text 或其经过格式化后的值是否在 channels 列表中。
    
    :param display_name_text: 原始的 display-name.text
    :param channels: 频道名称列表
    :return: 匹配的频道名称，如果匹配成功；否则返回 None
    """
    # 检查原始值是否在 channels 中
    if display_name_text in channels:
        return display_name_text

    # 检查“CCTV”替换为"CCTV-"后的值是否在 channels 中
    CCTV_name = display_name_text.replace('CCTV', 'CCTV-')
    if CCTV_name in channels:
        return CCTV_name
        
    # 如果包含空格，取空格前的内容
    if ' ' in display_name_text:
        space_split_name = display_name_text.split(' ')[0]
        if space_split_name in channels:
            return space_split_name
    
    # 检查加上 "HD" 后缀的值是否在 channels 中
    hd_name = display_name_text + ' HD'
    if hd_name in channels:
        return hd_name
        
    # 检查删除“台”字后的值是否在 channels 中
    no_hd_name = display_name_text.replace('HD', '')
    if no_hd_name in channels:
        return no_hd_name
        
    # 检查删除“台”字后的值是否在 channels 中
    no_tai_name = display_name_text.replace('台', '')
    if no_tai_name in channels:
        return no_tai_name
    
    # 检查加上“台”字后的值是否在 channels 中
    tai_name = display_name_text + '台'
    if tai_name in channels:
        return tai_name
    
    # 检查加上“台”字和“HD”后缀的值是否在 channels 中
    tai_hd_name = display_name_text + '台HD'
    if tai_hd_name in channels:
        return tai_hd_name
    
    # 如果都不匹配，返回 None
    return None

def indent(elem, level=0):
    """
    为 XML 元素添加缩进和换行，使其更易于阅读。
    
    :param elem: ElementTree.Element 对象
    :param level: 当前缩进级别
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def merge_xmltv_files(input_urls, output_file, display_name_file, matched_channel_file, unmatched_channel_file, channel_url):
    """
    合并多个XMLTV文件到一个文件中，并将唯一的display-name写入文本文件。
    
    :param input_urls: 输入文件网址列表
    :param output_file: 输出文件路径
    :param display_name_file: 保存唯一display-name的文本文件路径
    :param matched_channel_file: 保存匹配到的channel的文本文件路径
    :param unmatched_channel_file: 保存没有匹配到的channel的文本文件路径
    :param channel_url: 频道列表的网址
    """
    if not input_urls:
        print("没有输入网址。")
        return

    channels = extract_channels_from_url(channel_url)
    if not channels:
        print("没有获取到有效的频道列表。")
        return

    root = ET.Element('tv', attrib={'generator-info-name': 'My EPG Generator', 'generator-info-user': '天仙婆婆'})
    display_names = set()
    programme_keys = set()
    matched_channels = set()
    unmatched_channels = set()
    channel_map = {}  # 用于存储旧 channel-id 到新 channel-id 的映射
    channel_display_name_map = {}  # 用于存储 display-name 到新 channel-id 的映射

    for url in input_urls:
        print(f"正在获取 {url} 的数据")
        temp_tree = download_xmltv(url)
        if temp_tree is None:
            continue

        for channel in temp_tree.findall('channel'):
            for display_name in channel.findall('display-name'):
                display_names.add(display_name.text.strip())  # 添加到 display_names 集合
                matched_name = check_display_name(display_name.text, channels)
                if matched_name:
                    if matched_name not in channel_display_name_map:
                        new_channel = format_channel(channel,matched_name)
                        root.append(new_channel)
                        new_channel_id = new_channel.get('id')
                        channel_display_name_map[matched_name] = new_channel_id
                        matched_channels.add(matched_name)
                    else:
                        unmatched_channels.add(display_name.text)
                else:
                    unmatched_channels.add(display_name.text)

        for programme in temp_tree.findall('programme'):
            programme_key = (programme.get('start'), programme.get('channel'))
            if programme_key and programme_key not in programme_keys:
                channel_display_name = next((c.find('display-name').text for c in root.findall('channel') if c.get('id') == programme.get('channel')), None)
                if channel_display_name in channels:
                    programme_keys.add(programme_key)
                    new_programme = format_programme(programme)
                    new_programme.set('channel', channel_display_name_map[channel_display_name])
                    root.append(new_programme)

    # 重置 channel-id 并更新 programme 的 channel 属性
    channel_id_counter = 1
    for channel in root.findall('channel'):
        old_channel_id = channel.get('id')
        new_channel_id = str(channel_id_counter)
        channel.set('id', new_channel_id)
        channel_map[old_channel_id] = new_channel_id
        channel_id_counter += 1

    # 更新 programme 的 channel 属性
    for programme in root.findall('programme'):
        old_channel_id = programme.get('channel')
        if old_channel_id in channel_map:
            programme.set('channel', channel_map[old_channel_id])

    # 重新排序 root 的子元素，确保 channel 元素在 programme 元素之前
    root[:] = sorted(root, key=lambda child: child.tag)

    # 为 XML 元素添加缩进和换行
    indent(root)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 写入到输出文件
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"合并完成，结果已保存到 {output_file}")

    # 生成 gzip 文件
    with open(output_file, 'rb') as f_in:
        with gzip.open(output_file + '.gz', 'wb') as f_out:
            f_out.writelines(f_in)
    print(f"压缩文件已保存到 {output_file}.gz")

    # 将所有的display-name写入文本文件
    with open(display_name_file, 'w', encoding='utf-8') as f:
        for display_name in sorted(display_names):
            f.write(display_name + '\n')
    print(f"所有的display-name已保存到 {display_name_file}")

    # 将匹配到的channel写入文本文件
    with open(matched_channel_file, 'w', encoding='utf-8') as f:
        for display_name in sorted(matched_channels):
            f.write(display_name + '\n')
    print(f"匹配到的channel已保存到 {matched_channel_file}")

    # 将没有匹配到的channel写入文本文件
    with open(unmatched_channel_file, 'w', encoding='utf-8') as f:
        for display_name in sorted(unmatched_channels):
            f.write(display_name + '\n')
    print(f"没有匹配到的channel已保存到 {unmatched_channel_file}")




# 示例调用
# 我的列表txt
#channel_url = 'https://remix.7259.dpdns.org/list/yd.txt'
channel_url = 'https://7259.cloudns.ch/iptv/source/list_yd.txt'
# 定义输入网址和输出文件路径
    
input_urls = [
    "https://raw.bgithub.xyz/tqx5201/iptv/main/jiaoben/epg_cache/epg_1905.xml",
    "https://raw.bgithub.xyz/tqx5201/iptv/main/jiaoben/epg_cache/epg_migu.xml",
    
    "https://raw.bgithub.xyz/kuke31/xmlgz/main/e.xml.gz",
    "http://epg.51zmt.top:8000/e.xml",
    #"https://e.erw.cc/e.xml",
    "https://epg.112114.xyz/pp.xml",
    "https://assets.livednow.com/epg.xml",
    "https://epg.pw/xmltv/epg_TW.xml.gz",
    "https://epg.pw/xmltv/epg_HK.xml.gz",
    "https://epg.pw/xmltv/epg_CN.xml.gz"
    
    
]
output_file = "epg/e.xml"
display_name_file = "epg/display_names.txt"
matched_channel_file = "epg/matched_channels.txt"
unmatched_channel_file = "epg/unmatched_channels.txt"


merge_xmltv_files(input_urls, output_file, display_name_file, matched_channel_file, unmatched_channel_file, channel_url)
