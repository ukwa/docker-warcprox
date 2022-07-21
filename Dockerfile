FROM python:3.10-slim

MAINTAINER Andrew.Jackson@bl.uk

RUN apt-get update && \
        apt-get install -y \
        build-essential \
        libffi-dev \
        && rm -rf /var/lib/apt/lists/*


COPY setup.py .
COPY warcprox-plugins warcprox-plugins

RUN python setup.py install

EXPOSE 8000

VOLUME /output/warcs /output/log /db /ca

#ENTRYPOINT ["warcprox", "--address", "0.0.0.0", "--port", "8888"]

CMD warcprox -b 0.0.0.0 -d /output/warcs --base32 -z --rollover-idle-time 3600 --dedup-db-file /dev/null --stats-db-file /dev/null --quiet --plugin warcprox-plugins.listeners.UpdateOutbackCDX --plugin warcprox-plugins.listeners.KafkaCaptureFeed 2>&1 | tee /output/log
