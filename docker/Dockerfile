FROM debian:stretch

RUN apt-get update && \
    apt-get upgrade --assume-yes && \
    apt-get install curl gnupg2 apt-transport-https lsb-release libicu57 --assume-yes && \
    curl http://download.tarantool.org/tarantool/1.10/gpgkey | apt-key add - && \
    echo "deb http://download.tarantool.org/tarantool/1.10/debian/ stretch main" \
        > /etc/apt/sources.list.d/tarantool_1_10.list && \
    echo "deb-src http://download.tarantool.org/tarantool/1.10/debian/ stretch main" \
        >> /etc/apt/sources.list.d/tarantool_1_10.list && \
    apt-get update && \
    apt-get install python3 python3-pip swig procps net-tools rabbitmq-server tarantool --assume-yes && \
    rm -rf /var/lib/apt/*

RUN python3 -m pip install --upgrade pip && \
    pip install pytest pytest_rabbitmq python-ESL pydevd-pycharm~=192.5728.105 pytest-timeout pytest-cov tarantool

RUN mkdir -p /opt/src /opt/tests

VOLUME /opt/src
VOLUME /opt/tests

WORKDIR /opt