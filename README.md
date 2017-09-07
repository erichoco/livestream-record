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

### Inke 
Run
`python3 scraper_inke.py '[Inke Room URL]'`
to record. (Single quotes required, brackets not)

### Momo
Run
`python3 scraper_momo.py [Room ID]`
to record. 
> Room ID: if an URL of Momo looks like 'https://web.immomo.com/live/399886888?rf=683', the room ID is 399886888


