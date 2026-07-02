from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 启动浏览器（必须看得到界面，方便你扫码）
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # 打开酷狗首页
    page.goto("https://www.kugou.com/")
    
    # 暂停在这里，此时你在弹出的浏览器里手动扫码登录
    print("请在弹出的浏览器中完成扫码登录...")
    
    # 给自己预留 30 秒时间扫码，或者利用 input 阻塞
    input("登录成功后，在终端按回车键继续...")
    
    # 登录成功后，把包含登录信息的 cookie 保存到本地文件
    context.storage_state(path="auth.json")
    browser.close()