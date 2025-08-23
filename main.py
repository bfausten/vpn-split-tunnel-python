import logging
from pathlib import Path
from vpn_methods import connect_vpn, disconnect_vpn, change_vpn
from download_images import download_image
import time

# just a demonstration of a possible use case

# bash scripts to create and delete the routing table and iptables rules
CREATE_SCRIPT = Path("/absolute/path/to/setup_scripts/build_split_tunnel.sh")   # add rules / table
FIX_TABLES = Path("/absolute/path/to/setup_scripts/route_up_fix.sh")
DELETE_SCRIPT = Path("/absolute/path/to/setup_scripts/clean_up_split_tunnel.sh")   # remove them
VPN_PATH_1 = Path("absolute/path/to/config_file_1.ovpn") # path to an openvpn config file 
VPN_PATH_2 = Path("absolute/path/to/config_file_2.ovpn") # path to an openvpn config file 
IMAGE_PATH_1 = "image1.com"
IMAGE_PATH_2 = "image2.com"
logging.info("")


def main() -> None:
    # run the full workflow, always cleaning up at the end
    logging.info("starting main workflow at %s", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    t0 = time.perf_counter()
    try:
        # setup routing table and iptables rules and connect to the first vpn
        connect_vpn(VPN_PATH_1, FIX_TABLES, setup_script=CREATE_SCRIPT, first_use=True)
        logging.info("connected to vpn in %.2f seconds", time.perf_counter() - t0)

        # download the first image
        t2 = time.perf_counter()
        download_image(IMAGE_PATH_1, "downloads", n=1)
        logging.info("downloaded image 1 in %.2f seconds", time.perf_counter() - t2)

        # change vpn
        t3 = time.perf_counter()
        change_vpn(VPN_PATH_2, FIX_TABLES)
        logging.info("changed vpn in %.2f seconds", time.perf_counter() - t3)

        # download the second image
        t4 = time.perf_counter()
        download_image(IMAGE_PATH_2, "downloads", n=2)
        logging.info("downloaded image 2 in %.2f seconds", time.perf_counter() - t4)

    finally:
        # disconnect the vpn and clean up
        t5 = time.perf_counter()
        disconnect_vpn(final_disconnect=True, cleanup_script=DELETE_SCRIPT)
        logging.info("disconnected from vpn and cleanup took %.2f seconds", time.perf_counter() - t5)
        logging.info("total runtime: %.2f seconds", time.perf_counter() - t0)


if __name__ == "__main__":
    main()
