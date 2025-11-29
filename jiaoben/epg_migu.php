<?php
date_default_timezone_set('Asia/Shanghai');
set_time_limit(0);
$mgChannels = [
'CCTV1综合' => '608807420',
'CCTV2财经' => '631780532',
'CCTV3综艺' => '624878271',
'CCTV4中文国际' => '631780421',
'CCTV5体育' => '641886683',
'CCTV6电影' => '624878396',
'CCTV7国防军事' => '673168121',
'CCTV8电视剧' => '624878356',
'CCTV9纪录' => '673168140',
'CCTV10科教' => '624878405',
'CCTV11戏曲' => '667987558',
'CCTV12社会与法' => '673168185',
'CCTV13新闻' => '608807423',
'CCTV14少儿' => '624878440',
'CCTV15音乐' => '673168223',
'CCTV17农业农村' => '673168256',
'CCTV4欧洲' => '608807419',
'CCTV4美洲' => '608807416',
'CCTV5+体育赛事' => '641886773',
'CGTN' => '609017205',
'CGTN外语纪录' => '609006487',
'CGTN阿语' => '609154345',
'CGTN西语' => '609006450',
'CGTN法语' => '609006476',
'CGTN俄语' => '609006446',
'老故事' => '884121956',
'发现之旅' => '624878970',
'中学生' => '708869532',
'东方卫视' => '651632648',
'江苏卫视' => '623899368',
'广东卫视' => '608831231',
'江西卫视' => '783847495',
'河南卫视' => '790187291',
'陕西卫视' => '738910838',
'大湾区卫视' => '608917627',
'湖北卫视' => '947472496',
'吉林卫视' => '947472500',
'青海卫视' => '947472506',
'东南卫视' => '849116810',
'海南卫视' => '947472502',
'海峡卫视' => '849119120',
'中国农林卫视' => '956904896',
'兵团卫视' => '956923145',
'上海新闻综合' => '651632657',
'上视东方影视' => '617290047',
'上海第一财经' => '608780988',
'南京新闻综合频道' => '838109047',
'南京教科频道' => '838153729',
'南京十八频道' => '838151753',
'体育休闲频道' => '626064707',
'江苏城市频道' => '626064714',
'江苏国际' => '626064674',
'江苏教育' => '628008321',
'江苏影视频道' => '626064697',
'江苏综艺频道' => '626065193',
'江苏公共新闻' => '626064693',
'盐城新闻综合' => '639731825',
'淮安新闻综合' => '639731826',
'泰州新闻综合' => '639731818',
'连云港新闻综合' => '639731715',
'宿迁新闻综合' => '639731832',
'徐州新闻综合' => '639731747',
'优漫卡通频道' => '626064703',
'江阴新闻综合' => '955227979',
'南通新闻综合' => '955227985',
'宜兴新闻综合' => '955227996',
'溧水新闻综合' => '639737327',
'陕西银龄频道' => '956909362',
'陕西都市青春频道' => '956909358',
'陕西体育休闲频道' => '956909356',
'陕西秦腔频道' => '956909303',
'陕西新闻资讯频道' => '956909289',
'江苏财富天下' => '956923159',
'MIGU红色轮播' => '713600957',
'MIGU高清大片' => '629943678',
'MIGU经典港片' => '625703337',
'MIGU高能悬疑' => '625133682',
'MIGU抗战经典' => '617432318',
'MIGU新片放映' => '619495952',
'CHC影迷电影' => '952383261',
'CHC动作电影' => '644368714',
'CHC家庭影院' => '644368373',
'和美乡途轮播台' => '713591450',
'南方影视' => '614961829',
'五环传奇' => '707671890',
'掼蛋精英赛' => '631354620',
'四海钓鱼' => '637444975',
'咪咕24小时体育台' => '654102378',
'CETV1' => '923287154',
'CETV2' => '923287211',
'CETV4' => '923287339',
'熊猫频道0' => '609158151',
'熊猫频道1' => '608933610',
'熊猫频道2' => '608933640',
'熊猫频道3' => '608934619',
'熊猫频道4' => '608934721',
'熊猫频道5' => '608935104',
'熊猫频道6' => '608935797',
'熊猫频道7' => '609169286',
'熊猫频道8' => '609169287',
'熊猫频道9' => '609169226',
'熊猫频道10' => '609169285',
'嘉佳卡通' => '614952364',
'新动力量创一流' => '713589837',
'钱塘江' => '647370520',
];
// 缓存设置
$cacheDir = __DIR__ . '/epg_cache/';
if (!file_exists($cacheDir)){
    mkdir($cacheDir, 0755, true);
}
$cacheFile = $cacheDir . 'epg_migu.xml';
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
$tomorrow = date('Ymd', strtotime('+1 day'));
foreach ($mgChannels as $channelName => $channelId){
    echo $channelName;
    echo '<br>';
    foreach ([$today] as $date) {
        // 想加明天就把 $tomorrow 也写进来
        // 1. 干净接口
        $url = "https://program-sc.miguvideo.com/live/v2/tv-programs-data/{$channelId}/{$date}";
        // 2. 取回 JSONP
        $jsonp = httpGet($url, 'https://www.miguvideo.com/');
        if (!$jsonp) {
            continue;
        }
        // 3. 去头去尾变纯 JSON
        $json = preg_replace('/^callback $|$;?$/', '', $jsonp);
        // 4. 解析
        $data = json_decode($json, true);
        if (!$data || !isset($data['body']['program'][0]['content'])){
            continue;
        }
        // 5. 写 XML
        foreach ($data['body']['program'][0]['content'] as $p){
            $epgContent .= generateProgramXml(
            $channelName,
            $p['startTime'] / 1000,
            $p['endTime'] / 1000,
            $p['contName']
            );
        }
    }
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
?>
