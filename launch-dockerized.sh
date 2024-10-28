#!/usr/bin/env bash
set -e

start_client () {
  client_name="$1"
  sudo rm -rf "./dockerized/${client_name}"
  mkdir -p "./dockerized/${client_name}"
  gnome-terminal --title "$client_name" -- bash -ic "docker run --rm --name ${client_name} -v ${PWD}/dockerized/${client_name}:/var/lib/deluge:rw -it deluge; exec bash"
}

gnome-terminal --title "Tracker" -- bash -c "cd ../bittorrent-tracker; ./bin/cmd.js --http-hostname 192.168.1.99 --udp-hostname 192.168.1.99 --port 6969; exec bash"

start_client "client1"
start_client "client2"

sleep 2 # yeah this is a hack
sudo chmod a+r -R ./dockerized
#python -m experiment experiment-local.json