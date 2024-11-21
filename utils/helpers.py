import re

def is_valid_youtube_url(url):
    """Validates if the given URL is a valid YouTube link."""
    youtube_regex = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$')
    return bool(youtube_regex.match(url))
