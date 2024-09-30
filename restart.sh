#!/bin/bash
	screen -S dst_server1 -X quit > /dev/null 2>&1
	cd /home/dst/server_dst/bin
	screen -dmS dst_server1 ./start.sh