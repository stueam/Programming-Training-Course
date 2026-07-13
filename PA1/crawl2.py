# crawl the release time and the duration of each song

import requests
from bs4 import BeautifulSoup
import json
from playwright.sync_api import sync_playwright
import time

cookie = "kg_mid=8223a5384372188f76e00417b192d096; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1783423866; HMACCOUNT=8D6AA79DE30F3F9A; ACK_SERVER_10015=%7B%22list%22%3A%5B%5B%22gzlogin-user.kugou.com%22%5D%5D%7D; kg_dfid=3f0h9B3eWOUk00qSRT2Xi8J5; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; KuGoo=KugooID=1387168600&KugooPwd=A5719C19EFF676333415E54FF5A398BB&NickName=%u5c0f%u94a7%u94a7&Pic=http://imge.kugou.com/kugouicon/165/20230522/20230522080125206988.jpg&RegState=1&RegFrom=&t=dfcd129eb7746967f64dbdbea2ad3c64a5d78c525bd92232fd147f6f1ef4b69e&a_id=1014&ct=1783423886&UserName=%u0031%u0033%u0038%u0037%u0031%u0036%u0038%u0036%u0030%u0030&t1=; KugooID=1387168600; t=dfcd129eb7746967f64dbdbea2ad3c64a5d78c525bd92232fd147f6f1ef4b69e; a_id=1014; UserName=1387168600; mid=8223a5384372188f76e00417b192d096; dfid=3f0h9B3eWOUk00qSRT2Xi8J5; kg_mid_temp=8223a5384372188f76e00417b192d096; ACK_SERVER_10016=%7B%22list%22%3A%5B%5B%22gzreg-user.kugou.com%22%5D%5D%7D; ACK_SERVER_10017=%7B%22list%22%3A%5B%5B%22gzverifycode.service.kugou.com%22%5D%5D%7D; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1783425394"
headers = {
    "Referer": "https://kugou.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Cookie": cookie,
}


current_lyrics = None

def handle_response(response):
    global current_lyrics
    url = response.url
    
    if "play/songinfo" in url:
        current_lyrics = url
        
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context() 
    
    playwright_cookies = []
    for item in cookie.split(';'):
        if '=' in item:
            name, value = item.strip().split('=', 1) 
            
            playwright_cookies.append({
                'name': name,
                'value': value,
                'domain': '.kugou.com',
                'path': '/'
            })

    context.add_cookies(playwright_cookies)
    
    page = context.new_page()

    page.on("response", handle_response)

    total = 0
    break_up_location = 1950
    with open("song2.json", "a", encoding="utf-8") as out_f:
        with open("song.json", "r", encoding="utf-8") as f:
            for line in f:

                total += 1
                if break_up_location >= total:
                    continue


                line = line.strip()
                song = json.loads(line)
                song_url = song['url']

                page.goto(song_url, timeout=7000)
                time.sleep(0.2)
                if current_lyrics:
                    res = requests.get(current_lyrics, headers=headers)
                    resjson = res.json()
                    
                    timelength = resjson.get("data").get("timelength")
                    albumid = resjson.get("data").get("encode_album_id")
                    name = resjson.get("data").get("song_name").strip()
                    
                    if timelength and albumid:
                        print(f"{total}success")
                    else:
                        print(timelength,albumid)
                        
                    
                    out_f.write(json.dumps({"name": name, "timelength": timelength, "albumid": albumid}, ensure_ascii=False) + '\n')
                current_lyrics = None
                
