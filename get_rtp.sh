#!/bin/bash

# 定义省份名称数组
provinces=(
    "北京" "天津" "上海" "重庆"
    "河北" "山西" "辽宁" "吉林" "黑龙江"
    "江苏" "浙江" "安徽" "福建" "江西" "山东"
    "河南" "湖北" "湖南" "广东" "广西" "海南"
    "四川" "贵州" "云南" "西藏" "陕西" "甘肃"
    "青海" "台湾" "内蒙古" "宁夏" "新疆"
)

# 定义运营商类型数组
providers=("电信" "移动" "联通")

# 基础 URL
base_url="https://raw.bgithub.xyz/tqx5201/iptv-api/refs/heads/master/config/rtp/"

# 创建 rtp 目录（如果不存在）
mkdir -p rtp

# 遍历省份数组和运营商类型数组，生成 URL 并下载文件
for province in "${provinces[@]}"; do
    for provider in "${providers[@]}"; do
        # 对省份名称和运营商类型进行 URL 编码
        encoded_province=$(echo -n "$province" | jq -sRr @uri)
        encoded_provider=$(echo -n "$provider" | jq -sRr @uri)
        # 拼接完整的 URL
        full_url="${base_url}${encoded_province}_${encoded_provider}.txt"
        # 定义本地文件路径
        local_file="rtp/${province}_${provider}.txt"
        # 使用 curl 下载文件
        echo "Downloading $full_url to $local_file"
        curl -s -o "$local_file" "$full_url"
        if [ $? -eq 0 ]; then
            echo "Downloaded successfully: $local_file"
        else
            echo "Failed to download: $full_url"
        fi
    done
done
