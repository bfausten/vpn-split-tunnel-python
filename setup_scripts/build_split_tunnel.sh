#!/bin/bash

# inspo by another github repo
# Steps:
# 1. Create a new IP rule table to handle non-VPN traffic
# 2. Add an IP rule to lookup our no-VPN table for any packets marked with a specific netfilter mask
# 3. Add an IP route which directs all traffic in our no-VPN table to use your Ethernet interface instead of the tunnel
# 4. Add an iptables rule to mark all SSH traffic with our designated netfilter mask
# NOTE: these reset on reboot, run as a service to make the changes permanent

# USE THE FIRST TIME ONLY
# Make sure to have the following in rt_tables (only first time)
# echo "201 novpn" >> /etc/iproute2/rt_tables

# Parameters to change
DEVICE='xxx' # default non-VPN device adapter e.g. ens3
GATEWAY='xxx.xxx.xxx.xxx' # non-VPN gateway
SSH_PORT='xx' # ssh non-VPN port (e.g. 22)
TABLE='novpn' # table name we have created (e.g. novpn)
MARK='78' # mark for iptables to recognize ssh packages (e.g. 65)
PREF1='900' # preference for the SSH routing table
PREF2='901' # preference for the VPN main table (to eliminate ens3only table; not needed in general)

echo "Directing all traffic with mark in table ${TABLE} using the ${DEVICE} interface..."
ip rule show | grep -q "pref ${PREF1}.*fwmark ${MARK}.*lookup ${TABLE}" || \
    ip rule add pref ${PREF1} fwmark ${MARK} table ${TABLE}

# not needed in general
ip rule show | grep -q "pref ${PREF2}.*lookup main" || \
    ip rule add pref ${PREF2} lookup main

ip route replace default via ${GATEWAY} dev ${DEVICE} table ${TABLE}

echo "Flushing cache..."
ip route flush cache

# Include --wait if other programs are accessing the xtables lock
echo "Instructing firewall rule to mark all SSH traffic with the designated netfilter mask..."
iptables --wait -t mangle -A OUTPUT -p tcp --sport ${SSH_PORT} -j MARK --set-mark ${MARK}

# Add -I for the rule to be the first
echo "Adding firewall exception for port ${SSH_PORT}..."
iptables -I INPUT -p tcp --dport ${SSH_PORT} -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -I OUTPUT -p tcp --sport ${SSH_PORT} -m conntrack --ctstate ESTABLISHED -j ACCEPT

echo "Done!"
