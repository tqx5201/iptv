<?php
date_default_timezone_set('Asia/Shanghai');
set_time_limit(0);

// 缓存设置
$cacheDir = __DIR__ . '/epg_cache/';
if (!file_exists($cacheDir)){
    mkdir($cacheDir, 0755, true);
}
$cacheFile = $cacheDir . 'epg_tv189.xml';
$cacheTime = 86400;
// 24小时缓存
// 检查缓存是否存在且未过期
/*
if (file_exists($cacheFile) && (time() - filemtime($cacheFile) < $cacheTime)){
    $epgContent = file_get_contents($cacheFile);
    header('Content-Type: application/xml; charset=utf-8');
    echo $epgContent;
    exit;
}
*/
$mgChannels = [
    "TV189_24h轮播" => "C8000000000000000001658200465881",
    "TV189_传奇剧场" => "C8000000000000000001586755568202",
    "TV189_热血剧场" => "C8000000000000000001586755334304",
    "TV189_往昔影院" => "C8000000000000000001681195984396",
    "TV189_生活剧场" => "C8000000000000000001587975283115",
    "TV189_国产佳作" => "C8000000000000000001698305874412",
    "TV189_岁月男神" => "C8000000000000000001698218775729",
    "TV189_心动投送" => "C8000000000000000001698298656887",
    "TV189_宅家剧场" => "C8000000000000000001698297745509",
    "TV189_怀旧经典" => "C8000000000000000001681196041195",
    "TV189_放映厅" => "C8000000000000000001659935357556",
    "TV189_红色经典" => "C8000000000000000001681368925801",
    "TV189_大咖面对面" => "C8000000000000000001658992595677",
    "TV189_周润发系列" => "C8000000000000000001680847039258",
];

// 初始化EPG内容
$epgContent = '<?xml version="1.0" encoding="UTF-8"?>' . PHP_EOL;
$epgContent .= '<tv>' . PHP_EOL;
// 添加所有频道信息
foreach (array_keys($mgChannels) as $channelName) {
    $epgContent .= "\t<channel id=\"{$channelName}\">" . PHP_EOL;
    $epgContent .= "\t\t<display-name lang=\"zh\">{$channelName}</display-name>" . PHP_EOL;
    $epgContent .= "\t</channel>" . PHP_EOL;
}

/* ------------------- 处理咪咕频道 ------------------- */
$today = date('Ymd');
$time = date('YmdHis');
$tomorrow = date('Ymd', strtotime('+1 day'));
foreach ($mgChannels as $channelName => $channelId){
    //echo $channelName;echo '<br>';
    foreach ([$today] as $date) {
        // 想加明天就把 $tomorrow 也写进来
        // 1. 干净接口
        $url = 'https://h5.nty.tv189.com/bff/apis/content/liveschedule?';
        //cltrid=4208f2f3-f3de-46d5-94c6-d1d118a73e32&liveid=C8000000000000000001754380362525&date=20260223&cltts=20260225192147&cltkey=f07beba7e598ca07f027cb205b2264be
        $p = "cltrid=0b01aaee-a979-4c9e-928e-52cbc0c5891b&liveid=$channelId&cltts=$time&";
        $k = md5($p);
        $url .= $p;
        $url .= 'cltkey='.$k;
    
        // 2. 取回 JSONP
        $json = httpGet($url);
        //echo $json;exit;
        if (!$json) {
            continue;
        }
        // 4. 解析
        $data = json_decode($json, true);
        if (!$data){
            continue;
        }
        // 5. 写 XML
        foreach ($data['info'] as $p){
            //var_dump($p['title']);
            $epgContent .= generateProgramXml(
            $channelName,
            strtotime($p['starttime']),
            strtotime($p['endtime']),
            $p['title']
            );
        }
        //var_dump($epgContent);exit;
    }
    //exit;
}
$epgContent .= '</tv>';
// 清除旧缓存
if (file_exists($cacheFile)){
    unlink($cacheFile);
}
// 保存到缓存
file_put_contents($cacheFile, $epgContent);
// 输出EPG内容
header('Content-Type: application/xml; charset=utf-8');
echo $epgContent;



/* ------------------- HTTP 请求 ------------------- */
function httpGet($url,$Referer='') {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer: '.$Referer,
    'Accept: application/json, text/plain, */*'
    ]);
    $response = curl_exec($ch);
    if (curl_errno($ch)) {
        curl_close($ch);
        return false;
    }
    curl_close($ch);
    return $response;
};
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





?>
