#!/usr/bin/env bash

gnome-terminal --title "Tracker" -- bash -c "../opentracker/opentracker"
gnome-terminal --title "Deluge 1" -- bash -ic "conda activate btexperiment; deluged -c ./client1 -d; exec bash"
gnome-terminal --title "Deluge 2" -- bash -ic "conda activate btexperiment; deluged -c ./client2 -d; exec bash"
