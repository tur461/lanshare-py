import threading, time, base64, sys, pyaudio

class AudioCapture():
    def __init__(self):
        self.RATE = 44100
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.audio = pyaudio.PyAudio()
        self.buffer = b""

        # Select default output device for loopback capture
        # On Windows: use WASAPI loopback
        if sys.platform == "win32":
            wasapi_info = None
            for i in range(self.audio.get_device_count()):
                dev = self.audio.get_device_info_by_index(i)
                if (dev.get("name").lower().find("loopback") != -1):
                    wasapi_info = i
                    break
            if wasapi_info is None:
                raise RuntimeError("No WASAPI loopback device found! Enable 'Stereo Mix' or use a virtual audio driver.")
            self.device_index = wasapi_info
        else:
            # macOS/Linux -> user must select virtual device (BlackHole, Soundflower, Pulse monitor)
            self.device_index = None  # default device, may need manual config

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
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def record(self):
        while self.running:
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            self.buffer = base64.b64encode(data)
            time.sleep(0.01)  # small sleep to reduce CPU usage

    def gen(self):
        """Return latest audio chunk (base64 encoded)"""
        if isinstance(self.buffer, bytes):
            return self.buffer.decode()
        return self.buffer

audiolive = AudioCapture()
