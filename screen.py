# screenshare.py
# Copyright (C) 2021  Qijun Gu
# Modified to add PyAudio speaker/mic capture

import threading, time, base64, sys
import pyaudio
from collections import deque

ver = sys.version_info.major
if ver == 2:
    import StringIO as io
elif ver == 3:
    import io

if sys.platform in ["win32", "darwin"]:
    from PIL import ImageGrab as ig
else:
    import pyscreenshot as ig
    bkend = "pygdk3"


class Screen:
    def __init__(self):
        self.FPS = 10
        self.screenbuf = ""
        self.password = ""
        if ver == 2:
            self.screenfile = io.StringIO()
        elif ver == 3:
            self.screenfile = io.BytesIO()
        threading.Thread(target=self.getframes, daemon=True).start()

    def __del__(self):
        self.screenfile.close()

    def getframes(self):
        while True:
            if sys.platform in ["win32", "darwin"]:
                im = ig.grab()
            else:
                im = ig.grab(childprocess=False, backend=bkend)
            self.screenfile.seek(0)
            self.screenfile.truncate(0)
            im_converted = im.convert("RGB")
            im_converted.save(
                self.screenfile, format="jpeg", quality=75, progressive=True
            )
            self.screenbuf = base64.b64encode(self.screenfile.getvalue())
            time.sleep(1.0 / self.FPS)

    def gen(self):
        if ver == 2:
            return self.screenbuf
        elif ver == 3:
            return self.screenbuf.decode()

class AudioCapture:
    def __init__(self):
        self.RATE = 44100
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.audio = pyaudio.PyAudio()
        self.que = deque(maxlen=200)

        self.device_index = None
        if sys.platform == "win32":
            # Try to find WASAPI loopback device
            for i in range(self.audio.get_device_count()):
                dev = self.audio.get_device_info_by_index(i)
                if "loopback" in dev.get("name").lower():
                    self.device_index = i
                    break

            if self.device_index is None:
                print(
                    "[WARN] No WASAPI loopback device found! "
                    "Falling back to default input (microphone)."
                )
                self.device_index = None  # fallback mic

        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.CHUNK,
        )

        self.running = True
        threading.Thread(target=self.record, daemon=True).start()

    def __del__(self):
        self.running = False
        if hasattr(self, "stream"):
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        if hasattr(self, "audio"):
            try:
                self.audio.terminate()
            except Exception:
                pass

    def record(self):
        while self.running:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.que.append(data)
            except Exception as e:
                print("[AudioCapture] Error reading audio:", e)
                time.sleep(0.05)
            time.sleep(0.01)

    def gen(self):
        chunks = []
        while self.que:
            chunks.append(self.que.popleft())
        rawData = b''.join(chunks)
        print('audio capture len:', len(rawData))
        return base64.b64encode(rawData).decode('utf-8')


# Instantiate both
screenlive = Screen()
audiolive = AudioCapture()
