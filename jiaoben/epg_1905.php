<?php
date_default_timezone_set('Asia/Shanghai');
set_time_limit(0); // 

$date = $today = date('Ymd');echo $date;

$Channels = [
    '1905国内经典' => 'series',
    '1905环球经典' => 'cctv6networkv2',
    'CCTV6' => '340',
    'CHC家庭' => '341',
    'CMC北美' => '342',
    'CMC香港' => '343'
];
// 缓存设置
$cacheDir = __DIR__.'/epg_cache/';
if (!file_exists($cacheDir)) {
    mkdir($cacheDir, 0755, true);
}
$cacheFile = $cacheDir.'epg_1905.xml';
$cacheTime = 86400;
// 24小时缓存
// 检查缓存是否存在且未过期
if (file_exists($cacheFile) && (time() - filemtime($cacheFile) < $cacheTime)) {
    $epgContent = file_get_contents($cacheFile);
    header('Content-Type: application/xml; charset=utf-8');
    echo $epgContent;
    exit;
}
/* ------------------- 生成节目XML ------------------- */
function generateProgramXml($channel, $start, $end, $title, $desc = '') {
    $startFmt = date('YmdHis O', $start);
    $endFmt = date('YmdHis O', $end);
    $title = htmlspecialchars($title);
    $desc = htmlspecialchars($desc);
    $xml = "\t<programme channel=\"{$channel}\" start=\"{$startFmt}\" stop=\"{$endFmt}\">".PHP_EOL;
    $xml.= "\t\t<title lang=\"zh\">{$title}</title>".PHP_EOL;
    if (!empty($desc)) {
        $xml .= "\t\t<desc lang=\"zh\">{$desc}</desc>".PHP_EOL;
    }
    $xml.= "\t</programme>".PHP_EOL;
    return $xml;
}

// 初始化EPG内容
$epgContent = '<?xml version="1.0" encoding="UTF-8"?>'.PHP_EOL;
$epgContent.= '<tv>'.PHP_EOL;
// 添加所有频道信息
foreach(array_keys($Channels) as $channelName) {
    $epgContent.= "\t<channel id=\"{$channelName}\">".PHP_EOL;
    $epgContent.= "\t\t<display-name lang=\"zh\">{$channelName}</display-name>".PHP_EOL;
    $epgContent.= "\t</channel>".PHP_EOL;
}
/* ------------------- 处理频道 ------------------- */
$date = $today = date('Ymd');echo $date;
//使用Ymd格式日期
$tomorrow = date('Ymd', strtotime('+1 day'));
foreach($Channels as $channelName => $channelId) {
    if (is_numeric($channelId)) {
        $api = "https://www.1905.com/api/content/?m=Epginfo&a=getPcinfo&cid={$channelId}&dt={$date}&_=";
    } else {
        $api = "https://m.1905.com/m/api/epginfo/{$channelId}/?isweek=1&d={$date}&_=";
    }
    $data = httpGet($api);
    //var_dump($data);exit;
    // 检查数据是否有效
    if (!$data) {
        continue;
    }
    // 处理节目数据
    $list = $data['list'];
    //echo count($list);
    foreach($list as $k => $v) {
        $startTime = $v['timeU'];
        if (($k + 1) < count($list)) {
            $endTime = $list[$k + 1]['timeU'];
        } else {
            $endTime = strtotime($today.' 23:59:59');
        }
        $epgContent.= generateProgramXml($channelName, $startTime, $endTime, $v['title']);
    }
}
$epgContent.= '</tv>';
// 清除旧缓存
if (file_exists($cacheFile)) {
    unlink($cacheFile);
}
// 保存到缓存
file_put_contents($cacheFile, $epgContent);
// 输出EPG内容
header('Content-Type: application/xml; charset=utf-8');
echo $epgContent;
/* ------------------- HTTP 请求 ------------------- */
function httpGet($url, $Referer = '') {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);

    $response = curl_exec($ch);
    if (curl_errno($ch)) {
        curl_close($ch);
        return false;
    }
    curl_close($ch);
    $data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        return false;
    }
    return $data;
}

?>
