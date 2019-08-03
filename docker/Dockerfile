FROM debian:latest

RUN apt-get update && \
    apt-get upgrade --assume-yes && \
    apt-get install python3 python3-pip swig procps net-tools --assume-yes && \
    rm -rf /var/lib/apt/*

RUN pip3 install --upgrade pip && \
    pip3 install pytest python-ESL pydevd-pycharm~=192.5728.105 pytest-timeout pytest-cov

RUN mkdir -p /opt/src /opt/tests

VOLUME /opt/src
VOLUME /opt/tests

WORKDIR /opt