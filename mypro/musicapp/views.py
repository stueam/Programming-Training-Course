from django.shortcuts import render

# Create your views here.
from .models import Singer, Song, Comment

def song_list(request):
    songs = Song.objects.all()
    return render(request, 'song_list.html', {'songs': songs})

def song_detail(request, song_id):
    song = Song.objects.get(id=song_id)
    comments = song.comment.all()
    return render(request, 'song_detail.html', {'song': song, 'comments': comments})

def singer_list(request):
    singers = Singer.objects.all()
    return render(request, 'singer_list.html', {'singers': singers})

def singer_detail(request, singer_id):
    singer = Singer.objects.get(id=singer_id)
    songs = singer.song.all()
    return render(request, 'singer_detail.html', {'singer': singer, 'songs': songs})

def search(request):
    query = request.GET.get('q')
    songs = Song.objects.filter(name__icontains=query)
    singers = Singer.objects.filter(name__icontains=query)
    return render(request, 'search_results.html', {'songs': songs, 'singers': singers, 'query': query})