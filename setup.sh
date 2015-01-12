#!/bin/bash
mkdir /tmp/meDBsetup
wget -P /tmp/meDBsetup "http://apache.lauf-forum.at/kafka/0.8.1.1/kafka_2.10-0.8.1.1.tgz"
tar -zxvf "/tmp/meDBsetup/kafka_2.10-0.8.1.1.tgz" -C /tmp/meDBsetup
mkdir ./bin
mkdir ./bin/jar
find /tmp/meDBsetup/kafka_2.10-0.8.1.1/libs/ -iname "*.jar" -exec mv {} ./bin/jar \;
rm -rf /tmp/meDBsetup
