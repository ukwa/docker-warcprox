FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y gcc make build-essential python python-dev python-gdbm curl git libffi-dev libssl-dev

RUN curl "https://bootstrap.pypa.io/get-pip.py" | python

RUN apt-get install strace

RUN pip install warcprox==2.0b1
#RUN pip install git+https://github.com/internetarchive/warcprox.git@2.x

EXPOSE 8000

RUN mkdir -p /output/warcs

CMD warcprox -b 0.0.0.0 -d /output/warcs --base32 -z --rollover-idle-time 3600 2>&1 | tee /output/log

