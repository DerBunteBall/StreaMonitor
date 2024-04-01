import errno
import subprocess
import sys
from pathlib import Path # Use pathlib for nice file handling

import requests.cookies
from threading import Thread
from parameters import DEBUG, MOVE_DIR


def getVideoFfmpeg(self, url, filename):
    dl_file = Path(filename)
    dest_file = Path(MOVE_DIR).joinpath(dl_file)
    move_dir = Path(MOVE_DIR)
    cmd = [
        'ffmpeg',
        '-user_agent', self.headers['User-Agent']
    ]

    if type(self.cookies) is requests.cookies.RequestsCookieJar:
        cookies_text = ''
        for cookie in self.cookies:
            cookies_text += cookie.name + "=" + cookie.value + "; path=" + cookie.path + '; domain=' + cookie.domain + '\n'
        if len(cookies_text) > 10:
            cookies_text = cookies_text[:-1]
        cmd.extend([
            '-cookies', cookies_text
        ])

    cmd.extend([
        '-i', url,
        '-c:a', 'copy',
        '-c:v', 'copy',
        '-fs', '2G',
        filename
    ])

    class _Stopper:
        def __init__(self):
            self.stop = False

        def pls_stop(self):
            self.stop = True

    stopping = _Stopper()

    error = False
    def execute():
        nonlocal error
        try:
            stdout = open(filename + '.stdout.log', 'w+') if DEBUG else subprocess.DEVNULL
            stderr = open(filename + '.stderr.log', 'w+') if DEBUG else subprocess.DEVNULL
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.Popen(
                args=cmd, stdin=subprocess.PIPE, stderr=stderr, stdout=stdout, startupinfo=startupinfo)
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.logger.error('FFMpeg executable not found!')
                error = True
                return
            else:
                self.logger.error("Got OSError, errno: " + str(e.errno))
                error = True
                return

        while process.poll() is None:
            if stopping.stop:
                process.communicate(b'q')
                break
            try:
                process.wait(1)
            except subprocess.TimeoutExpired:
                pass
        
        # Create move Folder if not exists
        if not move_dir.exists():
            move_dir.create(parents=True, exists_ok=True)
        # Move file
        dl_file.rename(dest_file)

        if process.returncode and process.returncode != 0 and process.returncode != 255:
            self.logger.error('The process exited with an error. Return code: ' + str(process.returncode))
            error = True
            return

    thread = Thread(target=execute)
    thread.start()
    self.stopDownload = lambda: stopping.pls_stop()
    thread.join()
    self.stopDownload = None
    return not error
