export PYTHONUNBUFFERED=true
export CDXSERVER_ENDPOINT=http://localhost:9090/fc
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export KAFKA_CRAWLED_TOPIC=crawl-log
#warcprox -b 0.0.0.0 -p 8000 -d ./output/warcs --base32 -z --rollover-idle-time 3600 --plugin warcprox-plugins.listeners.KafkaCaptureFeed --plugin warcprox-plugins.listeners.UpdateOutbackCDX
warcprox -b 0.0.0.0 -p 8000 -d ./output/warcs --base32 -z --rollover-idle-time 3600 --plugin warcprox-plugins.listeners.KafkaCaptureFeed
