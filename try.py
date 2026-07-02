import requests
from bs4 import BeautifulSoup
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== 1. 配置中心 ====================
COOKIE = "kg_mid=c1e5ca98fbedcf5384d79032e4861c22; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1782911024; HMACCOUNT=BF6CB5A8FA424ABA; kg_dfid=1u0ffP2gudL03McrJP4eHFFM; ACK_SERVER_10015=%7B%22list%22%3A%5B%5B%22gzlogin-user.kugou.com%22%5D%5D%7D; kg_mid_temp=c1e5ca98fbedcf5384d79032e4861c22; ACK_SERVER_10016=%7B%22list%22%3A%5B%5B%22gzreg-user.kugou.com%22%5D%5D%7D; ACK_SERVER_10017=%7B%22list%22%3A%5B%5B%22gzverifycode.service.kugou.com%22%5D%5D%7D; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; KuGoo=KugooID=1387168600&KugooPwd=A5719C19EFF676333415E54FF5A398BB&NickName=%u5c0f%u94a7%u94a7&Pic=http://imge.kugou.com/kugouicon/165/20230522/20230522080125206988.jpg&RegState=1&RegFrom=&t=dfcd129eb7746967f64dbdbea2ad3c647db5602693fa1f3c985226b07ed1da11&a_id=1014&ct=1782997653&UserName=%u0031%u0033%u0038%u0037%u0031%u0036%u0038%u0036%u0030%u0030&t1=; KugooID=1387168600; t=dfcd129eb7746967f64dbdbea2ad3c647db5602693fa1f3c985226b07ed1da11; a_id=1014; UserName=1387168600; mid=c1e5ca98fbedcf5384d79032e4861c22; dfid=1u0ffP2gudL03McrJP4eHFFM; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1782997662"

HEADERS = {
    "Referer": "https://kugou.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Cookie": COOKIE,
}

# 核心：直接向后端 API 要数据。请根据你实际截获的抓包参数对以下内容进行微调！
BASE_API = "https://wwwapi.kugou.com/play/songinfo"
COMMON_PARAMS = {
    "srcappid": "2919",
    "clientver": "20000",
    "mid": "c1e5ca98fbedcf5384d79032e4861c22",
    "uuid": "c1e5ca98fbedcf5384d79032e4861c22",
    "dfid": "1u0ffP2gudL03McrJP4eHFFM",
    "appid": "1014",
    "platid": "4",
    "token": "dfcd129eb7746967f64dbdbea2ad3c647db5602693fa1f3c985226b07ed1da11",
    "userid": "1387168600",
    "signature": "0e7c4a203b6a23e5b4c798bcde04015e" # 酷狗的通用签名通常跟账号关联，可复用
}

# 并发线程数（可根据网络情况调整，建议 5-15 之间，太高容易被服务器拒绝）
MAX_WORKERS = 10 

# ==================== 2. 爬取数据逻辑 ====================

# 线程任务：独立请求某一首歌曲的 API 并返回结果
def download_songinfo(encode_id, song_name, singer_name, song_url):
    params = COMMON_PARAMS.copy()
    params["encode_album_audio_id"] = encode_id
    params["clienttime"] = str(int(time.time() * 1000))  # 动态生成当前毫秒级时间戳
    
    try:
        # 纯 API 请求，不加载网页资源，速度极快
        res = requests.get(BASE_API, params=params, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            json_data = res.json()
            # 校验接口返回状态（一般 1 或 200 代表成功，视具体接口而定）
            if json_data.get("status") == 1 or "data" in json_data:
                print(f"[成功] -> 《{song_name}》 歌词及歌曲信息提取完毕。")
                return {
                    "singer_name": singer_name,
                    "song_name": song_name,
                    "song_url": song_url,
                    "encode_id": encode_id,
                    "songinfo": json_data
                }
            else:
                print(f"[失败] -> 《{song_name}》 接口未返回有效数据，可能是签名失效。")
    except Exception as e:
        print(f"[错误] -> 请求歌曲 《{song_name}》 失败: {e}")
    return None


def main():
    artists = []
    total_artists = 0
    
    print("开始获取歌手列表...")
    # 第一步：获取歌手主页链接
    for i in range(1, 27):
        for j in range(1, 6):
            letter = chr(ord('a') + i - 1)
            url = f"https://www.kugou.com/yy/singer/index/{j}-{letter}-1.html"
            try:
                res = requests.get(url, headers=HEADERS, timeout=5)
                if res.status_code == 200:
                    bs = BeautifulSoup(res.text, "html.parser")
                    artist_list = bs.find_all("ul", class_="list1")
                    for artist_with_tag in artist_list:
                        a_tag = artist_with_tag.find("a")
                        if a_tag:
                            artists.append([a_tag.get("href"), a_tag.text])
                            total_artists += 1
            except Exception:
                pass
            if total_artists > 3: break # 控制测试歌手数量，可根据需要加大
        if total_artists > 3: break

    print(f"成功收集到 {len(artists)} 位歌手。开始提取歌曲特征...")

    # 第二步：解析所有歌手页面，提取出每首歌的 encode_id
    tasks = []  # 存放所有需要并发的歌曲任务数据
    
    for singer_url, singer_name in artists:
        try:
            res = requests.get(singer_url, headers=HEADERS, timeout=5)
            if res.status_code != 200: continue
            
            bs = BeautifulSoup(res.text, "html.parser")
            song_container = bs.find("div", class_="sng_song")
            songs_list = song_container.find("ul", id="song_container").find_all("li") if song_container else []
            
            for song in songs_list:
                a_tag = song.find("a")
                if a_tag:
                    song_url = a_tag.get("href")
                    span_tag = a_tag.find("span", class_="text")
                    song_name = span_tag.text if span_tag else "Unknown"
                    
                    # 使用正则从 url (如 .../mixsong/cbaxde5d.html) 中直接切出加密ID
                    match = re.search(r"mixsong/([\w]+)\.html", song_url)
                    if match:
                        encode_id = match.group(1)
                        # 将任务所需参数打包
                        tasks.append((encode_id, song_name, singer_name, song_url))
        except Exception as e:
            print(f"解析歌手 {singer_name} 页面失败: {e}")

    total_songs = len(tasks)
    print(f"特征提取完毕！共计发现 {total_songs} 首歌曲。")
    print(f"正在启动多线程加速引擎（并发数: {MAX_WORKERS}），预计几分钟内完成...")

    # 第三步：利用线程池多线程并发请求 API
    songs_descrip = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有提取出来的歌曲任务
        future_to_song = {
            executor.submit(download_songinfo, eid, sname, artist, surl): sname 
            for eid, sname, artist, surl in tasks
        }
        
        # 随着线程任务逐个完成，实时收集结果
        for future in as_completed(future_to_song):
            result = future.result()
            if result:
                songs_descrip.append(result)

    # 第四步：保存全量数据到本地
    print(f"\n全部下载结束！成功抓取并封存 {len(songs_descrip)}/{total_songs} 首歌曲的 songinfo。")
    with open("kugou_ultra_fast_results.json", "w", encoding="utf-8") as f:
        json.dump(songs_descrip, f, ensure_ascii=False, indent=4)
    print("数据已成功写入：kugou_ultra_fast_results.json")

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"总耗时: {time.time() - start_time:.2f} 秒。")