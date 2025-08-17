import threading, time, base64, sys, pyaudio

class AudioCapture:
    def __init__(self):
        self.RATE = 44100
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.audio = pyaudio.PyAudio()
        self.buffer = b""

        self.device_index = None
        if sys.platform == "win32":
            # Try to find WASAPI loopback device
            for i in range(self.audio.get_device_count()):
                dev = self.audio.get_device_info_by_index(i)
                if "loopback" in dev.get("name").lower():
                    self.device_index = i
                    break

            if self.device_index is None:
                print("[WARN] No WASAPI loopback device found! Falling back to default input (microphone).")
                # fallback to default mic
                self.device_index = None  

        self.stream = self.audio.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      input_device_index=self.device_index,
                                      frames_per_buffer=self.CHUNK)

        self.running = True
        threading.Thread(target=self.record, daemon=True).start()

    def __del__(self):
        self.running = False
        if hasattr(self, "stream"):  # safe cleanup
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
                self.buffer = base64.b64encode(data)
            except Exception as e:
                print("[AudioCapture] Error reading audio:", e)
                time.sleep(0.05)
            time.sleep(0.01)

    def gen(self):
        """Return latest audio chunk (base64 encoded)"""
        if isinstance(self.buffer, bytes):
            return self.buffer.decode()
        return self.buffer
