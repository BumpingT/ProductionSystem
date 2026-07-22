"""
热重载启动器 - 监听 main.py 修改, 自动重启应用
用法: python hot_reload.py
"""
import os, sys, time, subprocess, threading

# 强制无缓冲 + UTF-8 输出
os.environ['PYTHONUNBUFFERED'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
PROC = None

def log(msg):
    print(msg, flush=True)

class ReloadHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == WATCH_FILE:
            log("[重载] main.py 已修改, 重启中...")
            restart_app()

def start_app():
    global PROC
    if PROC is not None:
        PROC.kill()
        PROC.wait()
    log("[启动] main.py ...")
    PROC = subprocess.Popen(
        [sys.executable, 'main.py'],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, encoding='utf-8', errors='replace'
    )
    t = threading.Thread(target=read_output, args=(PROC,), daemon=True)
    t.start()

def read_output(proc):
    for line in proc.stdout:
        print("[app]", line.rstrip(), flush=True)
    if proc.returncode is not None and proc.returncode != 0:
        log("[警告] 进程退出, 代码: %d" % proc.returncode)

def restart_app():
    start_app()

def cleanup():
    global PROC
    if PROC is not None:
        PROC.kill()
        PROC.wait()

if __name__ == '__main__':
    log("=" * 50)
    log("  Hot Reload - 热重载")
    log("  监视: " + WATCH_FILE)
    log("  修改 main.py 后自动重启应用")
    log("  按 Ctrl+C 退出")
    log("=" * 50)

    start_app()

    event_handler = ReloadHandler()
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(WATCH_FILE), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("[退出] ...")
        cleanup()
        observer.stop()
    observer.join()
