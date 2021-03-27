#!/bin/bash -xv

#Start SpiderDAO API
cd ../api
#. ../spiderdao_env
nohup python3 spiderdao_api.py &

echo `pwd`
#Start SpiderDAO Discord bot
cd ../discord_bot
nohup python3 discord_bot.py &
