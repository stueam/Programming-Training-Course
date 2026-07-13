import requests
from bs4 import BeautifulSoup
import json
import time
import random
import matplotlib.pyplot as plt
import networkx as nx

cookie = "kg_mid=8223a5384372188f76e00417b192d096; Hm_lvt_aedee6983d4cfc62f509129360d6bb3d=1783423866; HMACCOUNT=8D6AA79DE30F3F9A; ACK_SERVER_10015=%7B%22list%22%3A%5B%5B%22gzlogin-user.kugou.com%22%5D%5D%7D; kg_dfid=3f0h9B3eWOUk00qSRT2Xi8J5; kg_dfid_collect=d41d8cd98f00b204e9800998ecf8427e; KuGoo=KugooID=1387168600&KugooPwd=A5719C19EFF676333415E54FF5A398BB&NickName=%u5c0f%u94a7%u94a7&Pic=http://imge.kugou.com/kugouicon/165/20230522/20230522080125206988.jpg&RegState=1&RegFrom=&t=dfcd129eb7746967f64dbdbea2ad3c64a5d78c525bd92232fd147f6f1ef4b69e&a_id=1014&ct=1783423886&UserName=%u0031%u0033%u0038%u0037%u0031%u0036%u0038%u0036%u0030%u0030&t1=; KugooID=1387168600; t=dfcd129eb7746967f64dbdbea2ad3c64a5d78c525bd92232fd147f6f1ef4b69e; a_id=1014; UserName=1387168600; mid=8223a5384372188f76e00417b192d096; dfid=3f0h9B3eWOUk00qSRT2Xi8J5; kg_mid_temp=8223a5384372188f76e00417b192d096; ACK_SERVER_10016=%7B%22list%22%3A%5B%5B%22gzreg-user.kugou.com%22%5D%5D%7D; ACK_SERVER_10017=%7B%22list%22%3A%5B%5B%22gzverifycode.service.kugou.com%22%5D%5D%7D; Hm_lpvt_aedee6983d4cfc62f509129360d6bb3d=1783425394"
headers = {
    "Referer": "https://kugou.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "Cookie": cookie,
}

coresinger = "Imagine Dragons"
oriurl = "https://www.kugou.com/singer/info/290FKAE36C92F/"

queue = [""] * 100
head = 0
tail = 0

queue[tail] = oriurl
s = set()

total = 0

nodes = []
edges = []

nodes.append(coresinger)
s.add(coresinger)

while total <= 20 and head <= tail:
    url = queue[head]
    head += 1

    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        bs = BeautifulSoup(res.text, "html.parser")
        
        current_name = bs.find("div", class_="intro").find("div", class_="clear_fix").find("strong").get("title")
        other_singer = bs.find("div", class_="other_singer")
        if not other_singer:
            print("error")
            print(url)
            break

        singer1 = other_singer.find("li", class_="f").find("strong").find("a").get("href")
        singer2 = other_singer.find("li", class_="s").find("strong").find("a").get("href")
        singer1_name = other_singer.find("li", class_="f").find("a").get("title")
        singer2_name = other_singer.find("li", class_="s").find("a").get("title")
        
        if singer1_name not in s:
            nodes.append(singer1_name)
        s.add(singer1)
        total += 1
        tail += 1
        queue[tail] = singer1
        edges.append((current_name, singer1_name))
    
        if singer2_name not in s:
            nodes.append(singer2_name)
        s.add(singer2)
        total += 1
        tail += 1
        queue[tail] = singer2
        edges.append((current_name, singer2_name))
        
        time.sleep(random.uniform(0.5, 1))


plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签（黑体）
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号
G = nx.DiGraph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)
pos = nx.spectral_layout(G)
plt.figure(figsize=(6, 6))
nx.draw(
    G,
    pos,
    with_labels=True,  # 显示节点标签
    node_color="skyblue",  # 节点颜色
    node_size=1000,  # 节点大小
    edge_color="gray",  # 连边颜色
    width=2,  # 连边粗细
    font_size=12,  # 字体大小
    font_weight="bold",  # 字体粗细
)
plt.show()