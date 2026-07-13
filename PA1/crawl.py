import requests
from bs4 import BeautifulSoup
import time
import random
import json
import re
from playwright.sync_api import sync_playwright

cookie = "kg_mid=8223a5384372188f76e00417b192d096; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1783423866; HMACCOUNT=8D6AA79DE30F3F9A; ACK_SERVER_10015=%7B%22list%22%3A%5B%5B%22gzlogin-user.kugou.com%22%5D%5D%7D; kg_dfid=3f0h9B3eWOUk00qSRT2Xi8J5; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; KuGoo=KugooID=1387168600&KugooPwd=A5719C19EFF676333415E54FF5A398BB&NickName=%u5c0f%u94a7%u94a7&Pic=http://imge.kugou.com/kugouicon/165/20230522/20230522080125206988.jpg&RegState=1&RegFrom=&t=dfcd129eb7746967f64dbdbea2ad3c64a5d78c525bd92232fd147f6f1ef4b69e&a_id=1014&ct=1783423886&UserName=%u0031%u0033%u0038%u0037%u0031%u0036%u0038%u0036%u0030%u0030&t1=; KugooID=1387168600; t=dfcd129eb7746967f64dbdbea2ad3c64a5d78c525bd92232fd147f6f1ef4b69e; a_id=1014; UserName=1387168600; mid=8223a5384372188f76e00417b192d096; dfid=3f0h9B3eWOUk00qSRT2Xi8J5; kg_mid_temp=8223a5384372188f76e00417b192d096; ACK_SERVER_10016=%7B%22list%22%3A%5B%5B%22gzreg-user.kugou.com%22%5D%5D%7D; ACK_SERVER_10017=%7B%22list%22%3A%5B%5B%22gzverifycode.service.kugou.com%22%5D%5D%7D; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1783425394"
headers = {
    "Referer": "https://kugou.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Cookie": cookie,
}

total_singer = 0
total_song = 0
artists = []

'''
for i in range(25, 27):
    for j in range(1, 2):
        letter = chr(ord('a') + i - 1)
        url = f"https://www.kugou.com/yy/singer/index/{j}-{letter}-1.html"
        res = requests.get(url, headers=headers)
        
        if res.status_code == 200:
            bs = BeautifulSoup(res.text, "html.parser")
            artist_list = bs.find_all("ul", class_="list1")
            for artist_with_tag in artist_list:
                a_tag = artist_with_tag.find("a")
                if a_tag:
                    artist_name = a_tag.text
                    artist_url = a_tag.get("href")

                    with open("singer_pre.json", "a", encoding="utf-8") as f:
                        f.write(json.dumps([artist_url, artist_name], ensure_ascii=False) + '\n')
                    
                    artists.append([artist_url, artist_name])
                    total_singer += 1
                    print(f"singer{artist_name}")
        
        if total_singer > 100:
            break
    if total_singer > 100: 
        break

print(f"Singer: {total_singer}")

'''
with open("singer_pre.json", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip() 
        artist_info = json.loads(line) 
        artists.append(artist_info)

break_up_location = 0
current_location = 0


current_lyrics = None

def handle_response(response):
    global current_lyrics
    url = response.url
    
    if "play/songinfo" in url:
        current_lyrics = url
        # print(url)
        # print("successfully get json")
        
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

    for singer_url, singer_name in artists:
        
        res = requests.get(singer_url, headers=headers)
        bs = BeautifulSoup(res.text, "html")

        singer_photo_url = bs.find("div", class_="top").find("img").get("_src")
        singer_intro = bs.find("div", class_="intro").find("p").text
        
        singer_item = {"name": singer_name,"intro": singer_intro,"url": singer_url,"photo": singer_photo_url}
        with open("singer.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(singer_item, ensure_ascii=False) + '\n')

        songs_list = bs.find("div", class_="sng_song").find("ul", id="song_container").find_all("li")

        tmp_amount = 0
        for song in songs_list:
            tmp_amount += 1
            if tmp_amount >= 20:
                break

            # break up 
            current_location += 1
            if current_location <= break_up_location:
                print(f"pass {total_song + 1}")
                total_song += 1
                continue

            song_url = song.find("a").get("href")
            song_name = song.find("a").find("span",class_="text").text
            
            page.goto(song_url, timeout=7000)
            page.wait_for_timeout(500) 
            

            if current_lyrics != None:
                print(f"song{total_song + 1}: success")
                total_song = total_song + 1

                song_item = {"songname": song_name,"singername": singer_name,"url": song_url,"photo": None}
                lyric_url = current_lyrics
                res = requests.get(lyric_url, headers=headers)
                photo_url = res.json().get("data").get("img")
                song_item["photo"] = photo_url

                lyric = res.json().get("data", {}).get("lyrics")
                
                song_item["lyric"] = lyric

                with open("song.json", "a", encoding="utf-8") as f:
                    f.write(json.dumps(song_item, ensure_ascii=False) + '\n')
                        
            current_lyrics = None
            time.sleep(random.uniform(0.4,0.8))

            if total_song > 2100:
                break
        if total_song > 2100:
            break

    browser.close()
