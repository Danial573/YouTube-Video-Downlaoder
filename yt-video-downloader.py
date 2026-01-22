# yt_downloader.py
"""
Simple YouTube video downloader
Requires: pip install yt-dlp

Legal note:
    Downloading videos may violate YouTube's Terms of Service
    Use only for content you have permission to download
    (your own videos, public domain, Creative Commons with download allowed, etc.)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    from yt_dlp import YoutubeDL, DownloadError
except ImportError:
    print("Error: yt-dlp is not installed")
    print("Please run:   pip install --upgrade yt-dlp")
    sys.exit(1)


def sizeof_fmt(num, suffix="B"):
    """Human friendly file size"""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def main():
    parser = argparse.ArgumentParser(
        description="Simple YouTube video downloader",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("url", help="YouTube video or playlist URL")
    
    parser.add_argument(
        "-f", "--format",
        choices=["best", "bestvideo", "bestaudio", "720", "1080", "audio"],
        default="best",
        help="""Quality/format to download:
  best        = best video + best audio combined (default)
  bestvideo   = best quality video only (no audio)
  bestaudio   = best quality audio only
  720         = ~720p video+audio
  1080        = ~1080p video+audio (if available)
  audio       = audio only (m4a / best available)"""
    )
    
    parser.add_argument(
        "-o", "--output",
        default="%(title)s [%(id)s].%(ext)s",
        help="output filename template (default: %(title)s [%(id)s].%(ext)s)"
    )
    
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="list all available formats and exit"
    )
    
    parser.add_argument(
        "--no-playlist",
        action="store_true",
        help="download only the video, even if URL is a playlist"
    )

    args = parser.parse_args()

    ydl_opts = {
        'outtmpl': args.output,
        'quiet': False,
        'no_warnings': True,
        'continuedl': True,
        'retries': 10,
        'fragment_retries': 10,
        'noplaylist': args.no_playlist,
        'progress_hooks': [progress_hook],
    }

    # Format selection
    if args.format == "best":
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
    elif args.format == "bestvideo":
        ydl_opts['format'] = 'bestvideo'
    elif args.format == "bestaudio":
        ydl_opts['format'] = 'bestaudio/best'
    elif args.format == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }]
    elif args.format == "720":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
    elif args.format == "1080":
        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'

    if args.list_formats:
        ydl_opts['listformats'] = True
        ydl_opts['quiet'] = True
        ydl_opts['simulate'] = True

    try:
        with YoutubeDL(ydl_opts) as ydl:
            print(f"\nFetching info... {args.url}")
            info = ydl.extract_info(args.url, download=not args.list_formats)

            if args.list_formats:
                return

            if 'entries' in info:  # playlist
                print(f"\nPlaylist: {info.get('title', 'Unknown')}")
                print(f"Found {len(info['entries'])} videos\n")
            else:
                title = info.get('title', 'Unknown title')
                duration = info.get('duration', 0)
                print(f"\nTitle: {title}")
                if duration:
                    mins, secs = divmod(duration, 60)
                    hrs, mins = divmod(mins, 60)
                    dur_str = f"{hrs:02d}:" if hrs else ""
                    dur_str += f"{mins:02d}:{secs:02d}"
                    print(f"Duration: {dur_str}")

    except DownloadError as e:
        print(f"\nDownload failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
        sys.exit(1)


def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '?%')
        speed = d.get('_speed_str', '? B/s')
        eta = d.get('_eta_str', '?s')
        
        total = d.get('total_bytes') or d.get('total_bytes_estimated')
        downloaded = d.get('downloaded_bytes') or 0
        
        if total:
            size_str = f"{sizeof_fmt(downloaded)} / {sizeof_fmt(total)}"
        else:
            size_str = sizeof_fmt(downloaded)
            
        msg = f"\r{percent}  {size_str}  {speed}  ETA {eta}"
        print(msg, end='', flush=True)
        
    elif d['status'] == 'finished':
        print("\nDownload complete, now post-processing...")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage examples:")
        print("  python yt_downloader.py https://youtu.be/dQw4w9WgXcQ")
        print("  python yt_downloader.py https://youtu.be/dQw4w9WgXcQ -f 1080")
        print("  python yt_downloader.py https://youtu.be/dQw4w9WgXcQ -f audio")
        print("  python yt_downloader.py https://youtube.com/playlist?list=PL... --no-playlist")
        print("\nFirst time? Run:  pip install --upgrade yt-dlp\n")
        sys.exit(0)

    main()