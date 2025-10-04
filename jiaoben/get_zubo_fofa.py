#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, time, base64, subprocess, requests, datetime
from pathlib import Path
from datetime import datetime, timedelta
import os,sys
from concurrent.futures import ThreadPoolExecutor
#from tqdm import tqdm
import socket

os.environ['TZ'] = 'Asia/Shanghai'
#time.tzset()

# ========== 全局配置 ==========
BASE_URL = 'https://fofa.info/result?qbase64='
RTP_DIR = Path('./rtp')
IP_DIR = Path('./ip')
TXT_DIR = Path('./txt')
OUTPUT_FILE = Path('./zubo_fofa.txt')

IP_DIR.mkdir(exist_ok=True)
TXT_DIR.mkdir(exist_ok=True)

PROVINCES_CN = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "广西", "海南", "四川", "贵州", "云南", "西藏", "陕西", "甘肃",
    "青海", "内蒙古", "宁夏", "新疆"
]
PROVINCES_EN = [
    "Beijing", "Tianjin", "Shanghai", "Chongqing", "Hebei", "Shanxi", "Liaoning",
    "Jilin", "Heilongjiang", "Jiangsu", "Zhejiang", "Anhui", "Fujian", "Jiangxi",
    "Shandong", "Henan", "Hubei", "Hunan", "Guangdong", "Guangxi Zhuangzu", "Hainan",
    "Sichuan", "Guizhou", "Yunnan", "Xizang", "Shaanxi", "Gansu", "Qinghai",
    "Nei Mongol", "Ningxia Huizu", "Xinjiang Uygur"
]
PROVIDERS = ["电信"]          # 如需多运营商自行扩展

# FOFA 账号 Cookie / Authorization
FOFA_HEADERS = {
    "Cookie": "isRedirectLang=1; is_mobile=pc; Hm_lvt_4275507ba9b9ea6b942c7a3f7c66da90=1759280591; HMACCOUNT=9A2FE7604340D8CF; _ga=GA1.1.216559623.1759280591; __fcd=SMHX4TKESUSP61V97C804F5F0E75CCCF; baseShowChange=false; viewOneHundredData=false; befor_router=%2Fresult%3Fqbase64%3DInVkcHh5IiAmJiByZWdpb249IlNoYW5naGFpIiBhc249IjQxMzQiIHx8IGFzbj0iNDg0NyIgfHwgYXNuPSI0ODA5IiB8fCBhc249IjQ4MTIiIHx8IGFzbj0iNDg0MiIgfHwgYXNuPSIxMzgwMTEiIHx8IGFzbj0iMTQwMzMwIiB8fCBhc249IjE0MDA2MSI%253D; fofa_token=eyJhbGciOiJIUzUxMiIsImtpZCI6Ik5XWTVZakF4TVRkalltSTJNRFZsWXpRM05EWXdaakF3TURVMlkyWTNZemd3TUdRd1pUTmpZUT09IiwidHlwIjoiSldUIn0.eyJpZCI6MjkwMjkyLCJtaWQiOjEwMDE2NDQ3NiwidXNlcm5hbWUiOiLlpKnku5nlqYblqYYiLCJwYXJlbnRfaWQiOjAsImV4cCI6MTc1OTg4NzQxOX0.eM22bl9uviBcjF5nSd4uFxWUuaWMyOZpDeqXNBV9wM7nSATW2seA8pIMnTEozmtKgbXPOZjrYxJhnjMs_EjckQ; user=%7B%22id%22%3A290292%2C%22mid%22%3A100164476%2C%22is_admin%22%3Afalse%2C%22username%22%3A%22%E5%A4%A9%E4%BB%99%E5%A9%86%E5%A9%86%22%2C%22nickname%22%3A%22%E5%A4%A9%E4%BB%99%E5%A9%86%E5%A9%86%22%2C%22email%22%3A%22tqx5201%40163.com%22%2C%22avatar_medium%22%3A%22https%3A%2F%2Fnosec.org%2Fmissing.jpg%22%2C%22avatar_thumb%22%3A%22https%3A%2F%2Fnosec.org%2Fmissing.jpg%22%2C%22key%22%3A%22efc3ee3b5851e426de7861dfd4370998%22%2C%22category%22%3A%22user%22%2C%22rank_avatar%22%3A%22%22%2C%22rank_level%22%3A0%2C%22rank_name%22%3A%22%E6%B3%A8%E5%86%8C%E7%94%A8%E6%88%B7%22%2C%22company_name%22%3A%22%E5%A4%A9%E4%BB%99%E5%A9%86%E5%A9%86%22%2C%22coins%22%3A0%2C%22can_pay_coins%22%3A0%2C%22fofa_point%22%3A0%2C%22credits%22%3A1%2C%22expiration%22%3A%22-%22%2C%22login_at%22%3A0%2C%22data_limit%22%3A%7B%22web_query%22%3A300%2C%22web_data%22%3A3000%2C%22api_query%22%3A0%2C%22api_data%22%3A0%2C%22data%22%3A-1%2C%22query%22%3A-1%7D%2C%22expiration_notice%22%3Afalse%2C%22remain_giveaway%22%3A1000%2C%22fpoint_upgrade%22%3Afalse%2C%22account_status%22%3A%22%22%2C%22parents_id%22%3A0%2C%22parents_email%22%3A%22%22%2C%22parents_fpoint%22%3A0%2C%22created_at%22%3A%222023-06-27%2000%3A00%3A00%22%7D; is_flag_login=1; Hm_lpvt_4275507ba9b9ea6b942c7a3f7c66da90=1759282623; _ga_9GWBD260K9=GS2.1.s1759280591$o1$g1$t1759282622$j30$l0$h0"
}

# ========== 工具函数 ==========
def log(msg):
    print(f"[{datetime.now():%m-%d %H:%M:%S}] {msg}")

def file_older_than_hours(path: str | Path, hours: float = 12, *, use_ctime: bool = False) -> bool:
    """
    返回 True 表示文件已「创建/修改」超过指定小时数
    use_ctime=True  用创建时间（Windows 上为真实创建时间）
    use_ctime=False 用修改时间（默认）
    """
    f = Path(path)
    if not f.exists():
        raise FileNotFoundError(path)

    # 取时间戳（秒）
    ts = f.stat().st_ctime if use_ctime else f.stat().st_mtime
    file_time = datetime.fromtimestamp(ts)
    return datetime.now() - file_time < timedelta(hours=hours)

def nc_alive(ip_port: str, timeout: float = 1.0) -> bool:
    ip, port = ip_port.rsplit(':', 1)
    try:
        with socket.create_connection((ip, int(port)), timeout=timeout):
            return True
    except (socket.timeout, socket.error, ValueError):
        return False
def ffmpeg_speed(url: str, probe_seconds: int = 10) -> float:
    # 1. 指向仓库根目录的 ffmpeg
    repo_root = Path(__file__).resolve().parent.parent  # jiaoben 的上一级
    ffmpeg_exe = repo_root / 'ffmpeg'
    if not ffmpeg_exe.is_file():
        raise FileNotFoundError(f'仓库根目录缺少 {ffmpeg_exe.name}')

    tmp = repo_root / 'speed_test.ts'  # 临时文件也放根目录，避免权限问题
    print(tmp)

    cmd = [
        str(ffmpeg_exe),          # 强制用当前目录的
        '-rw_timeout', str(probe_seconds * 1_000_000),
        '-i', url,
        '-t', str(probe_seconds),
        '-c', 'copy',
        '-f', 'mpegts',
        '-y', str(tmp),
        '-loglevel', 'error'
    ]

    start = time.perf_counter()
    try:
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return 0.0
    finally:
        print('66')
        if tmp.exists():
            elapsed = time.perf_counter() - start
            mbps = tmp.stat().st_size * 8 / elapsed / 1_000_000
            #tmp.unlink(missing_ok=True)
            print(tmp.stat().st_size)
            return round(mbps, 2) if mbps >= 0.01 else 0.0
    return 0.0

def fofa_query(prov_en: str, provider: str) -> str:
    """构造查询语句 -> base64 -> 返回完整 url"""
    asn_map = {
        "电信": '(asn="4134" || asn="4847" || asn="4809" || asn="4812" || asn="4842" || asn="138011" || asn="140330" || asn="140061")',
        "移动": '(asn="9808" || asn="56044" || asn="56045" || asn="56046" || asn="56047" || asn="56048" || asn="56049" || asn="56050" || asn="56051" || asn="56052")',
        "联通": '(asn="17621" || asn="4837" || asn="4808" || asn="55491")'
    }
    asn = asn_map.get(provider, 'asn=""')
    query = f'"udpxy" && country="CN" && region="{prov_en}" && {asn} && protocol="http"'
    b64 = base64.b64encode(query.encode()).decode().strip()
    return BASE_URL + b64

def parse_ip_port(html: str):
    """从 fofa 结果页提取 ip:port"""
    return re.findall(r'(\d+\.\d+\.\d+\.\d+:\d+)', html)

# ========== 核心流程 ==========
def get_ip_fofa(full_url: str, province: str, provider: str):
    html_file = IP_DIR / f"{province}_{provider}.html"
    ip_file   = IP_DIR / f"{province}_{provider}.txt"
    speed_file= IP_DIR / f"{province}_{provider}_测速.txt"
    # 删除已存在的文件
    for f in (ip_file, speed_file):
        f.unlink(missing_ok=True)

    log(f"检索 {province}_{provider} …")
    # 取模板第一行 rtp 地址
    tpl = RTP_DIR / f"{province}_{provider}.txt"
    if not tpl.exists():
        log(f"模板不存在 {tpl}")
        return
    first_line = tpl.read_text(encoding='utf8').splitlines()[0]
    print(first_line)
    # 包含 404 就放弃
    if '404' in first_line:
        print('首行包含 404，跳过处理')
        return
    rtp_part = first_line.split(',')[1].strip()
    stream = rtp_part.replace('rtp://', 'udp/')
    print(stream)

    cache = 0
    if os.path.isfile(html_file) and cache and file_older_than_hours(html_file):
        print('本地存在')
        with open(html_file,  encoding='utf-8') as file:
            html = file.read()
        #print(html)
    else:
        print('本地不存在')
        resp = requests.get(full_url, headers=FOFA_HEADERS, timeout=30)
        resp.raise_for_status()
        html = resp.text
        html_file.write_text(html, encoding='utf8')

    if 'IP访问异常，疑似为爬虫被暂时禁止访问' in html:
        log("FOFA 反爬触发，跳过")
        return


    ip_ports = list(dict.fromkeys(parse_ip_port(html)))
    print(ip_ports)
    log(f"FOFA 返回 {len(ip_ports)} 条记录")

    for ip_port in ip_ports:
        if not nc_alive(ip_port):
            print('not ok')
            continue
        else:
            print(f'{ip_port},ok')
        speed_url = f"http://{ip_port}/{stream}"
        print(speed_url)
        mbps = ffmpeg_speed(speed_url)
        print(mbps)
        if mbps > 0:
            with ip_file.open('a', encoding='utf-8') as f:
                f.write(f'{ip_port}\n')
            with speed_file.open('a', encoding='utf-8') as f:
                f.write(f'{ip_port} {mbps}M\n')

def make_zubo_txt():
    for speed_txt in IP_DIR.glob("*_测速.txt"):
        province, provider, _ = speed_txt.stem.split('_')
        sort_txt = IP_DIR / f"{province}_{provider}_排序.txt"
        lines = [l.strip() for l in speed_txt.read_text(encoding='utf8').splitlines() if 'M' in l and len(l.split()) >= 2]
        print(lines)
        lines.sort(key=lambda x: float(x.split()[1].rstrip('M')), reverse=True)
        sort_txt.write_text('\n'.join(lines), encoding='utf8')

        # 取前 3
        top3 = [l.split()[0] for l in lines[:3]]
        template = RTP_DIR / f"{province}_{provider}.txt"
        if not template.exists():
            continue
        content = template.read_text(encoding='utf8')
        out = TXT_DIR / f"fofa_{province}_{provider}.txt"
        out.unlink(missing_ok=True)
        for idx, ip in enumerate(top3, 1):
            replaced = content.replace('rtp://', f'http://{ip}/udp/')
            with out.open('a', encoding='utf8') as f:
                f.write(replaced + '\n')

def make_zubo_fofa():
    OUTPUT_FILE.unlink(missing_ok=True)
    for prov in PROVINCES_CN:
        for provider in PROVIDERS:
            txt = TXT_DIR / f"fofa_{prov}_{provider}.txt"
            if not txt.exists() or txt.stat().st_size == 0:
                continue
            tag = f"{prov}-{provider}".replace('_', '-')
            with OUTPUT_FILE.open('a', encoding='utf8') as f:
                f.write(f"{tag},#genre#\n")
                f.write(txt.read_text(encoding='utf8'))
                f.write('\n')

def main():
    # 按小时轮询省份
    now = datetime.now()
    hour = (now.hour + 8) % 24          # 修正：保证 0-23
    total = len(PROVINCES_CN)
    batch = (hour - 1) % ((total + 3) // 4)  # 0-based 批次
    start = batch * 4
    # 循环取 4 个（切片超界自动停）
    prov_cns = [PROVINCES_CN[i % total] for i in range(start, start + 4)]
    prov_ens = [PROVINCES_EN[i % total] for i in range(start, start + 4)]


    for provider in PROVIDERS:
        for prov_cn, prov_en in zip(prov_cns, prov_ens):   # 同时拿中英文,每小时4个省份
        #for prov_cn, prov_en in zip(PROVINCES_CN, PROVINCES_EN):   # 同时拿中英文,全部搞定
            url = fofa_query(prov_en, provider)
            #print(url)
            get_ip_fofa(url, prov_cn, provider)
    make_zubo_txt()
    make_zubo_fofa()
    log("全部完成")

if __name__ == '__main__':
    #main()
    ffmpeg_speed('http://111.127.156.228:51234/udp/239.29.0.2:5000')
