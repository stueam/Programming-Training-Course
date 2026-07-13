import json
import re
import random
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

cookie = "kg_mid=3b80a23d6930bb39af7574da9a85b430; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1783586663; HMACCOUNT=8D6AA79DE30F3F9A; ACK_SERVER_10017=%7B%22list%22%3A%5B%5B%22gzverifycode.service.kugou.com%22%5D%5D%7D; ACK_SERVER_10015=%7B%22list%22%3A%5B%5B%22gzlogin-user.kugou.com%22%5D%5D%7D; ACK_SERVER_10016=%7B%22list%22%3A%5B%5B%22gzreg-user.kugou.com%22%5D%5D%7D; kg_dfid=11VkLe3bTCuw1xCNN91YSWVM; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; kg_mid_temp=3b80a23d6930bb39af7574da9a85b430; KuGoo=KugooID=1387168600&KugooPwd=A5719C19EFF676333415E54FF5A398BB&NickName=%u5c0f%u94a7%u94a7&Pic=http://imge.kugou.com/kugouicon/165/20230522/20230522080125206988.jpg&RegState=1&RegFrom=&t=dfcd129eb7746967f64dbdbea2ad3c6426f205075c15541f49f069446ef1d788&a_id=1014&ct=1783586686&UserName=%u0031%u0033%u0038%u0037%u0031%u0036%u0038%u0036%u0030%u0030&t1=; KugooID=1387168600; t=dfcd129eb7746967f64dbdbea2ad3c6426f205075c15541f49f069446ef1d788; a_id=1014; UserName=1387168600; mid=3b80a23d6930bb39af7574da9a85b430; dfid=11VkLe3bTCuw1xCNN91YSWVM; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1783586689"
headers = {
    "Referer": "https://www.kugou.com/yy/album/index/1-1-1.html",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
}


break_up_location = 1550
total = 0
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

    with open("song2.json", "r", encoding="utf-8") as f:
        for line in f:
            total += 1
            if total <= break_up_location:
                continue
            albumid = json.loads(line.strip()).get("albumid")
            if not albumid:
                continue
            url = f"https://www.kugou.com/album/info/{albumid}"
            page.goto(url, timeout=7000)
            # page.wait_for_timeout(500)
            html_content = page.content()
            bs = BeautifulSoup(html_content, "html.parser")
            
            info = bs.find("div", class_="l")
            if info is not None:
                info = info.find("p", class_="detail").text
                mat = re.search(r'\d{4}-\d{2}-\d{2}', info).group()
                
                with open("release_time.json", "a", encoding="utf-8") as out_f:
                    out_f.write(json.dumps(mat, ensure_ascii=False) + '\n')
            time.sleep(random.uniform(0.5,1.2))
            
            
    context.close()
    browser.close()