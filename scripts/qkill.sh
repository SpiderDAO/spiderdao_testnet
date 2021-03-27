if [[ -z "$1" ]];then
echo "empty"
exit
fi
kill -9 `ps aux | grep "$1" | grep -v grep | awk '{print $2}'`