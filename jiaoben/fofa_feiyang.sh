#!/bin/bash
#设置时区
export TZ=Asia/Shanghai
ip_file="ip/feiyang.txt"
rm -rf ip/feiyang.txt
base_url="https://fofa.info/result?qbase64="
query='"请求成功，当前ALLINONE版本构建时间为"'
url_fofa=$(echo -n "$query" | base64 | tr -d '\n')
full_url="${base_url}${url_fofa}"
echo "${full_url}"
if grep -q '\[-3000\] IP访问异常，疑似为爬虫被暂时禁止访问，登录账号可用。' "$html"; then
        echo "检测到错误信息：IP访问异常，疑似为爬虫被暂时禁止访问。"
        #exit 1
    else
        echo "未检测到错误信息。"
    fi

    ips=$(grep -E '^\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' "$html" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+')
    
    # 初始化一个变量来存储成功连接的 IP 和端口
    good_ips=""

    for tmp_ip in $ips; do
        tmpip=$(echo -n "$tmp_ip" | sed 's/:/ /')
        echo "  是否可连接：nc -w 1 -v -z $tmpip 2>&1"
        output=$(nc -w 1 -v -z $tmpip 2>&1)
        echo "  $output"
        # 如果连接成功，且输出包含 "succeeded"，则将结果添加到变量中
        if [[ $output == *"succeeded"* ]]; then
            # 将成功的 IP 和端口添加到变量中，每个条目用换行符分隔
                echo -e "$good_ips"
                echo -e "$good_ips" >> "$ipfile"

        fi
    done
    echo "===============检索完成================="
    echo ""
    echo ""
