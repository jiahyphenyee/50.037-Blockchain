#!/bin/bash
IDS=()

print_usage() {
  echo "$0 usage:" && grep " .)\ #" $0;
  exit 0;
}

finish() {
  kill $(jobs -p);
  rm mine_lock;
  exit;
}

trap finish SIGHUP SIGINT SIGTERM

while getopts "hm:s:f:" OPT; do
  case $OPT in
    m) # Set miner count.
      miner_count=$OPTARG ;;
    s) # Set SPV client count.
      spv_client_count=$OPTARG ;;
    f) # enable selfish miner
      selfish_miner_count=$OPTARG ;;
    h | *) # Display help.
      print_usage ;;
  esac
done

if [ $OPTIND -eq 1 ]; then
  print_usage;
  exit 1;
elif [ -z "$miner_count" ]; then
  echo 'Please set miners';
  exit 1;
else
  echo 'Use [CTRL+C] to stop the program if you want...'
  python3 addr_server.py &
  IDS+=($!)
  sleep 2



  if [ -n "$spv_client_count" ]; then
    for i in $(seq 1 $spv_client_count)
      do
        python3 demo.py $(($i + 22345)) 's' &
        IDS+=($!)
        sleep 1
      done
  fi

  for i in $(seq 1 $miner_count)
    do
      python3 demo.py $(($i + 12345)) 'm' &
      IDS+=($!)
      sleep 1
    done

      for i in $(seq 1 $selfish_miner_count)
    do
      python3 demo.py $(($i + 32345)) 'f' &
      IDS+=($!)
      sleep 1
    done
fi

sleep 2
echo 'Initialization complete, starting demo...'
echo ''
touch mine_lock

while true
do
	sleep 1
done