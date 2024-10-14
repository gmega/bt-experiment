#!/usr/bin/env bash

start_client () {
  client_name="$1"
  rm -rf "$client_name/downloads"
  rm -rf "$client_name/state"

  mkdir "$client_name/downloads"
  mkdir "$client_name/state"

  gnome-terminal --title "$client_name" -- bash -ic "conda activate btexperiment; deluged -c ./${client_name} -L debug -i 127.0.0.1 -o 127.0.0.1 -d | tee ${client_name}.log; exec bash"
}

gnome-terminal --title "Tracker" -- bash -c "../opentracker/opentracker"

start_client "client1"
start_client "client2"