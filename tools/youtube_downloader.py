import yt_dlp
import sys
from pathlib import Path

class FileTooLargeError(Exception):
    def __init__(self, size_mb, limit_mb):
        super().__init__(f"File size {size_mb:.2f} MB exceeds limit of {limit_mb} MB")
        self.size_mb = size_mb
        self.limit_mb = limit_mb


def find_ffmpeg(custom_paths: list[str] = None) -> str | None:
    try:
        ffmpeg_path_str = yt_dlp.utils.check_executable('ffmpeg.exe')
        if ffmpeg_path_str:
            return ffmpeg_path_str
    except NameError:
        pass

    common_locations = ['C:/ffmpeg/bin/ffmpeg.exe']
    common_locations.extend([
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/opt/homebrew/bin/ffmpeg',
        'ffmpeg'
    ])

    if custom_paths:
        common_locations.extend(custom_paths)

    for loc in common_locations:
        if Path(loc).is_file():
            return str(Path(loc))

    print(
        "Warning: FFmpeg executable not found in PATH or common locations.",
        file=sys.stderr
    )
    print(
        "Ensure FFmpeg is installed and its location is in your system's "
        "PATH environment variable for audio extraction/conversion.",
        file=sys.stderr
    )
    return None


def download_audio(
        url: str,
        output_dir: str | Path = Path('.'),
        audio_format: str = 'mp3',
        audio_quality: str = '192',
        max_filesize_mb: float | None = None
) -> Path | None:
    """
    Downloads audio from a YouTube URL using yt-dlp, respecting file size
    limits, and returns the file path.

    Args:
        url: The YouTube video or playlist URL.
        output_dir: The directory where the audio file(s) should be saved.
                    Defaults to the current directory.
        audio_format: Desired audio format (e.g., 'mp3', 'm4a', 'wav', 'opus').
        audio_quality: Desired audio quality (bitrate in kbit/s, e.g.,
                       '128', '192', '320'). '0' for best available.
        max_filesize_mb: Maximum allowed file size in Megabytes (MB).
                         If None or 0, no limit is applied.

    Returns:
        A Path object to the downloaded audio file if successful and within
        size limits, otherwise None.
        Note: For playlists, size check applies to *each* video individually.
              Returns the path of the *last* successfully processed file.
    """
    if not url:
        return None

    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    last_successful_path = None
    error_occurred = False
    ffmpeg_path = find_ffmpeg()

    def progress_hook(d):
        nonlocal last_successful_path
        if d['status'] == 'finished':
            filepath = d.get('filename') or d.get('info_dict', {}).get('_filename')
            if filepath:
                current_file = Path(filepath)
                if not current_file.is_absolute():
                    current_file = output_path / current_file.name

                if current_file.suffix.lower() == f".{audio_format.lower()}" and current_file.exists():
                    size_mb = current_file.stat().st_size / (1024 * 1024)
                    if max_filesize_mb and size_mb > max_filesize_mb:
                        current_file.unlink(missing_ok=True)
                        raise FileTooLargeError(size_mb, max_filesize_mb)
                    last_successful_path = current_file

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': {
            'default': str(output_path / '%(title)s.%(ext)s'),
        },
        'postprocessors': [], # Initialize empty, add later if ffmpeg found
        'ffmpeg_location': ffmpeg_path,
        'keepvideo': False,
        'noplaylist': False,
        'progress_hooks': [progress_hook],
        'noprogress': True,
        'ignoreerrors': True,
        'restrictfilenames': True,
        'quiet': True,
        'verbose': False,
        'no_warnings': True,
        'simulate': False,
        'extract_flat': False,
    }

    # Only add audio extraction postprocessor if ffmpeg is available
    if ffmpeg_path:
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': audio_quality,
        })
    else:
        ydl_opts['format'] = f'bestaudio[ext={audio_format}]/bestaudio/best'


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return None
            except yt_dlp.utils.DownloadError:
                return None
            except Exception:
                return None

            entries_to_process = info.get('entries') or ([info] if info else [])
            urls_to_download = []

            for entry_info in entries_to_process:
                if not entry_info:
                    continue

                filesize_bytes = None

                try:

                    sim_opts = ydl_opts.copy()
                    sim_opts['simulate'] = True
                    sim_opts['quiet'] = True
                    sim_opts['verbose'] = False
                    sim_opts['progress_hooks'] = []
                    sim_opts['postprocessors'] = []
                    sim_opts['keepvideo'] = True

                    with yt_dlp.YoutubeDL(sim_opts) as sim_ydl:
                        processed_entry_info = sim_ydl.process_ie_info(entry_info, download=False)
                        filesize_bytes = processed_entry_info.get('filesize') or processed_entry_info.get('filesize_approx')
                        if not filesize_bytes and processed_entry_info.get('requested_formats'):
                            selected_format_info = processed_entry_info['requested_formats'][0]
                            filesize_bytes = selected_format_info.get('filesize') or selected_format_info.get('filesize_approx')
                        elif not filesize_bytes and not processed_entry_info.get('requested_formats'):
                            filesize_bytes = entry_info.get('filesize') or entry_info.get('filesize_approx')

                except Exception:
                    # Fallback to original info if simulation fails
                    filesize_bytes = entry_info.get('filesize') or entry_info.get('filesize_approx')


                if max_filesize_mb and max_filesize_mb > 0 and filesize_bytes:
                    filesize_mb = filesize_bytes / (1024 * 1024)
                    if filesize_mb > max_filesize_mb:
                        continue

                entry_url = entry_info.get('webpage_url') or entry_info.get('original_url') or entry_info.get('url')
                if entry_url:
                    urls_to_download.append(entry_url)


            if not urls_to_download:
                return None

            ydl.download(urls_to_download)

    except yt_dlp.utils.DownloadError:
        error_occurred = True
    except Exception:
        error_occurred = True


    if last_successful_path:
        return last_successful_path
    else:
        return None
