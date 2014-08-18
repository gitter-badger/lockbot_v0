#!/bin/bash

scriptpid=$$
echo $scriptpid | sudo tee /var/run/lockbot.pid

MASTERID=${MASTERID:-0000000000}
# require MASTERID
#: ${MASTERID?"Need to set MASTERID"}

: ${HOSTURL?"Need to set HOSTURL to be able to query acserver"}

CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $CWD

path_to_git=$(which git)
if [ ! -x "$path_to_git" ] ; then
  sudo apt-get --assume-yes install git-core
fi

# install the wiring Pi library, which provides the gpio command

path_to_gpio=$(which gpio)
if [ ! -x "$path_to_gpio" ] ; then
  git clone git://git.drogon.net/wiringPi
  cd wiringPi
  git pull origin
  #this calls sudo
  ./build
fi

cd $CWD

# set the lock pin controller to out and shut the lock while the other
# packages are being installed

# set the lock GPIO pint output and set it to closed
gpio -g mode 23 out
gpio -g write 23 1

# init the green led off red led on
gpio -g mode 17 out
gpio -g mode 18 out
gpio -g write 18 1
gpio -g write 17 0

# quick2wire needs python3
sudo apt-get --assume-yes install python3 python3-pip

# if you want to debug this script remotely, then setting SOCKS_HOST and
# SOCKS_PORT to some gateway host, will allow the pi to talk to the acserver
if [ -n "$SOCKS_HOST" -a -n "$SOCKS_PORT" ]; then
  #if ! dpkg -s python-socksipy >/dev/null 2>&1 ; then
    #sudo apt-get --assume-yes install python-socksipy
    sudo /usr/bin/pip-3.2 install PySocks
    sudo /usr/bin/pip-3.2 install requests
    sudo /usr/bin/pip-3.2 install requesocks
  #fi
fi


#path_to_gpio_admin=$(which gpio-admin)
if [ ! -f "/usr/local/bin/gpio-admin" ] ; then
  git clone https://github.com/quick2wire/quick2wire-gpio-admin.git
  cd quick2wire-gpio-admin
  make
  sudo make install
fi

cd $CWD

if ! python3  -c "import quick2wire" ; then

git clone https://github.com/quick2wire/quick2wire-python-api.git
cd quick2wire-python-api
sudo python3 setup.py install

fi

cd $CWD

echo "starting rfid loop"

# not sure if this while loop helps, its a legacy of the previous version

while true
do
# need to pass a bunch of login/auth stuff through from env to sudo
sudo HOSTURL=$HOSTURL MASTERID=$MASTERID  /home/pi/lockbot/rfid.py &
childpid=$!
if wait $childpid ; then
	echo "doorbot on $? signal"
	
fi

done
