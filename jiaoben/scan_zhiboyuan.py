#!/usr/bin/env python3
import asyncio, aiohttp, argparse, csv, sys
from urllib.parse import urlparse, urlunparse

async def check(session, url, timeout):
    try:
        async with session.get(url, timeout=timeout) as resp:
            return url, resp.status == 200
    except Exception as e:
        print(f"{url}-{e}")
        return url, False

async def main(template, m3u8, timeout, conn):
    # 根据模板生成 IP 列表
    parts = template.split(".")
    if len(parts) == 3:          # 192.168.2
        base = template
        ips = [f"{base}.{i}" for i in range(1, 256)]
    elif len(parts) == 2:        # 192.168
        base = template
        ips = [f"{base}.{i}.{j}" for i in range(1, 256) for j in range(1, 256)]
    else:
        sys.exit("模板必须是两段或三段，如 192.168 或 192.168.2")

    # 构造缓存 URL：把域名当路径前缀
    u = urlparse(m3u8)
    new_path = f"{u.netloc}{u.path}"
    if u.query:
        new_path += f"?{u.query}"
    new_path = new_path.lstrip("/")

    urls = [f"{u.scheme}://{ip}/{new_path}" for ip in ips]

    sem = asyncio.Semaphore(conn)
    async with aiohttp.ClientSession() as session:
        tasks = [check(session, url, timeout) for url in urls]
        results = await asyncio.gather(*tasks)

    with open("result.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cache_url", "alive"])
        writer.writerows(results)
    print(f"完成，共 {len(results)} 条地址 → result.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("template", help="IP 前缀，如 192.168.2 或 192.168")
    parser.add_argument("m3u8", help="原始 m3u8 地址")
    parser.add_argument("-t", "--timeout", type=int, default=5)
    parser.add_argument("-c", "--concurrency", type=int, default=300)
    args = parser.parse_args()
    asyncio.run(main(args.template, args.m3u8, args.timeout, args.concurrency))
