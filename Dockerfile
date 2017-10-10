FROM python:3.6-alpine

MAINTAINER steranin

COPY . .

RUN apk add --update build-base libffi libffi-dev openssl openssl-dev git && \
    python setup.py install && \
    apk del build-base libffi-dev openssl-dev git

EXPOSE 8000

VOLUME /output/warcs /db /ca

#ENTRYPOINT ["warcprox", "--address", "0.0.0.0", "--port", "8888"]

CMD warcprox -b 0.0.0.0 -d /output/warcs --base32 -z --rollover-idle-time 3600 --plugin warcprox-plugins.kafkafeed.CaptureFeed --plugin warcprox-plugins.kafkafeed.UpdateOutbackCDX 2>&1 | tee /output/log

