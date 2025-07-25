# save as scan_loop_v4.py
import asyncio, aiohttp, csv
from typing import List, Tuple
#pip install asyncio, aiohttp, csv,typing

# ============ 单地址配置 =============
ORIGINAL_URL = "https://hlslive-tx-cdn.ysp.cctv.cn/2022576702.m3u8"   # 改成你的
TIMEOUT      = 5                             # 单次超时
CONCURRENCY  = 300                           # 并发协程数
OUTPUT_FILE  = "epg/scan_result.csv"
# ====================================

semaphore = asyncio.Semaphore(CONCURRENCY)

def build_cache_urls(original: str) -> List[str]:
    """
    用两层循环拼 192.168.x.y
    """
    host_suffix = original.replace("http://", "", 1)  # example.com/1.m3u8
    urls = []
    for x in range(1, 256):          # 192.168.x.*
        for y in range(1, 256):      # 192.168.x.y
            urls.append(f"http://111.51.{x}.{y}/{host_suffix}")
    return urls

async def check(session: aiohttp.ClientSession, url: str) -> Tuple[str, bool]:
    async with semaphore:
        try:
            async with session.get(url, timeout=TIMEOUT) as resp:
                ok = resp.status == 200
        except Exception:
            ok = False
        return url, ok

async def main() -> None:
    urls = build_cache_urls(ORIGINAL_URL)
    async with aiohttp.ClientSession() as session:
        tasks = [check(session, u) for u in urls]
        results = await asyncio.gather(*tasks)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cache_url", "alive"])
        writer.writerows(results)
    print(f"共检测 {len(results)} 条缓存地址，结果写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
