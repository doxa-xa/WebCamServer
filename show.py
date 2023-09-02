import pyaudio

FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024

audio = pyaudio.PyAudio()

def record():
    #encode recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, output=True,
                        frames_per_buffer=CHUNK, input_device_index=0)
    #read encoding
    data = stream.read(CHUNK)
    return data