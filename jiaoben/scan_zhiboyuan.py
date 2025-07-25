#!/usr/bin/env python3
import asyncio, aiohttp, argparse, csv, re
from typing import List, Tuple
from urllib.parse import urlparse

async def check(session: aiohttp.ClientSession, url: str, timeout: int) -> Tuple[str, bool]:
    try:
        async with session.get(url, timeout=timeout) as resp:
            return url, resp.status == 200
    except Exception:
        return url, False

async def main(template: str, m3u8: str, timeout: int, max_conn: int) -> None:
    # 1. 生成 IP
    if template.count("x") == 1:
        ips = [template.replace("x", str(i)) for i in range(1, 256)]
    elif template.count("x") == 2:
        ips = [template.replace("x", str(i), 1).replace("x", str(j))
               for i in range(1, 256) for j in range(1, 256)]
    else:
        raise ValueError("模板只能含 1 或 2 个 x")

    # 2. 拼缓存 URL
    #host_suffix = m3u8.replace("http://", "", 1)
    #urls = [f"http://{ip}/{host_suffix}" for ip in ips]


    parts = urlparse(m3u8)
    domain = parts.netloc
    path_and_query = parts.path
    if parts.query:
        path_and_query += "?" + parts.query

    urls = [f"{parts.scheme}://{ip}/{domain}{path_and_query}" for ip in ips]

    # 3. 并发检测
    sem = asyncio.Semaphore(max_conn)
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(check(session, u, timeout)) for u in urls]
        results = await asyncio.gather(*tasks)

    # 4. 写 CSV
    with open("result.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cache_url", "alive"])
        writer.writerows(results)
    print(f"完成，共检测 {len(results)} 条地址 → result.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量检测带缓存 IP 的 m3u8")
    parser.add_argument("template", help="IP 模板，如 192.168.2.x 或 192.168.x.x")
    parser.add_argument("m3u8", help="原始 m3u8 地址")
    parser.add_argument("-t", "--timeout", type=int, default=5, help="单次超时秒")
    parser.add_argument("-c", "--concurrency", type=int, default=300, help="并发数")
    args = parser.parse_args()
    asyncio.run(main(args.template, args.m3u8, args.timeout, args.concurrency))
