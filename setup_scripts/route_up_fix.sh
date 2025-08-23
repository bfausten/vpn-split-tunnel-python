#!/bin/bash

# We search for specific rules in iptables: if they are not found in the right position, then we add them
# We want to allow port 22 as ssh port in this case
# You may want to run this as a crontab to fix iptables regularly in case of other programs messing with them (e.g. VPNs)
# Use e.g. as route up script after connecting openvpn
# keep format (indentation, ...) fixed! 
# ssh_port 22 is used here

echo "Checking rules..."

# Check input connection
iptables -L --line-numbers | grep '1    ACCEPT     tcp  --  anywhere             anywhere             tcp dpt:22 ctstate NEW,ESTABLISHED'
if [ $? -ne 0 ]; then
    echo "Rule not found. Inserting it on top of the iptables..."
    iptables -I INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
else
    echo "Rule found."
fi

# Check output connection
iptables -L --line-numbers | grep '1    ACCEPT     tcp  --  anywhere             anywhere             tcp spt:22 ctstate ESTABLISHED'
if [ $? -ne 0 ]; then
    echo "Rule not found. Inserting it on top of the iptables..."
    iptables -I OUTPUT -p tcp --sport 22 -m conntrack --ctstate ESTABLISHED -j ACCEPT
else
    echo "Rule found."
fi

echo "Done!"
