#!/bin/bash

CWD=$(pwd)

path_to_git=$(which git)
if [ ! -x "$path_to_git" ] ; then
  sudo apt-get install git-core
fi


path_to_gpio=$(which gpio)
if [ ! -x "$path_to_gpio" ] ; then
  git clone git://git.drogon.net/wiringPi
  cd wiringPi
  git pull origin
  ./build
fi


: ${MASTERID?"Need to set MASTERID"}
: ${HOSTURL?"Need to set HOSTURL"}


cd $CWD

while true
do
if sudo MASTERID=$MASTERID HOSTURL=$HOSTURL python $(pwd)/doorbot.py;
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
