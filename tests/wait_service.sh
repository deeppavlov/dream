#!/bin/bash

timeout=${WAIT_TIMEOUT:-1000}
url=${CHECK_URL}
reply=${REPLY}
interval=${WAIT_INTERVAL:-10}

while [ $timeout -gt 0 ]; do
  res=$(curl -XGET "$url" -s -o /dev/null -w "%{http_code}")
  if [ "$res" == "200" ]; then
    return 0
  fi
  sleep $interval
  ((timeout-=interval))
  echo wait $url timeout in $timeout sec..
done

return 1
