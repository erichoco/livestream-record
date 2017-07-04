import pyaudio
import wave
import argparse
import sys
import select
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

def stop_save(output, p, stream, frames):
    save(output, p , frames)
    print("* stop audio")
    stream.stop_stream()
    stream.close()
    p.terminate()

def save(output, p, frames):
    print("* saving audio")
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

    exiting = False

    last_min = time.gmtime()[4]
    count = 0

    try:
        print("* recording audio")
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

            # save every 20 min
            cur_min = time.gmtime()[4]
            over = 60 if cur_min < last_min else 0
            if (cur_min+over) - last_min > 20:
                last_min = cur_min
                save(args.path + "/audio" + args.suffix + "-" + str(count) + ".wav", p, frames)
                frames = []
                count = count + 1
                continue

            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                raise KeyboardInterrupt

    except KeyboardInterrupt:
        stop_save(args.path + "/audio" + args.suffix + ".wav", p, stream, frames)
        exit(0)


    except Exception as e:
        stop_save(args.path + "/audio" + args.suffix + ".wav", p, stream, frames)
        print(e)
        exit(0)
