# 酷猫音乐 Web 应用实现讲解

## 一、项目概述

基于 Django 框架的在线音乐浏览平台，数据来源于酷狗音乐。功能包括歌曲/歌手浏览、搜索、歌词展示、评论系统。

---

## 二、技术栈

| 层 | 技术 |
|---|---|
| 后端框架 | Django 6.0 |
| 数据库 | SQLite3 |
| 前端样式 | Bootstrap 5.3 |
| 图标库 | Bootstrap Icons 1.11 |
| 数据来源 | 爬虫抓取酷狗音乐 |

---

## 三、项目结构

```
mypro/
├── manage.py                  # Django 命令行入口
├── db.sqlite3                 # SQLite 数据库
├── mypro/                     # 项目配置
│   ├── settings.py            # 全局设置
│   └── urls.py                # 根路由
└── musicapp/                  # 主应用
    ├── models.py              # 数据模型
    ├── views.py               # 视图逻辑
    ├── urls.py                # 应用路由
    └── templates/             # HTML 模板
        ├── base.html          # 母版（布局骨架）
        ├── song_list.html     # 歌曲列表页
        ├── song_detail.html   # 歌曲详情页
        ├── singer_list.html   # 歌手列表页
        ├── singer_detail.html # 歌手详情页
        ├── search_results.html# 搜索结果页
        └── pagination.html   # 分页组件
```

---

## 四、数据模型 models.py —— 三层表结构

```python
class Singer(models.Model):   # 歌手表
    name    # 歌手名
    intro   # 简介
    url     # 酷狗主页
    image   # 头像 URL

class Song(models.Model):     # 歌曲表
    name    # 歌名
    singer  # 外键 → Singer
    url     # 源链接
    image   # 封面 URL
    lyrics  # 歌词文本

class Comment(models.Model):   # 评论表
    song         # 外键 → Song
    content      # 评论内容
    release_time # 发布时间（自动生成）
```

**relation 关系**：Singer 一对多 Song（`related_name='song'`），Song 一对多 Comment（`related_name='comment'`）。使用 **SQLite** 存储，轻量零配置。

---

## 五、路由设计 urls.py —— URL 到视图的映射

```python
path('',                   song_list,      name='song_list')      # 首页=歌曲列表
path('songs/',             song_list,      name='song_list')
path('songs/<int:song_id>/', song_detail,  name='song_detail')    # /songs/123/
path('singers/',           singer_list,    name='singer_list')
path('singers/<int:singer_id>/', singer_detail, name='singer_detail')
path('search/',            search,         name='search')
path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment')
```

**路由参数**：`<int:song_id>` 从 URL 中提取整数 ID，传入视图函数。

**根路由** `mypro/urls.py` 用 `include('musicapp.urls')` 把所有路径代理给应用路由。

---

## 六、模板系统 —— Django Template Language (DTL)

### 6.1 模板继承 —— base.html 母版

```django
<!-- base.html: 定义整体 HTML 框架 -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <!-- 1. CDN 引入 Bootstrap CSS -->
    <link href="bootstrap@5.3.0/css/bootstrap.min.css">
    <!-- 2. CDN 引入 Bootstrap Icons（免费图标库） -->
    <link href="bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <!-- 3. <style> 块：自定义 CSS -->
    <style> ... </style>
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark"> ... </nav>

    <!-- 内容占位：子模板填充 -->
    <main class="container">
        {% block content %}{% endblock %}
    </main>

    <!-- 页脚 -->
    <footer> ... </footer>

    <!-- Bootstrap JS（轮播/折叠等交互组件依赖） -->
    <script src="bootstrap@5.3.0/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

**继承机制**：子模板用 `{% extends 'base.html' %}` 继承母版，只需写 `{% block content %}...{% endblock %}`，复用导航栏、页脚、样式。

---

### 6.2 页面模板结构一览

| 模板文件 | 继承自 | 核心内容 |
|---|---|---|
| `song_list.html` | base.html | `{% for song in songs %}` 循环渲染卡片 |
| `song_detail.html` | base.html | 歌曲信息 + 歌词展示 + 评论列表 |
| `singer_list.html` | base.html | 歌手卡片网格 |
| `singer_detail.html` | base.html | 歌手详情 + 歌曲列表 |
| `search_results.html` | base.html | 按类型（歌曲/歌手）切换结果 |
| `pagination.html` | 被 include | 分页导航组件（被其他模板 `{% include %}` 复用） |

---

### 6.3 DTL 关键语法演示

```django
{# 1. 输出变量 #}
{{ song.name }}
{{ song.singer.name }}    {# 跨外键访问 #}

{# 2. 条件判断 #}
{% if song.image %}
    <img src="{{ song.image }}">
{% else %}
    <div>默认占位图</div>
{% endif %}

{% if lyrics %}
    <pre>{{ lyrics }}</pre>
{% else %}
    <p>暂无歌词</p>
{% endif %}

{# 3. 循环遍历 #}
{% for song in songs %}
    <div>{{ song.name }} - {{ song.singer.name }}</div>
{% empty %}  {# 列表为空时的兜底 #}
    <p>暂无歌曲</p>
{% endfor %}

{# 4. URL 反向解析 #}
<a href="{% url 'song_detail' song.id %}">查看详情</a>
{# Django 自动生成 /songs/123/ #}

{# 5. 跨站请求保护 #}
{% csrf_token %}

{# 6. 过滤器 #}
{{ singer.intro|truncatechars:40 }}
```

---

## 七、视图函数 views.py —— 数据处理与页面渲染

### 7.1 核心流程（以 song_detail 为例）

```
用户访问 /songs/123/
    ↓
URL 路由匹配 → views.song_detail(request, song_id=123)
    ↓
从数据库查询：Song.objects.select_related('singer').get(id=123)
                  ↑ 预加载外键，避免 N+1 查询
    ↓
调用 clean_lyrics() 清洗歌词（去元数据、去时间戳）
    ↓
render(request, 'song_detail.html', context)
    把 {'song': 歌曲对象, 'comments': 评论列表, 'lyrics': 清洗后歌词}
    传入模板渲染，返回 HTML 给浏览器
```

### 7.2 各视图函数

| 视图 | ORM 查询 | 返回 context |
|---|---|---|
| `song_list` | `Song.objects.select_related('singer').all().order_by('?')` 随机排序 + 分页 | `songs`分页对象 |
| `song_detail` | `get_object_or_404(Song..., id=song_id)` | `song`, `comments`, `lyrics` |
| `singer_list` | `Singer.objects.all().order_by('id')` + 分页 | `singers`分页对象 |
| `singer_detail` | `get_object_or_404(Singer, id=singer_id)` | `singer`, `songs` |
| `search` | `Song.objects.filter(Q(name__icontains=q) \| Q(singer__name__icontains=q) \| Q(lyrics__icontains=q))` | `results`, `query`, `search_type`, `elapsed` |

### 7.3 clean_lyrics() 函数 —— 歌词清洗逻辑

原始歌词是 LRC 格式，示例如下：
```
[id:$00000000]                  ← 元数据，过滤
[ar:周杰伦]                     ← 元数据，过滤
[ti:晴天]                       ← 元数据，过滤
[by:天琴实验室]                 ← 元数据，过滤
[00:00.00]作词：方文山          ← 作词行，过滤
[00:00.06]作曲：周杰伦          ← 作曲行，过滤
[00:16.00]故事的小黄花          ← 歌词正文，保留
[00:20.00]从出生那年就飘着      ← 歌词正文，保留
【未经著作权人许可不得翻唱】    ← 版权声明，过滤
```

清洗步骤：
1. `lstrip('\ufeff')` —— 移除 UTF-8 BOM 头
2. 按 `\n` 拆分为行
3. 正则 `^\[\d{2}:\d{2}\.\d{2,3}\]` 剥离 LRC 时间戳
4. 过滤：作词/作曲/编曲等元数据行、版权声明行、纯分隔符行
5. 输出不带时间戳的纯歌词文本

---

## 八、前端实现详解

### 8.1 Bootstrap 5 的用法

Bootstrap 是一个 CSS 框架，通过给 HTML 标签添加预定义的 **class** 来控制样式，无需手写 CSS。

#### 栅格系统（Grid Layout）

```html
<!-- 一行 12 列，col-lg-5 和 col-lg-7 在大屏上 5:7 分 -->
<div class="row g-4">              <!-- g-4 = 间距 -->
    <div class="col-lg-5">...</div>  <!-- 左侧 5/12 -->
    <div class="col-lg-7">...</div>  <!-- 右侧 7/12 -->
</div>

<!-- 响应式断点：col-md-6 col-lg-4 -->
<!-- 中等屏幕 6/12（一行2个），大屏幕 4/12（一行3个） -->
<div class="col-md-6 col-lg-4 mb-3">...</div>
```

#### 常用 Bootstrap 类

| class | 作用 |
|---|---|
| `container` | 固定宽度容器，自动居中 |
| `row` | 行容器，内部放 col |
| `card` / `card-body` / `card-header` | 卡片组件（白色背景、圆角、阴影） |
| `shadow-sm` | 轻微阴影 |
| `navbar navbar-expand-lg navbar-dark bg-dark` | 深色导航栏，大屏展开 |
| `btn btn-outline-primary btn-sm rounded-pill` | 按钮：轮廓样式、主色调、小号、药丸圆角 |
| `breadcrumb` | 面包屑导航 |
| `form-control` / `form-select` | 表单输入框/下拉框样式 |
| `text-truncate` | 文字溢出显示省略号 |
| `rounded-circle` | 正圆形（用于头像） |
| `d-flex` / `align-items-center` / `justify-content-center` | Flexbox 布局 |
| `text-muted` | 灰色文字 |
| `fw-semibold` / `fw-bold` | 字体粗细 |
| `mb-3` / `me-2` / `mt-auto` | margin 间距（1rem=16px，3=1rem, 2=0.5rem） |
| `bg-opacity-10` / `bg-secondary` | 背景色 + 透明度 |
| `order-lg-1` / `order-lg-2` | 响应式排序（移动端不同排列） |

### 8.2 自定义 CSS（base.html 的 `<style>` 块）

Bootstrap 处理通用样式，自定义 CSS 处理品牌特色的个性化需求：

| 自定义样式 | 说明 |
|---|---|
| `:root { --primary: #6c5ce7; }` | CSS 变量定义主题色（紫色系） |
| `.card:hover` | 卡片悬停时的阴影动效 |
| `.lyrics-scroll` | 歌词区域：最大高度 65vh，超出滚动 |
| `.lyrics-scroll pre` | 歌词文字：保留换行、2 倍行高 |
| `.lyrics-scroll::-webkit-scrollbar` | 自定义滚动条样式（紫色主题） |
| `.comment-avatar` | 评论序号圆圈（圆形紫色背景白色数字） |
| `.singer-card:hover` | 歌手卡片悬停上浮动效 |
| `.badge-gradient` | 渐变色徽章（紫→粉） |
| `.song-info-bar .card-body` | 歌曲信息栏渐变背景 |

### 8.3 Bootstrap Icons

通过 `<i class="bi bi-xxx"></i>` 使用 2000+ 免费图标：
- `bi bi-music-note-beamed` —— 音符（Logo）
- `bi bi-person` —— 人物
- `bi bi-search` —— 搜索
- `bi bi-file-text` —— 歌词
- `bi bi-chat-dots` —— 评论
- `bi bi-disc` —— 唱片（默认封面占位）
- `bi bi-emoji-frown` —— 空状态提示

---

## 九、JSON 数据流

### 9.1 数据采集（crawl.py）

```
酷狗音乐网站 → Playwright 浏览器自动化 → 抓取 API 响应 → JSON 文件
```

爬虫流程：
1. 读取 `singer_pre.json` 中的歌手列表（URL + 姓名）
2. Playwright 打开歌手页面，解析歌曲列表
3. 拦截 `play/songinfo` API 请求，获取歌词 JSON 端点
4. `requests.get()` 拉取歌词 API 返回的 JSON：
   ```json
   {
     "data": {
       "img": "封面图片URL",
       "lyrics": "[id:$00000000]\n[ar:周杰伦]\n[00:16.00]故事的小黄花\n..."
     }
   }
   ```
5. 逐行写入 `song.json`（JSONL 格式，每行一个对象）：
   ```json
   {"songname": "晴天", "singername": "周杰伦", "url": "https://...", "photo": "https://...", "lyric": "歌词原文"}
   ```

### 9.2 数据导入（import_data.py 管理命令）

```
python manage.py import_data
```

逐行读取 `singer.json` 和 `song.json`，通过 ORM 写入 SQLite：
1. `Singer.objects.get_or_create(...)` —— 先去重再创建歌手
2. `Song.objects.get_or_create(...)` —— JSON 键 `lyric` 映射到模型字段 `lyrics`

---

## 十、一次完整请求的端到端流程

```
浏览器请求 GET /songs/123/
  │
  ▼
Django URL 路由 → views.song_detail(request, song_id=123)
  │
  ▼
SQL: SELECT * FROM song JOIN singer WHERE song.id=123
  │
  ▼
clean_lyrics() 清洗歌词（去时间戳、去元数据、去版权声明）
  │
  ▼
SQL: SELECT * FROM comment WHERE song_id=123 ORDER BY release_time DESC
  │
  ▼
render('song_detail.html', {'song': song对象, 'comments': 评论列表, 'lyrics': 清洗后歌词})
  │
  ▼
DTL 模板引擎渲染：
  base.html  ← 母版框架（导航栏+页脚+Bootstrap CSS/JS）
       ↓
  song_detail.html ← 填充 content 块
       ├── {{ song.name }} → 歌名
       ├── {{ song.singer.name }} → 歌手名
       ├── {% if lyrics %}<pre>{{ lyrics }}</pre> → 歌词
       ├── {% for comment in comments %} → 评论列表
       └── {% csrf_token %} → 评论表单
  │
  ▼
返回完整 HTML 给浏览器
```

---

## 十一、关键技术点总结

| 知识点 | 在项目中的体现 |
|---|---|
| **MVC/MTV 模式** | Model(数据) → Template(展示) → View(逻辑) |
| **ORM 查询** | `select_related` 预加载外键、`Q` 对象组合查询、`icontains` 模糊匹配 |
| **模板继承** | `base.html` 定义骨架，子模板 `{% extends %}` 复用 |
| **{% block %}** | 占位机制，父模板定义块，子模板填充 |
| **{% include %}** | pagination.html 被多个页面复用 |
| **CSRF 保护** | 所有 POST 表单用 `{% csrf_token %}` |
| **Bootstrap 栅格** | `row > col-md-6 col-lg-4` 响应式布局 |
| **Bootstrap 工具类** | 阴影、间距、圆角、颜色全部用 class 控制 |
| **正则表达式** | `clean_lyrics()` 中用 re 清洗 LRC 歌词 |
| **JSON 数据处理** | `json.loads()` 解析 JSONL，存入数据库 |
| **管理命令** | `python manage.py import_data` 自定义数据导入 |
