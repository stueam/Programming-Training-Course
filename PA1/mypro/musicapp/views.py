import re
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField
from .models import Singer, Song, Comment
import time


def clean_lyrics(text):
    text = text.lstrip('\ufeff')
    lines = text.strip().split('\n')
    result = []
    meta_pattern = re.compile(
        r'^((作词|作曲|编曲|制作人|原唱|原词曲|音乐总监|制作总监|混音|母带|录音|和声|吉他|贝斯|键盘|鼓手|钢琴|管风琴|PGM|舞团|灯光|舞台|和声编写|录音制作者|定位制作人|执行音乐总监|音乐团队|官方指定音乐合作伙伴|中文填词|Rap词|改编歌曲|改编歌曲词曲版权代理|OP|SP|出品)|'
        r'.*[：:])\s*'
    )
    copyright_pattern = re.compile(r'[（(【]未经|版权所有|翻[唱录]|授权')
    lrc_timestamp = re.compile(r'^\[\d{2}:\d{2}\.\d{2,3}\]')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        clean = lrc_timestamp.sub('', stripped).strip()
        if not clean:
            continue
        if meta_pattern.match(clean):
            continue
        if copyright_pattern.search(clean):
            continue
        if re.match(r'^[\s\-—_=]+$', clean):
            continue
        if i < 3 and ' - ' in clean and len(clean) < 60:
            continue
        result.append(clean)
    return '\n'.join(result)


def get_page_range(page_obj, window=1, edge=2):
    num_pages = page_obj.paginator.num_pages
    current = page_obj.number

    if num_pages <= edge * 2 + window * 2 + 1:
        return list(range(1, num_pages + 1))

    pages = []
    for i in range(1, edge + 1):
        pages.append(i)

    if current > edge + window + 1:
        pages.append(0)

    start = max(current - window, edge + 1)
    end = min(current + window, num_pages - edge)
    for i in range(start, end + 1):
        pages.append(i)

    if current < num_pages - edge - window:
        pages.append(0)

    for i in range(num_pages - edge + 1, num_pages + 1):
        if i > pages[-1]:
            pages.append(i)

    return pages


def build_pagination_context(page_obj, request):
    params = request.GET.copy()
    params.pop('page', None)
    extra_params = '&' + params.urlencode() if params else ''
    hidden_inputs = ''.join(
        f'<input type="hidden" name="{k}" value="{v}">'
        for k, v in params.items()
    )
    return {
        'page_range': get_page_range(page_obj),
        'extra_params': extra_params,
        'hidden_inputs': hidden_inputs,
    }


def song_list(request):
    songs_list = Song.objects.select_related('singer').all().order_by('?')
    paginator = Paginator(songs_list, 12)
    page_number = request.GET.get('page', 1)
    songs = paginator.get_page(page_number)
    ctx = build_pagination_context(songs, request)
    ctx['songs'] = songs
    return render(request, 'song_list.html', ctx)


def song_detail(request, song_id):
    song = get_object_or_404(Song.objects.select_related('singer'), id=song_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(song=song, content=content)
    comments = song.comment.all().order_by('-release_time')
    lyrics = clean_lyrics(song.lyrics) if song.lyrics else ''
    return render(request, 'song_detail.html', {'song': song, 'comments': comments, 'lyrics': lyrics})


def singer_list(request):
    singers_list = Singer.objects.all().order_by('id')
    paginator = Paginator(singers_list, 12)
    page_number = request.GET.get('page', 1)
    singers = paginator.get_page(page_number)
    ctx = build_pagination_context(singers, request)
    ctx['singers'] = singers
    return render(request, 'singer_list.html', ctx)


def singer_detail(request, singer_id):
    singer = get_object_or_404(Singer, id=singer_id)
    songs = singer.song.all()
    return render(request, 'singer_detail.html', {'singer': singer, 'songs': songs})


def get_search_results(query, search_type):
    if search_type == 'singer':
        return Singer.objects.filter(
            Q(name__icontains=query) | Q(intro__icontains=query)
        ).order_by('id')

    if not query:
        return Song.objects.none()

    return (
        Song.objects.filter(
            Q(name__icontains=query) |
            Q(singer__name__icontains=query) |
            Q(lyrics__icontains=query)
        )
        .select_related('singer')
        .annotate(
            match_priority=Case(
                When(Q(name__icontains=query), then=Value(0)),
                When(Q(lyrics__icontains=query), then=Value(1)),
                When(Q(singer__name__icontains=query), then=Value(2)),
                default=Value(2),
                output_field=IntegerField(),
            )
        )
        .order_by('match_priority', 'id')
    )


def search(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'song')
    start_time = time.time()

    results_list = get_search_results(query, search_type)

    elapsed = time.time() - start_time
    paginator = Paginator(results_list, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    ctx = build_pagination_context(page_obj, request)
    ctx.update({
        'results': page_obj,
        'query': query,
        'search_type': search_type,
        'total_count': paginator.count,
        'elapsed': f'{elapsed:.4f}',
    })
    return render(request, 'search_results.html', ctx)


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        song_id = comment.song.id
        comment.delete()
        return redirect('song_detail', song_id=song_id)
    return redirect('song_list')
