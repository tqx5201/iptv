#!/bin/bash
# cd /root/iptv
# read -p "确定要运行脚本吗？(y/n): " choice

# 判断用户的选择，如果不是"y"则退出脚本
# if [ "$choice" != "y" ]; then
#     echo "脚本已取消."
#     exit 0
# fi

time=$(date +%m%d%H%M)
i=0

if [ $# -eq 0 ]; then
  echo "请选择城市："
  echo "1. 上海电信（Shanghai_103）"
  echo "2. 北京联通（Beijing_liantong_145）"
  echo "3. 四川电信（Sichuan_333）"
  echo "4. 浙江电信（Zhejiang_120）"
  echo "5. 北京电信（Beijing_dianxin_186）"
  echo "6. 江苏（Jiangsu）"
  echo "7. 广东电信（Guangdong_332）"
  echo "8. 河南电信（Henan_327）"
  echo "9. 山西电信（Shanxi_117）"
  echo "10. 天津联通（Tianjin_160）"
  echo "11. 湖北电信（Hubei_90）"
  echo "12. 福建电信（Fujian_114）"
  echo "13. 湖南电信（Hunan_282）"
  echo "14. 甘肃电信（Gansu_105）"
  echo "15. 河北联通（Hebei_313）"
  echo "0. 全部"
  read -t 10 -p "输入选择或在10秒内无输入将默认选择全部: " city_choice

  if [ -z "$city_choice" ]; then
      echo "未检测到输入，自动选择全部选项..."
      city_choice=0
  fi

else
  city_choice=$1
fi
city_choice=3

# 根据用户选择设置城市和相应的stream
case $city_choice in
    1)
        city="Shanghai_103"
        stream="udp/239.45.1.4:5140"
        channel_key="上海"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Shanghai" && org="China Telecom Group" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    2)
        city="Beijing_liantong_145"
        stream="rtp/239.3.1.236:2000"
        channel_key="北京联通"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Beijing" && org="China Unicom Beijing Province Network" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    3)
        city="Sichuan_333"
        stream="udp/239.93.42.33:5140"
        channel_key="四川电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Sichuan" && org="CHINA UNICOM China169 Backbone"  && protocol="http"' | base64 |tr -d '\n')
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Sichuan" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    4)
        city="Zhejiang_120"
        stream="rtp/233.50.201.63:5140"
        channel_key="浙江电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Zhejiang" && org="Chinanet" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    5)
        city="Beijing_dianxin_186"
        stream="udp/225.1.8.80:2000"
        channel_key="北京电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Beijing" && org="China Networks Inter-Exchange"  && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    6)
        city="Jiangsu"
        stream="udp/239.49.8.19:9614"
        channel_key="江苏"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Jiangsu" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    7)
        city="Guangdong_332"
        stream="udp/239.77.1.98:5146"
        channel_key="广东电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Guangdong" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    8)
        city="Henan_327"
        stream="rtp/239.16.20.1:10010"
        channel_key="河南电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Henan" && city="Zhengzhou"  && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    9)
        city="Shanxi_117"
        stream="udp/239.1.1.7:8007"
        channel_key="山西电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Shanxi" && city="Taiyuan" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    10)
        city="Tianjin_160"
        stream="udp/225.1.2.190:5002"
        channel_key="天津联通"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Tianjin" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    11)
        city="Hubei_90"
        stream="rtp/239.254.96.96:8550"
        channel_key="湖北电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Hubei" && city="Wuhan" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    12)
        city="Fujian_114"
        stream="rtp/239.61.2.183:9086"
        channel_key="福建电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Fujian" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    13)
        city="Hunan_282"
        stream="udp/239.76.252.35:9000"
        channel_key="湖南电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Hunan" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    14)
        city="Gansu_105"
        stream="udp/239.255.30.123:8231"
        channel_key="甘肃电信"
        url_fofa=$(echo  '"udpxy" && country="CN" && region="Gansu" && city="Lanzhou" && protocol="http"' | base64 |tr -d '\n')
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    15)
        city="Hebei_313"
        stream="rtp/239.253.93.134:6631"
        channel_key="河北联通"
        url_fofa=$(echo ""udpxy" && country="CN" && region="Hebei"  && protocol="http"" | base64)
        url_fofa="https://fofa.info/result?qbase64="$url_fofa
        ;;
    0)
        # 如果选择是“全部选项”，则逐个处理每个选项
        for option in {1..15}; do
          bash  "$0" $option  # 假定fofa.sh是当前脚本的文件名，$option将递归调用
        done
        exit 0
        ;;

    *)
        echo "错误：无效的选择。"
        exit 1
        ;;
esac

echo "===============删除存在的文件================="
#rm -rf txt/*

# 使用城市名作为默认文件名，格式为 CityName.ip
ipfile="ip/${city}.ip"
only_good_ip="ip/${city}.onlygood.ip"
rm -f $only_good_ip
rm -f $ipfile
rm -f "ip/${city}.port"
rm -f "result/result_fofa_${city}.txt"

# 搜索最新 IP
echo "===============从 fofa 检索 ${city}的ip+端口================="
curl -o test.html "$url_fofa"
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

# 检查文件是否存在
if [ ! -f "$only_good_ip" ]; then
    echo "错误：文件 $only_good_ip 不存在。"
    exit 1
fi

lines=$(wc -l < "$only_good_ip")
echo "【$only_good_ip】内 ip 共计 $lines 个"

line_i=0
mkdir -p tmpip
while read -r line; do
    ip=$(echo "$line" | sed 's/^[ \t]*//;s/[ \t]*$//')  # 去除首尾空格
    
    # 如果行不为空，则写入临时文件
    if [ -n "$ip" ]; then
        echo "$ip" > "tmpip/ip_$line_i.txt"  # 保存为 tmpip 目录下的临时文件
        ((line_i++))
    fi
done < "$only_good_ip"

line_i=0
for temp_file in tmpip/ip_*.txt; do
      ((line_i++))
     ip=$(<"$temp_file")  # 从临时文件中读取 IP 地址
     a=$(./speed.sh "$ip" "$stream")
     echo "第 $line_i/$lines 个：$ip $a"
     echo "$ip $a" >> "speedtest_${city}_$time.log"
done
rm -rf tmpip/*

awk '/M|k/{print $2"  "$1}' "speedtest_${city}_$time.log" | sort -n -r >"result/result_fofa_${city}.txt"
cat "result/result_fofa_${city}.txt"
ip1=$(awk 'NR==1{print $2}' result/result_fofa_${city}.txt)
ip2=$(awk 'NR==2{print $2}' result/result_fofa_${city}.txt)
ip3=$(awk 'NR==3{print $2}' result/result_fofa_${city}.txt)
rm -f "speedtest_${city}_$time.log"

# 用 3 个最快 ip 生成对应城市的 txt 文件
program="template/template_${city}.txt"
#判断ip不为空
if [ -n "$ip1" ]; then
  sed "s/ipipip/$ip1/g" "$program" > tmp1.txt
fi
if [ -n "$ip2" ]; then
  sed "s/ipipip/$ip2/g" "$program" > tmp2.txt
fi
if [ -n "$ip3" ]; then
  sed "s/ipipip/$ip3/g" "$program" > tmp3.txt
fi
#cat tmp1.txt tmp2.txt tmp3.txt > "txt/fofa_${city}.txt"
# 合并临时文件到最终文件
{
  [ -f "tmp1.txt" ] && cat tmp1.txt
  [ -f "tmp2.txt" ] && cat tmp2.txt
  [ -f "tmp3.txt" ] && cat tmp3.txt
} > "txt/fofa_${city}.txt"

rm -rf tmp1.txt tmp2.txt tmp3.txt

echo "===============-合并所有城市的txt文件为:zubo_fofa.txt================="
output_file="zubo_fofa.txt"
for file in txt/fofa_*.txt;do
     #filename=$(basename "$file")
     filename=$(basename "$file" | sed 's/_/-/g')
     echo "$filename"
     echo "$filename,#genre#" >> "$output_file"
     cat "$file" >> "$output_file"
     echo "" >> "$output_file"
done

# for a in result/*.txt; do echo "";echo "========================= $(basename "$a") ==================================="; cat $a; done
