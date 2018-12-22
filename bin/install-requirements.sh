#!/bin/bash
mkdir -p /run/lock

flock -x /run/lock/easy_install.lock\
    easy_install fresco pymysql pyyaml

flock -x /run/lock/gem.lock\
    gem install sass
