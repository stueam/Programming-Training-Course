import requests
from bs4 import BeautifulSoup
import time
import json
import re
from playwright.sync_api import sync_playwright

cookie = "kg_mid=c1e5ca98fbedcf5384d79032e4861c22; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1782911024; HMACCOUNT=BF6CB5A8FA424ABA; kg_dfid=1u0ffP2gudL03McrJP4eHFFM; ACK_SERVER_10015=%7B%22list%22%3A%5B%5B%22gzlogin-user.kugou.com%22%5D%5D%7D; kg_mid_temp=c1e5ca98fbedcf5384d79032e4861c22; ACK_SERVER_10016=%7B%22list%22%3A%5B%5B%22gzreg-user.kugou.com%22%5D%5D%7D; ACK_SERVER_10017=%7B%22list%22%3A%5B%5B%22gzverifycode.service.kugou.com%22%5D%5D%7D; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; KuGoo=KugooID=1387168600&KugooPwd=A5719C19EFF676333415E54FF5A398BB&NickName=%u5c0f%u94a7%u94a7&Pic=http://imge.kugou.com/kugouicon/165/20230522/20230522080125206988.jpg&RegState=1&RegFrom=&t=dfcd129eb7746967f64dbdbea2ad3c647db5602693fa1f3c985226b07ed1da11&a_id=1014&ct=1782997653&UserName=%u0031%u0033%u0038%u0037%u0031%u0036%u0038%u0036%u0030%u0030&t1=; KugooID=1387168600; t=dfcd129eb7746967f64dbdbea2ad3c647db5602693fa1f3c985226b07ed1da11; a_id=1014; UserName=1387168600; mid=c1e5ca98fbedcf5384d79032e4861c22; dfid=1u0ffP2gudL03McrJP4eHFFM; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1782997662"

headers = {
    "Referer": "https://kugou.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Cookie": cookie,
}

total_singer = 0
total_song = 0
artists = []

for i in range(1, 27):
    for j in range(1, 6):
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
                    artists.append([artist_url, artist_name])
                    total_singer += 1
                if total_singer > 2:
                    break
        
        if total_singer > 2:
            break
    if total_singer > 2: 
        break

singers_descip = []
songs_descrip = []

lyrics_url = []

current_lyrics = None

def handle_response(response):
    global current_lyrics
    url = response.url
    
    if "play/songinfo" in url:
        # 确保返回的是 json 或文本
        lyrics_url.append(url)
        current_lyrics = url
        print(url)
        print("successfully get json")
        


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context() 
    page = context.new_page()

    page.on("response", handle_response)

    for singer_url, singer_name in artists:
        res = requests.get(singer_url, headers=headers)
        bs = BeautifulSoup(res.text, "html")

        singer_photo = bs.find("div", class_="top").find("img").get("src")
        singer_intro = bs.find("div", class_="intro").find("p").text
        
        singers_descip.append([singer_name,singer_intro,singer_url,singer_photo])

        songs_list = bs.find("div", class_="sng_song").find("ul", id="song_container").find_all("li")

        for song in songs_list:
            song_url = song.find("a").get("href")
            song_name = song.find("a").find("span",class_="text").text
            song_photo = None
            
            page.goto(song_url, timeout=5000)
            page.wait_for_timeout(500) 

            if current_lyrics != None:
                print("success")
                total_song = total_song + 1
                songs_descrip.append([song_name,singer_name,song_url,song_photo])
            
            current_lyrics = None
            if total_song > 3:
                break

            
        if total_song > 3:
            break

    browser.close()

# already got URL of all lyrics

for i, lyric_url in enumerate(lyrics_url):
    res = requests.get(lyric_url, headers=headers)
    lyric = res.json().get("data").get("lyrics")
    print(type(lyric))
    clean_lyric = re.sub(r"\[[^\]]*\]","",lyric).lstrip()
    songs_descrip[i].append(clean_lyric)

# already got songs_descrip & singers_descrip

with open("song.json", "w", encoding="utf-8") as f:
    json.dump(songs_descrip, f, ensure_ascii=False, indent=2)

with open("singer.json", "w", encoding="utf-8") as f:
    json.dump(singers_descip, f, ensure_ascii=False, indent=2)

