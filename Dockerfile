FROM python:3.6-alpine

MAINTAINER steranin

RUN apk add --update build-base libffi libffi-dev openssl openssl-dev && \
    pip install warcprox==2.0 && \
    apk del build-base libffi-dev openssl-dev

EXPOSE 8888

VOLUME /output/warcs /db /ca

#ENTRYPOINT ["warcprox", "--address", "0.0.0.0", "--port", "8888"]

CMD warcprox -b 0.0.0.0 -d /output/warcs --base32 -z --rollover-idle-time 3600 2>&1 | tee /output/log

