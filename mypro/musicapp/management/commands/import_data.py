import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from musicapp.models import Singer, Song

class Command(BaseCommand):
    help = 'Import singer.json and song.json into the database'

    def handle(self, *args, **options):
        import sys
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    def handle(self, *args, **options):
        singer_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'singer.json'))
        song_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'song.json'))

        singer_cache = {}

        if os.path.exists(singer_path):
            with open(singer_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    photo = data.get('photo') or ''
                    singer, created = Singer.objects.get_or_create(
                        name=data['name'],
                        defaults={
                            'intro': data.get('intro', ''),
                            'url': data.get('url', ''),
                            'image': photo,
                        }
                    )
                    singer_cache[singer.name] = singer
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Created singer: {singer.name}"))
                    else:
                        self.stdout.write(f"Singer already exists: {singer.name}")
        else:
            self.stdout.write(self.style.WARNING(f"singer.json not found at {singer_path}"))

        if os.path.exists(song_path):
            with open(song_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    singer_name = data.get('singername', '')
                    singer = singer_cache.get(singer_name)
                    if not singer:
                        self.stdout.write(self.style.WARNING(f"Singer '{singer_name}' not found, skipping song '{data.get('songname', '')}'"))
                        continue
                    photo = data.get('photo') or ''
                    song, created = Song.objects.get_or_create(
                        name=data['songname'],
                        singer=singer,
                        defaults={
                            'url': data.get('url', ''),
                            'image': photo,
                            'lyrics': data.get('lyric') or '',
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  Created song: {song.name}"))
                    else:
                        self.stdout.write(f"  Song already exists: {song.name}")
        else:
            self.stdout.write(self.style.WARNING(f"song.json not found at {song_path}"))

        self.stdout.write(self.style.SUCCESS('Import completed!'))
