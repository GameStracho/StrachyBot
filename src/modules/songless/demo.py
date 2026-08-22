import static_ffmpeg
static_ffmpeg.add_paths()

from pydub import AudioSegment
import requests

# 1. Stáhnutí MP3 ukázky z Deezeru
# preview_url = "https://cdns-preview-d.dzcdn.net/stream/..."
preview_url = "https://cdnt-preview.dzcdn.net/api/1/1/4/8/4/0/4848102b635d148c22c225b713a08512.mp3?hdnea=exp=1787379766~acl=/api/1/1/4/8/4/0/4848102b635d148c22c225b713a08512.mp3*~data=user_id=0,application_id=42~hmac=9ef0dac07d26b7bfc379954938913ce177dd2db3c09b8bed559a0d94683fe103"

response = requests.get(preview_url)
with open("song.mp3", "wb") as f:
    f.write(response.content)

# 2. Oříznutí na požadovaný počet sekund (např. 2 sekundy)
duration_ms = 2 * 1000  # Pydub pracuje v milisekundách
song = AudioSegment.from_file("song.mp3")
cut_song = song[:duration_ms]

# 3. Uložení výsledného souboru k odeslání
cut_song.export("snippet.mp3", format="mp3")
