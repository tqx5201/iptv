<?php
date_default_timezone_set('Asia/Shanghai');

$mgChannels = [
    '咪咕高清大片' => '629943678', 
    '咪咕红色轮播' => '713600957',
    '经典香港电影' => '625703337',
    '抗战经典影片' => '617432318',
    '咪咕新片放映' => '619495952',
    '咪咕高能悬疑' => '625133682',
];

// 缓存设置
$cacheDir = __DIR__ . '/epg_cache/';
if (!file_exists($cacheDir)) {
    mkdir($cacheDir, 0755, true);
}

$cacheFile = $cacheDir . 'e.xml';
$cacheTime = 86400; // 24小时缓存

// 检查缓存是否存在且未过期
if (file_exists($cacheFile) && (time() - filemtime($cacheFile) < $cacheTime)) {
    $epgContent = file_get_contents($cacheFile);
    header('Content-Type: application/xml; charset=utf-8');
    echo $epgContent;
    exit;
}

/* -------------------  HTTP 请求 ------------------- */
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
    $data = json_decode($response, true);
     if (json_last_error() !== JSON_ERROR_NONE) {
        return false;
    }
    
    return $data;
    
};

/* -------------------  生成节目XML ------------------- */
function generateProgramXml($channel, $start, $end, $title, $desc = '') {
    $startFmt = date('YmdHis O', $start);
    $endFmt = date('YmdHis O', $end);
    $title = htmlspecialchars($title);
    $desc = htmlspecialchars($desc);
    
    $xml = '<programme channel="' . $channel . '" start="' . $startFmt . '" stop="' . $endFmt . '">' . PHP_EOL;
    $xml .= '    <title lang="zh">' . $title . '</title>' . PHP_EOL;
    if (!empty($desc)) {
        $xml .= '    <desc lang="zh">' . $desc . '</desc>' . PHP_EOL;
    }
    $xml .= '</programme>' . PHP_EOL;
    
    return $xml;
}

// 初始化EPG内容
$epgContent = '<?xml version="1.0" encoding="UTF-8"?>' . PHP_EOL;
$epgContent .= '<tv>' . PHP_EOL;

// 添加所有频道信息
foreach (array_keys($mgChannels) as $channelName) {
    $epgContent .= "\t<channel id=\"{$channelName}\">" . PHP_EOL;
    $epgContent .= "\t\t<display-name lang=\"zh\">{$channelName}</display-name>" . PHP_EOL;
    $epgContent .= "\t</channel>" . PHP_EOL;
}

/* -------------------  处理咪咕频道 ------------------- */
   $today = date('Ymd'); // 咪咕API使用Ymd格式日期
   $tomorrow = date('Ymd', strtotime('+1 day'));
   
   foreach ($mgChannels as $channelName => $channelId) {
       //$dates = [$today, $tomorrow];
       $dates = [$today];
       foreach ($dates as $date) {
           $url = "https://program-sc.miguvideo.com/live/v2/tv-programs-data/{$channelId}/{$date}";
           $data = httpGet($url, 'https://www.miguvideo.com/');
           
           // 检查数据是否有效
           if (!$data || !isset($data['body']['program'][0]['content']) || $data['code'] != 200) {
               continue;
           }
           
           // 处理节目数据
           foreach ($data['body']['program'][0]['content'] as $program) {
               $startTime = $program['startTime'] / 1000; // 转换为秒
               $endTime = $program['endTime'] / 1000;     // 转换为秒
               
               $epgContent .= generateProgramXml($channelName, $startTime, $endTime, $program['contName']);
           }
       }
   }


$epgContent .= '</tv>';
// 清除旧缓存
if (file_exists($cacheFile)) {
    unlink($cacheFile);
}
// 保存到缓存
file_put_contents($cacheFile, $epgContent);
// 输出EPG内容
header('Content-Type: application/xml; charset=utf-8');
echo $epgContent;
?>
