import xml.etree.ElementTree as ET
import requests
import gzip
import io
import os

# 全局请求头，避免被源地址拦截（模拟浏览器）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def download_xmltv(url):
    """从网址下载XMLTV文件并解析为ElementTree对象，支持gzip解压"""
    url = url.replace('bgithub.xyz','githubusercontent.com')
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        if url.endswith('.gz'):
            with gzip.open(io.BytesIO(response.content), 'rt', encoding='utf-8') as f:
                content = f.read()
        else:
            content = response.content.decode('utf-8', errors='ignore')  # 忽略编码错误

        return ET.fromstring(content)
    except requests.RequestException as e:
        print(f"下载文件 {url} 时出错: {e}")
    except ET.ParseError as e:
        print(f"解析文件 {url} 时出错: {e}")
    return None

def extract_channels_from_url(url):
    """从网络地址提取自定义频道列表，过滤空行和#genre#，设置超时"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'  # 强制utf-8编码

        channels = []
        for line in response.text.splitlines():
            line = line.strip()
            if line and "#genre#" not in line:
                channel_name = line.split(',')[0].strip()  # 增加strip，避免首尾空格
                channels.append(channel_name)
        
        print("获取我的频道成功，共{}个频道".format(len(channels)))
        return channels

    except requests.RequestException as e:
        print(f"请求频道列表失败: {e}")
        return []

def format_programme(programme):
    """格式化programme节点，补全时区，清洗标题"""
    new_programme = ET.Element('programme')

    start = programme.get('start', '').split()[0]
    stop = programme.get('stop', '').split()[0]

    new_start = start + ' +0800' if start else ''
    new_stop = stop + ' +0800' if stop else ''

    new_programme.set('start', new_start)
    new_programme.set('stop', new_stop)
    new_programme.set('channel', programme.get('channel', ''))

    title = programme.find('title')
    new_title = ET.SubElement(new_programme, 'title')
    new_title.text = title.text.strip() if (title and title.text) else '未知标题'
    return new_programme

def format_channel(channel, matched_name):
    """格式化channel节点，仅保留id和匹配后的display-name"""
    new_channel = ET.Element('channel')
    new_channel.set('id', channel.get('id', ''))

    new_display_name = ET.SubElement(new_channel, 'display-name')
    new_display_name.text = matched_name
    return new_channel

def check_display_name(display_name_text, channels):
    """智能匹配频道名，处理格式差异（CCTV/HD/台字等）"""
    if not display_name_text or not channels:
        return None
    display_name_text = display_name_text.strip()  # 清洗原始名空格

    # 匹配规则按优先级执行
    match_rules = [
        display_name_text,  # 原始名
        display_name_text.replace('CCTV', 'CCTV-'),  # CCTV→CCTV-
        display_name_text.split(' ')[0],  # 取空格前
        display_name_text + ' HD',  # 加HD
        display_name_text.replace('HD', ''),  # 删HD
        display_name_text.replace('台', ''),  # 删台
        display_name_text + '台',  # 加台
        display_name_text + '台HD'  # 加台+HD
    ]
    # 遍历规则，返回第一个匹配的频道名
    for name in match_rules:
        if name.strip() in channels:
            return name.strip()
    return None

def indent(elem, level=0):
    """为XML节点添加缩进，让文件可读"""
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
    """主函数：合并、筛选、格式化XMLTV，生成最终文件"""
    if not input_urls:
        print("没有输入XMLTV网址，退出")
        return

    # 1. 提取自定义频道列表
    custom_channels = extract_channels_from_url(channel_url)
    if not custom_channels:
        print("未获取到有效自定义频道列表，退出")
        return

    # 初始化全局变量
    root = ET.Element('tv', attrib={'generator-info-name': 'My EPG Generator', 'generator-info-user': '天仙婆婆'})
    all_display_names = set()  # 所有原始频道名
    programme_keys = set()     # 节目去重键 (start, channel)
    matched_channels = set()   # 匹配成功的频道名
    unmatched_channels = set() # 匹配失败的原始频道名
    channel_display_name_map = {}  # 匹配名→新频道ID
    channel_original_id_map = {}   # 原始频道ID→匹配名

    # 2. 遍历所有XMLTV源，处理频道和节目
    for url in input_urls:
        print(f"正在处理: {url}")
        xml_elem = download_xmltv(url)
        if xml_elem is None:
            continue

        # 处理频道节点
        for channel in xml_elem.findall('channel'):
            # 取第一个display-name，避免多节点重复处理
            original_dn = channel.find('display-name')
            if not original_dn or not original_dn.text:
                continue
            original_dn_text = original_dn.text.strip()
            all_display_names.add(original_dn_text)

            # 智能匹配自定义频道
            matched_name = check_display_name(original_dn_text, custom_channels)
            original_channel_id = channel.get('id', '')
            if original_channel_id:
                channel_original_id_map[original_channel_id] = matched_name  # 记录原始ID→匹配名

            if matched_name:
                if matched_name not in channel_display_name_map:
                    # 未添加过的匹配频道，生成新节点并加入根节点
                    new_channel = format_channel(channel, matched_name)
                    root.append(new_channel)
                    channel_display_name_map[matched_name] = new_channel.get('id')
                    matched_channels.add(matched_name)
            else:
                # 匹配失败，加入未匹配列表
                unmatched_channels.add(original_dn_text)

        # 处理节目节点（核心BUG修复：按原始ID→匹配名判断是否有效）
        for programme in xml_elem.findall('programme'):
            original_channel_id = programme.get('channel', '')
            # 仅处理「原始频道ID匹配成功」的节目
            if original_channel_id not in channel_original_id_map:
                continue
            matched_name = channel_original_id_map[original_channel_id]
            if matched_name not in channel_display_name_map:
                continue

            # 节目去重：(start, 原始channel_id) 作为唯一键
            start = programme.get('start', '').split()[0]
            programme_key = (start, original_channel_id)
            if not start or programme_key in programme_keys:
                continue
            programme_keys.add(programme_key)

            # 生成格式化节目节点，替换为匹配后的频道ID
            new_programme = format_programme(programme)
            new_programme.set('channel', channel_display_name_map[matched_name])
            root.append(new_programme)

    # 3. 重置频道ID为连续数字（1,2,3...），简化规则
    channel_id_counter = 1
    channel_old2new_id = {}  # 旧ID→新ID
    for channel in root.findall('channel'):
        old_id = channel.get('id', '')
        new_id = str(channel_id_counter)
        channel_old2new_id[old_id] = new_id
        channel.set('id', new_id)
        channel_id_counter += 1
    # 更新节目节点的channel为新ID
    for programme in root.findall('programme'):
        old_id = programme.get('channel', '')
        if old_id in channel_old2new_id:
            programme.set('channel', channel_old2new_id[old_id])

    # 4. 重排节点：channel在前，programme在后（XMLTV规范）
    root[:] = sorted(root, key=lambda child: 0 if child.tag == 'channel' else 1)

    # 5. 格式化XML缩进
    indent(root)

    # 6. 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 7. 生成最终文件（XML + gzip）
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"✅ 标准化XMLTV已保存: {output_file}")

    # 生成gzip压缩版
    with open(output_file, 'rb') as f_in, gzip.open(f"{output_file}.gz", 'wb') as f_out:
        f_out.write(f_in.read())
    print(f"✅ gzip压缩版已保存: {output_file}.gz")

    # 8. 生成统计文件
    # 所有原始频道名
    with open(display_name_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(all_display_names)))
    # 匹配成功的频道名
    with open(matched_channel_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(matched_channels)))
    # 匹配失败的原始频道名
    with open(unmatched_channel_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(unmatched_channels)))

    # 打印统计信息
    print(f"📊 统计：原始频道{len(all_display_names)}个 | 匹配成功{len(matched_channels)}个 | 未匹配{len(unmatched_channels)}个")
    print(f"📊 生成节目{len(programme_keys)}个 | 输出统计文件3个")

# 示例调用（可直接运行）
if __name__ == "__main__":
    # 自定义频道列表URL
    channel_url = 'https://7259.cloudns.ch/iptv/source/list_yd.txt'
    # XMLTV源地址列表
    input_urls = [
        "https://raw.bgithub.xyz/tqx5201/iptv/main/jiaoben/epg_cache/epg_1905.xml",
        "https://raw.bgithub.xyz/tqx5201/iptv/main/jiaoben/epg_cache/epg_migu.xml",
        "https://raw.bgithub.xyz/kuke31/xmlgz/main/e.xml.gz",
        "http://epg.51zmt.top:8000/e.xml",
        "https://epg.112114.xyz/pp.xml",
        "https://assets.livednow.com/epg.xml",
        "https://epg.pw/xmltv/epg_TW.xml.gz",
        "https://epg.pw/xmltv/epg_HK.xml.gz",
        "https://epg.pw/xmltv/epg_CN.xml.gz"
    ]
    # 输出文件路径
    output_file = "epg/e.xml"
    display_name_file = "epg/display_names.txt"
    matched_channel_file = "epg/matched_channels.txt"
    unmatched_channel_file = "epg/unmatched_channels.txt"

    # 执行合并
    merge_xmltv_files(input_urls, output_file, display_name_file, matched_channel_file, unmatched_channel_file, channel_url)
