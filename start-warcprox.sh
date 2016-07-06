sleep 5
warcprox --rethinkdb-servers rethinkdb -b 0.0.0.0 -d /output/warcs --base32 -z --rollover-idle-time 3600
