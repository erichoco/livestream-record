import pyaudio
import wave
import argparse

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def stop_save(output, p, stream, frames):
    print("saving audio")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(output, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--path', default='./', help='specify output path')
    parser.add_argument('-s', '--suffix', default='', help='specify output file suffix')
    args = parser.parse_args()

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                  channels=CHANNELS,
                  rate=RATE,
                  input=True,
                  frames_per_buffer=CHUNK)
    frames = []

    try:
        print("* recording audio")
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

    except KeyboardInterrupt:
        stop_save(args.path + "/audio" + args.suffix + ".wav", p, stream, frames)


    except Exception as e:
        stop_save(args.path + "/audio" + args.suffix + ".wav", p, stream, frames)
        print(e)



