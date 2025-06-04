#!/bin/bash
#在线测试https://www.jyshare.com/compile/18/

# 创建目录
rm -rf ip/*
mkdir -p ip


function get_ip_fofa(){
    url_fofa=$1
    province=$2
    provider=$3
    ipfile="ip/${province}_${provider}.ip"
    only_good_ip="ip/${province}_${provider}.onlygood.ip"

    # 搜索最新 IP
    echo "===============从 fofa 检索【 ${province}_${provider} 】的ip+端口================="
    # 使用 curl 获取内容并保存到变量中
    response=$(curl -s "$url_fofa")
    #echo "$response"
    # 使用正则表达式提取IP和端口
    ips=$(grep -E '^\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' <<< "$response" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+')

    # 初始化一个变量来存储成功连接的 IP 和端口
    good_ips=""

    for tmp_ip in $ips; do
        tmpip=$(echo -n "$tmp_ip" | sed 's/:/ /')
        echo "nc -w 1 -v -z $tmpip 2>&1"
        output=$(nc -w 1 -v -z $tmpip 2>&1)
        echo "$output"
        # 如果连接成功，且输出包含 "succeeded"，则将结果添加到变量中
        if [[ $output == *"succeeded"* ]]; then
            # 将成功的 IP 和端口添加到变量中，每个条目用换行符分隔
            good_ips+="$tmpip"$'\n'
        fi
    done

    # 输出成功连接的 IP 和端口
    echo "===============成功连接的 IP 和端口================="
    echo -e "$good_ips"
    echo -e "$good_ips" > "$ipfile"
    echo "===============检索完成================="
    echo ""
    echo ""
}


# 定义省份名称数组
provinces0=(
    "北京" "天津" "上海" "重庆"
    "河北" "山西" "辽宁" "吉林" "黑龙江"
    "江苏" "浙江" "安徽" "福建" "江西" "山东"
    "河南" "湖北" "湖南" "广东" "广西" "海南"
    "四川" "贵州" "云南" "西藏" "陕西" "甘肃"
    "青海" "台湾" "内蒙古" "宁夏" "新疆"
)

# 定义运营商类型数组
providers0=("电信" "移动" "联通")

# 定义省份名称数组
provinces=("Sichuan")

# 定义运营商类型数组
providers=("电信" "移动" "联通")

# 基础 URL
base_url="https://fofa.info/result?qbase64="

# 遍历省份数组和运营商类型数组，生成 URL 并下载文件
for province in "${provinces[@]}"; do
    for provider in "${providers[@]}"; do
        # 拼接完整的 URL
        asn=""
        if [ "$provider" = "电信" ]; then
            asn='asn="4134"'
        elif [ "$provider" = "移动" ]; then
            asn='asn="9808"'
        else
            asn='(asn="4837" || asn="4808")'
        fi
        query='"udpxy" && country="CN" && region="'$province'" && '$asn' && protocol="http"'
        url_fofa=$(echo -n "$query" | base64 | tr -d '\n')
        full_url="${base_url}${url_fofa}"
        echo "${full_url}"
        
        # 假设 get_ip_fofa 是一个函数，用于处理 URL 并保存 IP 到文件
        # 你需要定义这个函数或确保它已经定义
        get_ip_fofa "${full_url}" "${province}" "${provider}"
    done
done

