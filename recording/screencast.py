import subprocess
import pyaudio
import wave
import socket

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"
VLC_PATH = "/Applications/VLC.app/Contents/MacOS/VLC"

class Screencast:
    def __init__(self, filepath, file_suffix):
        self.filepath = filepath
        self.file_suffix = file_suffix
        self.init_video()
        # self.init_audio()

    def start(self):
        self.p = subprocess.Popen(['bash', 'recording/screencast.sh', self.filepath, self.file_suffix])

        # recording audio
        # for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        #     data = self.stream.read(CHUNK, exception_on_overflow=False)
        #     self.frames.append(data)

    def stop(self):
        pass
        # subprocess.Popen()
        # self.p.kill()

        # stop recording audio
        # self.stream.stop_stream()
        # self.stream.close()
        # self.audio.terminate()
        # self.save_audio()

    def init_video(self):
        # self.video_ouput = self.filepath + "/video.mp4"
        self.video_output = "video.mp4"
        # self.command = VLC_PATH + r" -I macosx screen:// --screen-fps=5.0 --sout-transcode-vcodec=mp4v --sout-standard-access=file --sout-standard-mux=mp4 --sout-standard-dst=./video.mp4"
        self.command = VLC_PATH + r" -I dummy --extraintf rc --rc-host localhost:8082 screen:// --screen-fps=5.0 --sout-transcode-vcodec=mp4v --sout-standard-access=file --sout-standard-mux=mp4 --sout-standard-dst=./video.mp4"
        # ='#transcode{vcodec=mp4v,vb=1600,scale=1,acodec=mp3,ab=128,channels=2,samplerate=44100}:std{access=file,mux=mp4,dst=video.mp4}'"
        print(self.command.split())
        # self.commands = command.split()
        # self.command = VLC_PATH + " -I rc screen:// --screen-fps=5.0 --sout='#transcode{vcodec=mp4v,vb=1600,scale=1,acodec=mp3,ab=128,channels=2,samplerate=44100}:std{access=file,mux=mp4,dst=video.mp4}'"

    def init_audio(self):
        self.audio_output = self.filepath + "/audio.wav"

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)
        self.frames = []

    def save_audio(self):
        wf = wave.open(self.audio_output, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
