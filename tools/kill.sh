for pid in $(ps aux | grep swak.*start | sed '/grep/d' | awk '{print $2}'); do
    kill -9 $pid
done
