#!/bin/bash
#在线测试https://www.jyshare.com/compile/18/


# 定义函数
get_ip_fofa() {
    url_fofa=$1
    ipfile=$2
    only_good_ip=$3
    echo "$url_fofa,$ipfile,$only_good_ip"
    echo
}


function get_ip_fofa(){
    # 搜索最新 IP
    echo "===============从 fofa 检索 ${city}的ip+端口================="
    curl -o test.html "$1"
    #echo $url_fofa
    echo "$ipfile"
    grep -E '^\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' test.html | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+' > "$ipfile"
    rm -f test.html
    # 遍历文件 A 中的每个 IP 地址
    while IFS= read -r ip; do
        # 尝试连接 IP 地址和端口号，并将输出保存到变量中
        tmp_ip=$(echo -n "$ip" | sed 's/:/ /')
        echo "nc -w 1 -v -z $tmp_ip 2>&1"
        output=$(nc -w 1 -v -z $tmp_ip 2>&1)
        echo $output    
        # 如果连接成功，且输出包含 "succeeded"，则将结果保存到输出文件中
        if [[ $output == *"succeeded"* ]]; then
            # 使用 awk 提取 IP 地址和端口号对应的字符串，并保存到输出文件中
            echo "$output" | grep "succeeded" | awk -v ip="$ip" '{print ip}' >> "$only_good_ip"
        fi
    done < "$ipfile"

    echo "===============检索完成================="
}


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
base_url="https://fofa.info/result?qbase64="

# 遍历省份数组和运营商类型数组，生成 URL 并下载文件
for province in "${provinces[@]}"; do
    for provider in "${providers[@]}"; do
        # 拼接完整的 URL
        asn=""
        if [ "$provider" = "电信" ]; then
            asn="4812"
        elif [ "$provider" = "移动" ]; then
            asn="9808"
        else
            asn="4808"
        fi
        query='"udpxy" && country="CN" && region="'$province'" && asn="'$asn'" && protocol="http"'
        url_fofa=$(echo -n "$query" | base64 | tr -d '\n')
        full_url="${base_url}${url_fofa}"
        echo "${full_url}"

        ipfile="ip/${province}_${provider}.ip"
        only_good_ip="ip/${province}_${provider}.onlygood.ip"
        get_ip_fofa "${full_url}" "${ipfile}" "${only_good_ip}"
    done
done

