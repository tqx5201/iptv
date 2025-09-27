#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, time, base64, subprocess, requests, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

os.environ['TZ'] = 'Asia/Shanghai'
time.tzset()

# ========== 全局配置 ==========
BASE_URL = 'https://fofa.info/result?qbase64='
RTP_DIR = Path('../rtp')
IP_DIR = Path('../ip')
TXT_DIR = Path('../txt')
OUTPUT_FILE = Path('../zubo_fofa.txt')

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
    "Authorization": "Bearer eyJhbGciOiJIUzUxMiIsImtpZCI6Ik5XWTVZakF4TVRkalltSTJNRFZsWXpRM05EWXdaakF3TURVMlkyWTNZemd3TUdRd1pUTmpZUT09IiwidHlwIjoiSldUIn0.eyJpZCI6MjkwMjkyLCJtaWQiOjEwMDE2NDQ3NiwidXNlcm5hbWUiOiLlpKnku5nlqYblqYYiLCJwYXJlbnRfaWQiOjAsImV4cCI6MTc1OTU2MjcwM30.UrWz7NcuIzZJuSglIDEuZ-JzU349kPf812R6_r7MVjeKZ0_M4oYZp8fEOA7wOKHk1n6wRZWhqtMzPA3XoNNy7A",
    "Cookie": "acw_tc=3ccdc15917589579056873556e3e6659e5a1e1d24617ab48463a17fe7ecaef; __fcd=L6A5MOXZOGGXJXSJBA1C829C184F8BA2"
}

# ========== 工具函数 ==========
def log(msg):
    print(f"[{datetime.datetime.now():%m-%d %H:%M:%S}] {msg}")

def ffmpeg_speed(url: str) -> float:
    """下载 10 秒，返回 Mbps，失败返回 0"""
    tmp = Path("temp_video.mp4")
    cmd = [
        'ffmpeg', '-timeout', '10000000', '-i', url,
        '-t', '10', '-c', 'copy', str(tmp), '-y', '-loglevel', 'error'
    ]
    start = time.time()
    ret = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elapsed = time.time() - start
    if ret.returncode != 0 or not tmp.exists() or elapsed <= 0:
        return 0.0
    size_bytes = tmp.stat().st_size
    tmp.unlink(missing_ok=True)
    mbps = size_bytes * 8 / elapsed / 1_000_000
    return round(mbps, 2) if mbps >= 1 else 0.0

def nc_alive(ip_port: str) -> bool:
    ip, port = ip_port.split(':')
    ret = subprocess.run(['nc', '-w', '1', '-z', ip, port],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ret.returncode == 0

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
    for f in (html_file, ip_file, speed_file):
        f.unlink(missing_ok=True)

    # 取模板第一行 rtp 地址
    tpl = RTP_DIR / f"{province}_{provider}.txt"
    if not tpl.exists():
        log(f"模板不存在 {tpl}")
        return
    first_line = tpl.read_text(encoding='utf8').splitlines()[0]
    rtp_part = first_line.split(',')[1].strip()
    stream = rtp_part.replace('rtp://', 'udp/')

    log(f"检索 {province}_{provider} …")
    resp = requests.get(full_url, headers=FOFA_HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text
    html_file.write_text(html, encoding='utf8')

    if 'IP访问异常，疑似为爬虫被暂时禁止访问' in html:
        log("FOFA 反爬触发，跳过")
        return

    ip_ports = parse_ip_port(html)
    log(f"FOFA 返回 {len(ip_ports)} 条记录")

    for ip_port in tqdm(ip_ports, desc="检测存活"):
        if not nc_alive(ip_port):
            continue
        speed_url = f"http://{ip_port}/{stream}"
        mbps = ffmpeg_speed(speed_url)
        if mbps > 0:
            ip_file.write_text(f"{ip_port}\n", encoding='utf8', append=True)
            speed_file.write_text(f"{ip_port}  {mbps} Mb/s\n", encoding='utf8', append=True)

def make_zubo_txt():
    for speed_txt in IP_DIR.glob("*_测速.txt"):
        province, provider, _ = speed_txt.stem.split('_')
        sort_txt = IP_DIR / f"{province}_{provider}_排序.txt"
        lines = [l.strip() for l in speed_txt.read_text(encoding='utf8').splitlines() if 'M' in l]
        lines.sort(key=lambda x: float(x.split()[1]), reverse=True)
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
            out.write_text(replaced + '\n', encoding='utf8', append=True)

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
    now = datetime.datetime.now()
    hour = now.hour
    day_odd = now.day % 2 == 1
    start = 0 if day_odd else 24
    idx = (start + hour) % len(PROVINCES_CN)
    prov_cn = PROVINCES_CN[idx]
    prov_en = PROVINCES_EN[idx]
    log(f"今日奇偶={day_odd} 小时={hour} 选中省份={prov_cn}")

    for provider in PROVIDERS:
        url = fofa_query(prov_en, provider)
        get_ip_fofa(url, prov_cn, provider)

    make_zubo_txt()
    make_zubo_fofa()
    log("全部完成")

if __name__ == '__main__':
    main()
