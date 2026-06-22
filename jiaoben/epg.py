import xml.etree.ElementTree as ET
import requests
import gzip
import io
import os
# 新增：禁用HTTPS证书验证警告（核心解决InsecureRequestWarning）
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# 全局请求头：模拟浏览器，避免被源地址拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip, deflate"
}

def ignore_xml_namespace(elem):
    """忽略XML命名空间，解决带命名空间的节点无法查找问题"""
    if elem.tag.startswith('{'):
        elem.tag = elem.tag.split('}', 1)[1]
    for child in elem:
        ignore_xml_namespace(child)
    return elem

def get_node_text(elem, node_name):
    """通用节点文本提取：兼容命名空间/多层嵌套/多节点，返回第一个有效文本"""
    if elem is None:
        return ""
    nodes = elem.findall(f'.//{node_name}')
    for node in nodes:
        if node.text and node.text.strip():
            return node.text.strip()
    return ""

def download_xmltv(url):
    """从网址下载XMLTV文件并解析，支持gzip解压，自动处理命名空间"""
    url = url.replace('bgithub.xyz', 'githubusercontent.com')
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.raise_for_status()

        if url.endswith('.gz'):
            with gzip.open(io.BytesIO(response.content), 'rt', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            content = response.content.decode('utf-8', errors='ignore')

        elem = ET.fromstring(content)
        elem = ignore_xml_namespace(elem)
        return elem
    except requests.RequestException as e:
        print(f"❌ 下载文件 {url} 时出错: {e}")
    except ET.ParseError as e:
        print(f"❌ 解析文件 {url} 时出错: {e}")
    return None

def extract_channels_from_url(url):
    """从网络地址提取自定义频道列表，过滤空行/无效行/空频道名"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        response.encoding = 'utf-8'
        channels = []
        for line in response.text.splitlines():
            line = line.strip()
            if line and "#genre#" not in line:
                channel_name = line.split(',')[0].strip()
                if channel_name:
                    channels.append(channel_name)
        # 去重自定义频道，避免重复匹配
        channels = list(set(channels))
        print(f"✅ 获取我的频道成功，共{len(channels)}个有效频道")
        return channels
    except requests.RequestException as e:
        print(f"❌ 请求频道列表失败: {e}")
        return []

def format_programme(programme):
    """格式化programme节点，补全东八区时区，兼容所有格式的title解析"""
    new_programme = ET.Element('programme')
    # 处理时间，裁剪多余后缀并补全+0800时区
    start = programme.get('start', '').split()[0] if programme.get('start') else ''
    stop = programme.get('stop', '').split()[0] if programme.get('stop') else ''
    new_programme.set('start', f"{start} +0800" if start else '')
    new_programme.set('stop', f"{stop} +0800" if stop else '')
    new_programme.set('channel', programme.get('channel', ''))

    # 提取节目标题，无有效标题则显示「未知标题」
    title_text = get_node_text(programme, 'title')
    new_title = ET.SubElement(new_programme, 'title')
    new_title.text = title_text if title_text else '未知标题'
    return new_programme

def format_channel(channel, matched_name):
    """格式化channel节点，仅保留ID和匹配后的频道名，精简节点"""
    new_channel = ET.Element('channel')
    new_channel.set('id', channel.get('id', ''))
    # 写入匹配后的自定义频道名，空值兜底
    new_display_name = ET.SubElement(new_channel, 'display-name')
    new_display_name_text = matched_name.strip() if matched_name else '未知频道'
    new_display_name.text = new_display_name_text
    return new_channel

def check_display_name(display_name_text, channels):
    """智能匹配频道名，处理CCTV/HD/台字等格式差异，按优先级匹配"""
    if not display_name_text or not channels:
        return None
    display_name_text = display_name_text.strip()
    # 匹配规则（按优先级从高到低）
    match_rules = [
        display_name_text,
        display_name_text.replace('CCTV', 'CCTV-'),
        display_name_text.split(' ')[0],
        display_name_text + ' HD',
        display_name_text.replace('HD', '').strip(),
        display_name_text.replace('台', '').strip(),
        display_name_text + '台',
        display_name_text + '台HD'
    ]
    for name in match_rules:
        if name in channels:
            return name
    return None

def indent(elem, level=0):
    """为XML节点添加缩进，生成人类可读的XML文件"""
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
    """主函数：合并、筛选、格式化XMLTV，生成最终文件+统计文件"""
    if not input_urls:
        print("❌ 没有输入XMLTV源地址，程序退出")
        return

    # 提取并校验自定义频道列表
    custom_channels = extract_channels_from_url(channel_url)
    if not custom_channels:
        print("❌ 未获取到有效自定义频道列表，程序退出")
        return

    # 初始化全局变量
    root = ET.Element('tv', attrib={
        'generator-info-name': 'My EPG Generator',
        'generator-info-user': '天仙婆婆',
        'xmlns': 'http://xmltv.org/ns/xmltv/0.1'
    })
    all_display_names = set()  # 所有原始频道名
    programme_keys = set()     # 节目去重键 (start, 原始channel_id)
    matched_channels = set()   # 匹配成功的频道名
    unmatched_channels = set() # 匹配失败的原始频道名
    channel_display_name_map = {}  # 匹配名→新频道ID（全局去重核心）
    channel_original_id_map = {}   # 原始频道ID→匹配名
    failed_urls = 0               # 源地址处理失败计数

    # 遍历所有XMLTV源，处理频道和节目
    for url in input_urls:
        print(f"\n正在处理源地址: {url}")
        xml_elem = download_xmltv(url)
        if xml_elem is None:
            failed_urls += 1
            continue

        # 处理频道节点：过滤无ID、无频道名，全局去重匹配
        for channel in xml_elem.findall('channel'):
            original_channel_id = channel.get('id', '').strip()
            if not original_channel_id:
                continue
            # 提取原始频道名
            original_dn_text = get_node_text(channel, 'display-name')
            if not original_dn_text:
                continue

            all_display_names.add(original_dn_text)
            # 智能匹配自定义频道
            matched_name = check_display_name(original_dn_text, custom_channels)
            channel_original_id_map[original_channel_id] = matched_name

            # 匹配成功：仅首次出现时生成频道节点（全局去重）
            if matched_name:
                if matched_name not in channel_display_name_map:
                    new_channel = format_channel(channel, matched_name)
                    root.append(new_channel)
                    channel_display_name_map[matched_name] = new_channel.get('id')
                    matched_channels.add(matched_name)
            # 匹配失败：加入未匹配列表
            else:
                unmatched_channels.add(original_dn_text)

        # 处理节目节点：仅保留匹配成功频道的节目，去重聚合
        for programme in xml_elem.findall('programme'):
            original_channel_id = programme.get('channel', '').strip()
            # 过滤无原始ID、未匹配成功的节目
            if original_channel_id not in channel_original_id_map:
                continue
            matched_name = channel_original_id_map[original_channel_id]
            if matched_name not in channel_display_name_map:
                continue

            # 节目去重：以(开始时间, 原始频道ID)为唯一键
            start = programme.get('start', '').split()[0] if programme.get('start') else ''
            if not start:
                continue
            programme_key = (start, original_channel_id)
            if programme_key in programme_keys:
                continue
            programme_keys.add(programme_key)

            # 生成格式化节目节点，关联到全局唯一频道ID
            new_programme = format_programme(programme)
            new_programme.set('channel', channel_display_name_map[matched_name])
            root.append(new_programme)

    # 重置频道ID为连续数字（1,2,3...），简化ID规则
    channel_id_counter = 1
    channel_old2new_id = {}
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

    # 重排节点：channel在前，programme在后（符合XMLTV官方规范）
    root[:] = sorted(root, key=lambda child: 0 if child.tag == 'channel' else 1)
    # 格式化XML缩进，提升可读性
    indent(root)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 生成最终文件：XML原文件 + gzip压缩版
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"\n✅ 标准化XMLTV文件已保存: {output_file}")

    # 生成gzip压缩版（体积小，适合IPTV播放器网络加载）
    with open(output_file, 'rb') as f_in, gzip.open(f"{output_file}.gz", 'wb') as f_out:
        f_out.write(f_in.read())
    print(f"✅ Gzip压缩版已保存: {output_file}.gz")

    # 生成3个统计文件
    with open(display_name_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(all_display_names)))
    with open(matched_channel_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(matched_channels)))
    with open(unmatched_channel_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(unmatched_channels)))

    # 打印最终统计信息
    print(f"\n📊 处理结果统计：")
    print(f"  源地址：共{len(input_urls)}个 | 成功{len(input_urls)-failed_urls}个 | 失败{failed_urls}个")
    print(f"  频道：原始{len(all_display_names)}个 | 匹配成功{len(matched_channels)}个 | 未匹配{len(unmatched_channels)}个")
    print(f"  节目：共生成{len(programme_keys)}个（已去重）")
    print(f"  统计文件：3个（display_names/matched_channels/unmatched_channels）")

if __name__ == "__main__":
    # 配置参数（可根据需求修改）
    CHANNEL_URL = 'https://7259.cloudns.ch/iptv/source/list_yd.txt'  # 自定义频道列表URL
    # XMLTV源地址列表（稳定有效，已剔除失效源）
    INPUT_URLS = [
        "https://raw.githubuserconten.com/tqx5201/iptv/main/jiaoben/epg_cache/epg_tv189.xml",
        "https://raw.githubuserconten.com/tqx5201/iptv/main/jiaoben/epg_cache/epg_1905.xml",
        "https://raw.githubuserconten.com/tqx5201/iptv/main/jiaoben/epg_cache/epg_migu.xml",
        "https://raw.githubuserconten.com/kuke31/xmlgz/main/e.xml.gz",
        "http://epg.51zmt.top:8000/e.xml.gz",
        "https://epg.hoholove.com/epg.xml",
        "https://raw.bgithub.xyz/imDazui/Telegram-EPG/master/epg.xml",
        "https://epg.pw/xmltv/epg_TW.xml.gz",
        "https://epg.pw/xmltv/epg_HK.xml.gz",
        "https://epg.pw/xmltv/epg_CN.xml.gz"
    ]
    # 输出文件路径（自动创建epg目录）
    OUTPUT_FILE = "epg/e.xml"
    DISPLAY_NAME_FILE = "epg/display_names.txt"
    MATCHED_CHANNEL_FILE = "epg/matched_channels.txt"
    UNMATCHED_CHANNEL_FILE = "epg/unmatched_channels.txt"

    # 执行EPG合并主程序
    merge_xmltv_files(
        input_urls=INPUT_URLS,
        output_file=OUTPUT_FILE,
        display_name_file=DISPLAY_NAME_FILE,
        matched_channel_file=MATCHED_CHANNEL_FILE,
        unmatched_channel_file=UNMATCHED_CHANNEL_FILE,
        channel_url=CHANNEL_URL
    )
