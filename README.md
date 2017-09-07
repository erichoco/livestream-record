# livestream-record
Recording activities from live-streaming video sites.

Supporting:
- [x] [Momo](https://web.immomo.com/) (Chinese)
- [x] [Inke](http://inke.cn/hotlive_list.html) (Chinese)
- [ ] [Twitch](https://www.twitch.tv/)
- [ ] [Live.me](https://www.liveme.com/)

## Getting Started
### Installation
* Install python3
* `pip3 install selenium`
* Install Soundflower https://github.com/mattingalls/Soundflower/releases/tag/2.0b2

### Inke 
Run
`python3 scraper_inke.py '[Inke Room URL]'`
to record messsages and gifts. (Single quotes required, brackets not)

### Momo
Run
`python3 scraper_momo.py [Room ID]`
to record messsages and gifts. 
> Room ID: if an URL of Momo looks like 'https://web.immomo.com/live/399886888?rf=683', the room ID is 399886888

### Recording Video & Audio
Go to System Preferences > Sound > Output tab

Select **Soundflower (64ch)**

![](https://i.imgur.com/ie4dDcY.png)

Open QuickTime Player, go to File > New Screen Recording

At the right of the recording button, click to open a dropdown menu

Select **Soundflower (64ch)**

![](https://i.imgur.com/iCkKnxI.png)
