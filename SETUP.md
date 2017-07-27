Amazon EC2 Linux GUI for Web Scraper
===============================================

## Installation
1. ssh to EC2 instance
2. Follow the top and second answers [here](https://stackoverflow.com/questions/25657596/how-to-set-up-gui-on-amazon-ec2-ubuntu-server)
  * Default username: `awsgui` / password: `tippinggui` (for vncserver too)
3. `git clone` this repo (branch `ec2`)
4. `sudo apt-get install python3-pip`
5. `pip3 install selenium`
6. `sudo apt-get install python3-pyaudio` or check out [here](https://people.csail.mit.edu/hubert/pyaudio/)
7. `sudo apt-get install vlc`

## Connecting GUI
1. Add EC2 instance security group => Custom TCP & port 5901
2. Get VNC client ([Mac](http://www.realvnc.com/download/get/1286/) [Windows](https://aws.amazon.com/premiumsupport/knowledge-center/connect-to-linux-desktop-from-windows/)
3. Use EC2 instance public DNS plus ":1" to connect (e.g. ec2-13-59-61-98.us-east-2.compute.amazonaws.com:1)
4. Install Chrome ([potential Chrome installation issue](https://askubuntu.com/questions/68724/cannot-install-google-chrome))


