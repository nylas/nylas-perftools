#!/bin/sh

if ! influxdb_installed=$(dpkg -s influxdb); then
    wget http://influxdb.s3.amazonaws.com/influxdb_0.9.2_amd64.deb
    dpkg -i influxdb_0.9.2_amd64.deb
    rm influxdb_0.9.2_amd64.deb
fi


