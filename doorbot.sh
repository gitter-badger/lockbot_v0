#!/bin/bash

scriptpid=$$
echo $scriptpid | sudo tee /var/run/lockbot.pid

CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $CWD

path_to_git=$(which git)
if [ ! -x "$path_to_git" ] ; then
  sudo apt-get --assume-yes install git-core
fi

if [ -n "$SOCKS_HOST" -a -n "$SOCKS_PORT" ]; then
  if ! dpkg -s python-socksipy >/dev/null 2>&1 ; then
    sudo apt-get --assume-yes install python-socksipy
  fi
fi

path_to_gpio=$(which gpio)
if [ ! -x "$path_to_gpio" ] ; then
  git clone git://git.drogon.net/wiringPi
  cd wiringPi
  git pull origin
  ./build
fi

MASTERID=${MASTERID:-0000000000}
# require MASTERID
#: ${MASTERID?"Need to set MASTERID"}

: ${HOSTURL?"Need to set HOSTURL to be able to query acserver"}


cd $CWD

# set the lock pin controller to out
gpio -g mode 23 out
gpio -g write 23 1

gpio -g mode 17 out
gpio -g mode 18 out
gpio -g write 18 1
gpio -g write 17 0

sudo apt-get  --assume-yes  install python3-pip
#sudo /usr/bin/pip-3.2 install urllib2
sudo /usr/bin/pip-3.2 install PySocks
sudo /usr/bin/pip-3.2 install requests
sudo /usr/bin/pip-3.2 install requesocks

if [ -n "$SOCKS_HOST" -a -n "$SOCKS_PORT" ]; then
  if ! dpkg -s python-socksipy >/dev/null 2>&1 ; then    
    sudo /usr/bin/pip-3.2 install PySocks
    sudo /usr/bin/pip-3.2 install requests
    sudo /usr/bin/pip-3.2 install requesocks
  fi
fi

echo "starting rc522 loop"





while true
do
# need to pass a bunch of login/auth stuff through from env to sudo
sudo HOSTURL=http://172.31.24.5:1234 MASTERID=B337FAA4DA  /home/pi/lockbot/rfid.py &
childpid=$!
if wait $childpid ; then
	echo "doorbot on $? signal"
	
fi

done
