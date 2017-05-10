vlc=/Applications/VLC.app/Contents/MacOS/VLC
a='#transcode{vcodec=mp4v,vb=1600,scale=1,acodec=mp3,ab=128,channels=2,samplerate=44100}:std{access=file,mux=mp4,dst='
b='/video'
c='.mp4}'
$vlc -I rc screen:// --screen-fps=5.0 --sout=$a$1$b$2$c