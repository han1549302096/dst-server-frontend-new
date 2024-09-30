#!/bin/bash
	screen -S dst_server2 -X quit > /dev/null 2>&1
	cd /home/dst/server_dst/bin
	screen -dmS dst_server2 ./start2.sh