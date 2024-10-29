#!/usr/bin/env bash

start_client () {
  client_name="$1"
  rm -rf "./${client_name}/"{downloads,state}
  gnome-terminal --title "$client_name" -- bash --login -ic "conda activate deluge; python -m deluge.core.daemon_entry -L debug -i 127.0.0.1 -o 127.0.0.1 -d -c ./local/${client_name} | tee ${client_name}.log; exec bash"
}

gnome-terminal --title "Tracker" -- bash -c "cd ../bittorrent-tracker; ./bin/cmd.js --port 6969; exec bash"

start_client "client1"
start_client "client2"

sleep 2 # yeah this is a hack
python -m experiment experiment-local.json