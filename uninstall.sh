#!/bin/bash

sudo systemctl stop cf_proxy_ping_aggregator.service
sudo systemctl disable cf_proxy_ping_aggregator.service
sudo rm /usr/lib/systemd/system/cf_proxy_ping_aggregator.service
sudo systemctl daemon-reload
sudo systemctl reset-failed
sudo rm -rf /var/log/cf_proxy_ping_aggregator