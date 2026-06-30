"""
Stream service: manages ffmpeg processes for RTSP → HLS transcoding.
Each camera gets its own ffmpeg subprocess writing HLS segments to disk.
"""
import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

STREAM_BASE = os.environ.get("STREAM_DIR", "/media/just_another_wine_app/streams")
FFMPEG = os.environ.get("FFMPEG_PATH", "/usr/bin/ffmpeg")

# Runtime registry: camera_id -> subprocess.Popen
_processes: Dict[int, subprocess.Popen] = {}


def stream_dir(camera_id: int) -> str:
    path = os.path.join(STREAM_BASE, str(camera_id))
    os.makedirs(path, exist_ok=True)
    return path


def start_stream(camera_id: int, stream_url: str) -> bool:
    """Spawn an ffmpeg process transcoding RTSP → HLS."""
    if camera_id in _processes and _processes[camera_id].poll() is None:
        return True  # already running

    out_dir = stream_dir(camera_id)
    manifest = os.path.join(out_dir, "index.m3u8")

    cmd = [
        FFMPEG,
        "-loglevel", "warning",
        "-rtsp_transport", "tcp",
        "-i", stream_url,
        "-c:v", "copy",
        "-an",                      # no audio
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "5",
        "-hls_flags", "delete_segments+append_list",
        "-hls_segment_filename", os.path.join(out_dir, "seg%03d.ts"),
        manifest,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _processes[camera_id] = proc
        logger.info(f"Stream started for camera {camera_id} (pid {proc.pid})")
        return True
    except FileNotFoundError:
        logger.error(f"ffmpeg not found at {FFMPEG}")
        return False
    except Exception as e:
        logger.error(f"Failed to start stream for camera {camera_id}: {e}")
        return False


def stop_stream(camera_id: int):
    proc = _processes.get(camera_id)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    _processes.pop(camera_id, None)
    logger.info(f"Stream stopped for camera {camera_id}")


def get_stream_status(camera_id: int) -> dict:
    proc = _processes.get(camera_id)
    if proc is None:
        return {"running": False, "pid": None}
    running = proc.poll() is None
    return {"running": running, "pid": proc.pid if running else None}


def get_hls_manifest_path(camera_id: int) -> Optional[str]:
    path = os.path.join(stream_dir(camera_id), "index.m3u8")
    return path if os.path.exists(path) else None


def stop_all():
    for camera_id in list(_processes.keys()):
        stop_stream(camera_id)
