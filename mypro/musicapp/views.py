from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Singer, Song, Comment
import time


def song_list(request):
    songs_list = Song.objects.select_related('singer').all().order_by('id')
    paginator = Paginator(songs_list, 10)
    page_number = request.GET.get('page', 1)
    songs = paginator.get_page(page_number)
    return render(request, 'song_list.html', {'songs': songs})


def song_detail(request, song_id):
    song = get_object_or_404(Song.objects.select_related('singer'), id=song_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(song=song, content=content)
    comments = song.comment.all().order_by('-release_time')
    return render(request, 'song_detail.html', {'song': song, 'comments': comments})


def singer_list(request):
    singers_list = Singer.objects.all().order_by('id')
    paginator = Paginator(singers_list, 10)
    page_number = request.GET.get('page', 1)
    singers = paginator.get_page(page_number)
    return render(request, 'singer_list.html', {'singers': singers})


def singer_detail(request, singer_id):
    singer = get_object_or_404(Singer, id=singer_id)
    songs = singer.song.all()
    return render(request, 'singer_detail.html', {'singer': singer, 'songs': songs})


def search(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'song')
    start_time = time.time()

    if query:
        if search_type == 'singer':
            results_list = Singer.objects.filter(
                Q(name__icontains=query) | Q(intro__icontains=query)
            ).order_by('id')
        else:
            results_list = Song.objects.filter(
                Q(name__icontains=query) |
                Q(singer__name__icontains=query) |
                Q(lyrics__icontains=query)
            ).select_related('singer').distinct().order_by('id')
    else:
        results_list = Singer.objects.none() if search_type == 'singer' else Song.objects.none()

    elapsed = time.time() - start_time
    paginator = Paginator(results_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'search_results.html', {
        'results': page_obj,
        'query': query,
        'search_type': search_type,
        'total_count': paginator.count,
        'elapsed': f'{elapsed:.4f}',
    })


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        song_id = comment.song.id
        comment.delete()
        return redirect('song_detail', song_id=song_id)
    return redirect('song_list')
