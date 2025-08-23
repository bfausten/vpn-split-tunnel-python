from __future__ import annotations
from download_images import download_image
import logging
import subprocess
import sys
import time
from pathlib import Path

def _run(script: Path) -> None:
    # run bash script
    if not script.exists():
        logging.error("script %s not found - aborting.", script)
        raise FileNotFoundError

    if not script.is_file():
        logging.error("there's sth wrong with %s", script)
        raise IsADirectoryError

    logging.info("running %s", script)
    try:
        subprocess.run(["sudo","-n", str(script)], check=True)
        logging.info("successfully ran %s", script)
    except subprocess.CalledProcessError as exc:
        logging.error("%s exited with code %s", script, exc.returncode)
        raise
    except KeyboardInterrupt:
        logging.info("interrupted by user")
        raise


def setup(setup_script: Path) -> None:
    # create routing table novpn, iptables marks and policy rule; after that the vpn tunnel can be established safely
    logging.info("setting up routing table and iptables rules")
    _run(setup_script)
    time.sleep(0.5)  # give it a moment to settle
    logging.info("successful")


def connect_vpn(config: Path, route_up_script: Path | None = None, setup_script: Path | None = None, first_use: bool = True, timeout: int = 30) -> None:
    """Connect to the VPN and block until OpenVPN is fully up."""
    if not config.exists():
        logging.error("vpn config file %s not found", config)
        raise FileNotFoundError

    if (first_use and not setup_script) or (first_use and not setup_script.exists()) or (not first_use and setup_script):
        logging.error("setup script not provided, although it's the first use OR first_use not set to True; careful!")
        raise FileNotFoundError

    log_file = Path("/absolute/path/to/logs/openvpn.log")
    try:
        # truncate old log if present so we don't match stale lines
        log_file.write_text("")
    except Exception:
        pass
    
    if first_use:
        if not setup_script or not setup_script.exists():
            logging.error("first_use=True but setup_script missing or not found")
            raise FileNotFoundError("setup_script required on first use")
    else:
        # Ignore any provided setup_script when switching VPNs
        setup_script = None

    # setup split-tunnelling ONLY IF FIRST USE (not when changing vpns)
    if first_use and setup_script:
        try:
            t0 = time.perf_counter()
            setup(setup_script)
            logging.info("setup took %.2f seconds", time.perf_counter() - t0)
        except Exception as e:
            logging.error("failed to setup: %s", e)
            raise

    # subprocess: run openvpn
    cmd = [
        "sudo", "-n", "openvpn",
        "--config", str(config),
        "--verb", "3",
        "--log", str(log_file),
    ]
    # we'll include a route script only if provided.
    if route_up_script and route_up_script.exists():
        cmd += ["--route-up", str(route_up_script)]

    logging.info("connecting to vpn with config %s", config)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    start = time.time()
    try:
        while time.time() - start <= timeout:
            # if OpenVPN died, fail fast with helpful log tail (80)
            if proc.poll() is not None:
                try:
                    tail = subprocess.check_output(["tail", "-n", "80", str(log_file)], text=True)
                except Exception:
                    tail = "<no log available>"
                logging.error("openvpn exited early. last log lines:\n%s", tail)
                raise RuntimeError("openvpn exited early")

            # success when OpenVPN says it's ready; wait for "Initialization Sequence Completed"
            try:
                log_tail = subprocess.check_output(["tail", "-n", "50", str(log_file)], text=True)
                if "Initialization Sequence Completed" in log_tail:
                    logging.info("vpn connection established in %.2f seconds", time.perf_counter() - start)
                    time.sleep(0.5)
                    return
            except Exception:
                pass
            time.sleep(0.5)

        # timeout
        logging.error("vpn connection timed out after %d seconds", timeout)
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass
        disconnect_vpn()
        raise TimeoutError(f"vpn connection timed out after {timeout} seconds")

    except KeyboardInterrupt:
        logging.info("interrupted by user")
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            pass
        raise


def disconnect_vpn(final_disconnect: bool = True, cleanup_script: Path | None = Path("/absolute/path/to/setup_scripts/clean_up_split_tunnel.sh")) -> None:
    # disconnect from the vpn via KILLALL (very drastic; maybe need's adjusting for only a single process)
    logging.info("disconnecting from vpn")
    try:
        subprocess.run(["sudo","-n","killall","-q","openvpn"], check=True)
    except subprocess.CalledProcessError as exc:
        logging.warning("no openvpn to kill (or failed): %s", exc.returncode)
        return
    # wait for tun0 to disappear
    start = time.time()
    while time.time() - start < 10:
        try:
            out = subprocess.check_output(["ip","route","show"], text=True)
            if "tun0" not in out or " dev tun" not in out or "tun" not in out: break
        except subprocess.CalledProcessError:
            break
    time.sleep(0.5)
    logging.info("successful")
    # cleanup after final disconnect
    if final_disconnect:
        t6 = time.perf_counter()
        delete_setup(cleanup_script)
        logging.info("cleanup took %.2f seconds", time.perf_counter() - t6)

def change_vpn(new_config: Path, route_up_script: Path) -> None:
    # change the vpn config file
    logging.info("changing vpn config to %s", new_config)
    if not new_config.exists():
        logging.error("new vpn config file %s not found", new_config)
        raise FileNotFoundError

    disconnect_vpn(final_disconnect=False)  # disconnect the current vpn, but don't delete setup
    time.sleep(1)  # give it a moment to settle
    connect_vpn(new_config, route_up_script, first_use=False)
    logging.info("successful")


def delete_setup(cleanup_script: Path) -> None:
    # remove table 200, iptables marks and policy rule; close vpn tunnel BEFORE running this!
    logging.info("deleting setup")
    _run(cleanup_script)
    logging.info("successful")
