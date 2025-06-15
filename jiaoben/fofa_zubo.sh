#!/bin/bash
#设置时区
export TZ=Asia/Shanghai


#在线测试https://www.jyshare.com/compile/18/

# 创建目录
#rm -rf ip/*
#mkdir -p ip

#rm -rf txt/*
#mkdir -p txt


function speed_test(){
    # IPTV 地址
    URL="$1"
    #echo "$URL"
    # 输出文件名
    OUTPUT_FILE="temp_video.mp4" 

    # 开始时间
    START_TIME=$(date +%s)

    # 使用 ffmpeg 下载视频并保存 10 秒  10秒超时
    ffmpeg -timeout 10000000 -i "$URL" -t 10 -c copy "$OUTPUT_FILE" -y 2>/dev/null

    # 检查 ffmpeg 的退出状态
    if [ $? -ne 0 ]; then
        #echo "下载失败，速度为 0 Mb/s"
        echo "0"
        exit 0
    fi

    # 结束时间
    END_TIME=$(date +%s)

    # 计算下载时长
    DURATION=$((END_TIME - START_TIME))

    # 获取文件大小（以字节为单位）
    FILE_SIZE=$(stat -c%s "$OUTPUT_FILE")
    # 计算下载速度（字节/秒）
    DOWNLOAD_SPEED=$(echo "scale=2; $FILE_SIZE / $DURATION" | bc)
    # 将下载速度转换为 Mb/s
    DOWNLOAD_SPEED_MBPS=$(echo "scale=2; $DOWNLOAD_SPEED * 8 / 1000000" | bc)
    # 判断 DOWNLOAD_SPEED_MBPS 是否小于 1M，速度太慢的节点不要也罢
    if (( $(echo "$DOWNLOAD_SPEED_MBPS < 1" | bc -l) )); then
        DOWNLOAD_SPEED_MBPS=0
    fi

    # 输出结果
    echo "$DOWNLOAD_SPEED_MBPS Mb/s"
}

function make_zubo(){
    for tmp_file in ip/*_测速.txt;do
        filename=$(basename "$tmp_file")
        province=$(echo "$filename" | cut -d'_' -f1)
        provider=$(echo "$filename" | cut -d'_' -f2)
        awk '/M|k/{print $2"  "$1}' "ip/${province}_${provider}_测速.txt" | sort -n -r > "ip/${province}_${provider}_排序.txt"
        if [ ! -s "ip/${province}_${provider}_排序.txt" ]; then
            echo "排序文件 $sorted_file 为空，可能没有符合条件的行"
            continue
        fi

        cat "ip/${province}_${provider}_排序.txt"
        ip1=$(awk 'NR==1{print $2}' ip/${province}_${provider}_排序.txt)
        ip2=$(awk 'NR==2{print $2}' ip/${province}_${provider}_排序.txt)
        ip3=$(awk 'NR==3{print $2}' ip/${province}_${provider}_排序.txt)

        # 用 3 个最快 ip 生成对应城市的 txt 文件
        template="rtp/${province}_${provider}.txt"
        #判断ip不为空
        if [ -n "$ip1" ]; then
            sed "s/rtp:\/\//http:\/\/$ip1\/udp\//g" "$template" > tmp1.txt
        fi
        if [ -n "$ip2" ]; then
            sed "s/rtp:\/\//http:\/\/$ip2\/udp\//g" "$template" > tmp2.txt
        fi
        if [ -n "$ip3" ]; then
            sed "s/rtp:\/\//http:\/\/$ip3\/udp\//g" "$template" > tmp3.txt
        fi
        #cat tmp1.txt tmp2.txt tmp3.txt > "txt/fofa_${province}_${provider}.txt"
        # 合并临时文件到最终文件
        {
            [ -f "tmp1.txt" ] && cat tmp1.txt
            [ -f "tmp2.txt" ] && cat tmp2.txt
            [ -f "tmp3.txt" ] && cat tmp3.txt
        } > "txt/fofa_${province}_${provider}.txt"

        rm -rf tmp1.txt tmp2.txt tmp3.txt
    done

    rm -rf zubo_fofa.txt
    echo "===============合并所有城市的txt文件为:zubo_fofa.txt================="
    output_file="zubo_fofa.txt"
    for file in txt/fofa_*.txt;do
        if [ ! -s "${file}" ]; then
            echo "$file文件为空，不添加"
            continue
        fi
        echo "添加$file"
        #filename=$(basename "$file")
        filename=$(basename "$file" | sed 's/_/-/g' | sed 's/fofa-//g' | sed 's/.txt//g')
        echo "$filename,#genre#" >> "$output_file"
        cat "$file" >> "$output_file"
        echo "" >> "$output_file"
    done

}

function get_ip_fofa(){
    url_fofa=$1
    province=$2
    provider=$3
    ipfile="ip/${province}_${provider}.txt"
    html="ip/${province}_${provider}.html"
    ip_speedtest="ip/${province}_${provider}_测速.txt"
    rm -rf "$ipfile"
    rm -rf "$ip_speedtest"

    # 假设文件名为 file.txt
    file="rtp/${province}_${provider}.txt"
    # 取出第一行内容
    first_line=$(head -n 1 "$file")
    # 使用逗号分割并提取第二部分（即rtp部分）
    rtp_part=$(echo "$first_line" | cut -d ',' -f 2)
    # 将 rtp:// 替换为 udp/
    stream=$(echo "$rtp_part" | sed 's/rtp:\/\//udp\//')
    # 输出结果
    echo "$stream"

    # 搜索最新 IP
    echo "===============从 fofa 检索【 ${province}_${provider} 】的ip+端口================="
    # 使用 curl 获取内容并保存到变量中
    #response=$(curl -L -s "$url_fofa")
    #echo "$response"
    # 使用正则表达式提取IP和端口
    #ips=$(grep -E '^\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' <<< "$response" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+')

    curl -o "$html" "$url_fofa"
    if grep -q '\[-3000\] IP访问异常，疑似为爬虫被暂时禁止访问，登录账号可用。' "$html"; then
        echo "检测到错误信息：IP访问异常，疑似为爬虫被暂时禁止访问。"
        exit 1
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
            
            echo "  ************测速开始************"
            echo "    http://$tmp_ip/$stream"
            if [[ $stream =~ ^udp ]]; then
                #a=$(./speedtest/speed.sh "$tmp_ip" "$stream")
                a=$(speed_test "http://$tmp_ip/$stream")
                #echo "第 $line_i/$lines 个：$ip $a"
                echo "    ip:$tmp_ip,连接速度:$a"
                echo "$tmp_ip $a" >> "$ip_speedtest"
            else
                echo "    错误的rtp地址"
            fi
            echo "  ************测速结束************"
            
        fi
    done
    echo "===============检索完成================="
    echo ""
    echo ""
}

function get_zubo_ip_day_hour(){
    # 定义省份名称数组
    provinces_cn=$1
    provinces_en=$2
    providers=$3
    # 基础 URL
    base_url="https://fofa.info/result?qbase64="

    # 获取数组长度
    len=${#provinces_cn[@]}

    # 遍历数组
    #for ((i=0; i<len; i++)); do

        # 获取当前的小时数（24小时制）
        current_hour=$(date +"%H")
        # 去掉前导零
        current_hour=${current_hour#0}
        current_day=$(date +"%d")
        # 根据日期的奇偶性决定起始索引
        if (( current_day % 2 == 1 )); then  # 奇数天
            start_index=0
        else  # 偶数天
            start_index=24
        fi

        # 计算当前取出的数据索引
        i=$(( (start_index + current_hour) % len ))

        province_cn=${provinces_cn[i]}
        province_en=${provinces_en[i]}
        for provider in "${providers[@]}"; do
            asn=""
            # 根据运营商名称设置 ASN 条件
            if [ "$provider" = "电信" ]; then
                asn='(asn="4134" || asn="4847" || asn="4809" || asn="4812" || asn="4842" || asn="138011" || asn="140330" || asn="140061")'
            elif [ "$provider" = "移动" ]; then
                asn='(asn="9808" || asn="56044" || asn="56045" || asn="56046" || asn="56047"
 || asn="56048" || asn="56049" || asn="56050" || asn="56051" || asn="56052")'
            elif [ "$provider" = "联通" ]; then
                asn='(asn="17621" || asn="4837" || asn="4808" || asn="55491")'
            else
                asn='asn=""'  # 如果不是已知运营商，设置为空
            fi

            query='"udpxy" && country="CN" && region="'$province_en'" && '$asn' && protocol="http"'
            url_fofa=$(echo -n "$query" | base64 | tr -d '\n')
            full_url="${base_url}${url_fofa}"
            echo "${full_url}"
            
            # 假设 get_ip_fofa 是一个函数，用于处理 URL 并保存 IP 到文件
            # 你需要定义这个函数或确保它已经定义

            # 开始时间
            START_TIME=$(date +%s)
            #获取IP地址
            get_ip_fofa "${full_url}" "${province_cn}" "${provider}"
            # 结束时间
            END_TIME=$(date +%s)
            # 计算下载时长
            DURATION=$((END_TIME - START_TIME))
            # 如果时长小于10秒，则暂停
            if [ $DURATION -lt 10 ]; then
                sleep $((10 - DURATION))
            fi
        done
    #done
}


function get_zubo_ip(){
    # 定义省份名称数组
    provinces_cn=$1
    provinces_en=$2
    providers=$3
    # 基础 URL
    base_url="https://fofa.info/result?qbase64="

    # 获取数组长度
    len=${#provinces_cn[@]}
    # 获取当前的小时数（24小时制）
    current_hour=$(date +"%H")
    # 去掉前导零
    current_hour=${current_hour#0}
    
    # 遍历数组
    for ((start_index=0; start_index<4; start_index++)); do
        # 计算当前取出的数据索引
        i=$(( (start_index + current_hour * 4) % len ))
        echo "正在获取第$i个"
        province_cn=${provinces_cn[i]}
        province_en=${provinces_en[i]}
        for provider in "${providers[@]}"; do
            asn=""
            # 根据运营商名称设置 ASN 条件
            if [ "$provider" = "电信" ]; then
                asn='(asn="4134" || asn="4847" || asn="4809" || asn="4812" || asn="4842" || asn="138011" || asn="140330" || asn="140061")'
            elif [ "$provider" = "移动" ]; then
                asn='(asn="9808" || asn="56044" || asn="56045" || asn="56046" || asn="56047"
 || asn="56048" || asn="56049" || asn="56050" || asn="56051" || asn="56052")'
            elif [ "$provider" = "联通" ]; then
                asn='(asn="17621" || asn="4837" || asn="4808" || asn="55491")'
            else
                asn='asn=""'  # 如果不是已知运营商，设置为空
            fi

            query='"udpxy" && country="CN" && region="'$province_en'" && '$asn' && protocol="http"'
            url_fofa=$(echo -n "$query" | base64 | tr -d '\n')
            full_url="${base_url}${url_fofa}"
            echo "${full_url}"

            # 开始时间
            START_TIME=$(date +%s)
            #获取IP地址
            get_ip_fofa "${full_url}" "${province_cn}" "${provider}"
            # 结束时间
            END_TIME=$(date +%s)
            # 计算下载时长
            DURATION=$((END_TIME - START_TIME))
            # 如果时长小于30秒，则暂停
            if [ $DURATION -lt 30 ]; then
                sleep $((30 - DURATION))
            fi
        done
    done
}


# 定义省份名称数组
    provinces_cn=(
        "北京" "天津" "上海" "重庆"
        "河北" "山西" "辽宁" "吉林" "黑龙江"
        "江苏" "浙江" "安徽" "福建" "江西" "山东"
        "河南" "湖北" "湖南" "广东" "广西" "海南"
        "四川" "贵州" "云南" "西藏" "陕西" "甘肃"
        "青海" "内蒙古" "宁夏" "新疆"
    )
        #"香港" "澳门" "台湾" )

        #!/bin/bash

    provinces_cn=(
        "北京" "天津" "河北" "山西" "内蒙古"
        "辽宁" "吉林" "黑龙江"
        "上海" "江苏" "浙江" "安徽" "福建" "江西" "山东"
        "河南" "湖北" "湖南" "广东" "广西" "海南"
        "重庆" "四川" "贵州" "云南" "西藏"
        "陕西" "甘肃" "青海" "宁夏" "新疆"
    )
    #"台湾" "香港" "澳门")


    provinces_en=(
        "Beijing" "Tianjin" "Shanghai" "Chongqing"
        "Hebei" "Shanxi" "Liaoning" "Jilin" "Heilongjiang"
        "Jiangsu" "Zhejiang" "Anhui" "Fujian" "Jiangxi" "Shandong"
        "Henan" "Hubei" "Hunan" "Guangdong" "Guangxi Zhuangzu" "Hainan"
        "Sichuan" "Guizhou" "Yunnan" "Xizang" "Shaanxi" "Gansu"
        "Qinghai" "Nei Mongol" "Ningxia Huizu" "Xinjiang Uygur"
    )    
        #"HK" "MO" "TW" )

    # 定义省份名称数组
    #provinces_cn=("湖南")
    #provinces_en=("Hunan")

    # 定义运营商类型数组
    #providers=("电信" "移动" "联通")
    providers=("电信")
get_zubo_ip $provinces_cn $provinces_en $providers
make_zubo
