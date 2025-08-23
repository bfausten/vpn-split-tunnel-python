# vpn-split-tunnel-python
## Connect a server to a VPN while keeping SSH off the VPN (split tunneling). Python + Bash.
### How it works
- `iptables -t mangle` marks SSH reply packets (e.g., MARK 78).
- `ip rule` sends marked packets to a policy table `novpn` with `default via <gateway> dev <nic>`.
- A higher-priority rule (`pref 901 lookup main`) ensures everything else follows the main table, which OpenVPN sets to the VPN.
- Python starts OpenVPN, appends logs to `logs/run.log`, and waits for _Initialization Sequence Completed_.
### Prerequisites
- Install openvpn and various requirements
```bash
sudo apt-get update && sudo apt-get install -y openvpn iproute2 iptables curl tcpdump
```
- Your provider (e.g. protonvpn) .ovpn with: `auth-user-pass /path/to/openvpn_credentials.txt` and write `script-security 2` somewhere in the .ovpn files
- Do _not_ add `route-nopull` or `pull-filter ignore redirect-gateway` (we want full tunnel).
- make scripts executable via `chmod +x setup_scripts/*.sh`
- Run as root, or configure passwordless sudo for openvpn, ip, iptables.
### Quick Start
- Without Python run
```bash
sudo ./setup_scripts/build_split_tunnel.sh
sudo openvpn --config ./openvpn_files/config_file.ovpn --route-up ./setup_scripts/route_up_fix.sh
```
- to kill the connection run *in that order*
```bash
sudo killall openvpn
sudo ./setup_scripts/clean_up_split_tunnel.sh
```
- If you're connecting to the VPN for the first time (in your current workflow, not only overall) with Python, run
```python
connect_vpn(config_path, route_up_path, set_up_path, first_use=True)
```
- To disconnect, run:
```python
disconnect_vpn(final_disconnect=True, clean_up_path)
```
- To change VPN connections, run
```python
change_vpn(new_config_path, route_up_path)
```
- Only set `final_disconnect=False` if you don't plan on cleanup afterwards (e.g. if you're connecting to another VPN in the near future)
- Only set `first_use=False` if you were already connected to a VPN before and *haven't* used `clean_up_script.sh`. `split-tunnel.sh` has to be active still! Otherwise the ssh-connection will freeze.
### Verification
- You can check whether the VPN is connected and the split-tunnel is working correctly, use
  - `ip route show`
  - `ip rule show`
  - `curl ifconfig.io` before and after connecting.
