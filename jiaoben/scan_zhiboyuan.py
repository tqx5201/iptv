#!/usr/bin/env python3
import asyncio, aiohttp, argparse, csv, time, sys
from urllib.parse import urlparse

async def check(session, url, timeout):
    """返回 (url, 是否成功, 错误信息)"""
    try:
        async with session.get(url, timeout=timeout) as resp:
            ok = resp.status == 200
            err = None
    except Exception as e:
        ok  = False
        err = str(e)
    return url, ok, err

async def main(template, m3u8, timeout, conn):
    # 1. IP 列表
    bits = template.split(".")
    if len(bits) == 3:        # 192.168.2
        ips = [f"{template}.{i}" for i in range(1, 256)]
    elif len(bits) == 2:      # 192.168
        ips = [f"{template}.{i}.{j}"
               for i in range(1, 256) for j in range(1, 256)]
    else:
        sys.exit("模板必须是两段或三段，如 192.168 或 192.168.2")

    # 2. 构造缓存 URL：把原域名当路径前缀
    u = urlparse(m3u8)
    prefix = u.netloc + u.path
    if u.query:
        prefix += "?" + u.query
    prefix = prefix.lstrip("/")
    urls = [f"{u.scheme}://{ip}/{prefix}" for ip in ips]

    # 3. 并发检测
    sem = asyncio.Semaphore(conn)
    aio_timeout = aiohttp.ClientTimeout(sock_connect=3, sock_read=timeout)

    start = time.perf_counter()
    async with aiohttp.ClientSession(timeout=aio_timeout) as session:
        tasks = [
            asyncio.create_task(check(session, url, aio_timeout))
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    # 4. 结果
    ok_cnt = sum(r[1] for r in results)
    print(f"检测结束：{len(results)} 条，成功 {ok_cnt} 条，耗时 {elapsed:.2f}s")

    with open("result.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cache_url", "alive", "error"])
        for url, ok, err in results:
            writer.writerow([url, ok, err or ""])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量扫描带缓存 IP 的 m3u8")
    parser.add_argument("template", help="IP 前缀，如 192.168.2 或 192.168")
    parser.add_argument("m3u8", help="原始 m3u8 地址")
    parser.add_argument("-t", "--timeout", type=int, default=5, help="读超时秒")
    parser.add_argument("-c", "--concurrency", type=int, default=300, help="并发")
    args = parser.parse_args()
    asyncio.run(main(args.template, args.m3u8, args.timeout, args.concurrency))
