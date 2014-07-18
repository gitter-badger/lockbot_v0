#!/bin/bash

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

while true
do
if sudo MASTERID=$MASTERID HOSTURL=$HOSTURL SOCKS_HOST=$SOCKS_HOST SOCKS_PORT=$SOCKS_PORT python doorbot.py;
then
echo "open lock on $? signal"
sudo /usr/local/bin/gpio -g write 23 0
sleep 3
sudo /usr/local/bin/gpio -g write 23 1 
echo "closing lock"

else
RETVAL=$?
echo "not opening lock on $RETVAL signal"

if (( $RETVAL == 1 )); then
# return val of 1 is an error from the python script so stop
exit 1
fi

fi

done
