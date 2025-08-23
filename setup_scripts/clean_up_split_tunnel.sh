#!/bin/bash

# cleans up after use; deletes all changes made my build_split_tunnel.sh

set -euo pipefail

TABLE='novpn'
MARK='78'
PREF1='900'   # fwmark -> novpn
PREF2='901'   # lookup main ;not needed in general
SSH_PORT='xx' # e.g. 22

# Remove mangle MARK rules (both variants, just in case)
while iptables -w -t mangle -C OUTPUT -p tcp --sport ${SSH_PORT} -j MARK --set-mark "$MARK" 2>/dev/null; do
  iptables -w -t mangle -D OUTPUT -p tcp --sport ${SSH_PORT} -j MARK --set-mark "$MARK"
done
while iptables -w -t mangle -C OUTPUT -p tcp --dport ${SSH_PORT} -j MARK --set-mark "$MARK" 2>/dev/null; do
  iptables -w -t mangle -D OUTPUT -p tcp --dport ${SSH_PORT} -j MARK --set-mark "$MARK"
done

# Remove the filter-table SSH allows that setup added
while iptables -C INPUT  -p tcp --dport ${SSH_PORT} -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT 2>/dev/null; do
  iptables -D INPUT  -p tcp --dport ${SSH_PORT} -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
done
while iptables -C OUTPUT -p tcp --sport ${SSH_PORT} -m conntrack --ctstate ESTABLISHED -j ACCEPT 2>/dev/null; do
  iptables -D OUTPUT -p tcp --sport ${SSH_PORT} -m conntrack --ctstate ESTABLISHED -j ACCEPT
done

# Remove policy rules (try exact match first, then by pref)
ip rule del fwmark "$MARK" lookup "$TABLE" 2>/dev/null || true
ip rule del pref "$PREF1" 2>/dev/null || true
ip rule del pref "$PREF2" 2>/dev/null || true

# Flush the novpn table
ip route flush table "$TABLE" || true

echo "Cleanup done."
