#!/usr/bin/env python3
"""
encrypt.py

Simple CLI tool to encrypt (sign) a message using a Bittensor wallet's coldkey.
It wraps the provided `generate` function and offers a command-line interface.

Usage:
    python encrypt.py --name alice --api-url https://api.example.com --token mytoken123 --wallet-password secret --output signed.txt

Notes:
- This script expects the `bittensor` Python package to be installed and a valid wallet name.
- The wallet password is stored to the environment using `wallet.coldkey_file.save_password_to_env()` as in the original snippet, then the coldkey is unlocked and used for signing.
- The output file (if provided) will contain the message, signer address, and signature (hex).

"""
from datetime import datetime
import argparse
import getpass
import logging
import os
import sys

import bittensor


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def generate(name: str, api_url: str, token: str, wallet_password: str) -> str:
    """
    Create a signed message string using the wallet's coldkey.

    Returns the file contents (message + signer + signature hex).
    """
    message = api_url + "<seperate>" + token

    # initialize wallet
    wallet = bittensor.wallet(name=name)

    # store password and unlock
    wallet.coldkey_file.save_password_to_env(wallet_password)
    try:
        wallet.unlock_coldkey()
    except Exception as e:
        logger.error("Failed to unlock coldkey: %s", e)
        raise

    keypair = wallet.coldkey

    timestamp = datetime.now()
    timezone = timestamp.astimezone().tzname()

    # sign data (use raw bytes of the message)
    signature = keypair.sign(data=message)

    file_contents = (
        f"{message}\n"
        f"\tSigned by: {keypair.ss58_address}\n"
        f"\tSignature: {signature.hex()}\n"
        f"\tTimestamp: {timestamp.isoformat()} ({timezone})\n"
    )
    return file_contents


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sign a message (api_url + token) with a Bittensor wallet coldkey.")
    parser.add_argument("--name", required=True, help="Wallet name (as used by bittensor.wallet(name=...)).")
    parser.add_argument("--api-url", required=True, help="API URL to include in the message.")
    parser.add_argument("--token", required=True, help="Token to include in the message.")
    parser.add_argument("--wallet-password", help="Wallet password. If omitted, you'll be prompted securely.")
    parser.add_argument("--output", help="If provided, write signed contents to this file. Otherwise prints to stdout.")

    args = parser.parse_args(argv)

    wallet_password = args.wallet_password
    if not wallet_password:
        # securely prompt for the wallet password
        wallet_password = getpass.getpass(prompt="Wallet password: ")

    try:
        signed = generate(name=args.name, api_url=args.api_url, token=args.token, wallet_password=wallet_password)
    except Exception as e:
        logger.error("Signing failed: %s", e)
        sys.exit(2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(signed)
            logger.info("Signed message written to: %s", os.path.abspath(args.output))
        except Exception as e:
            logger.error("Failed to write output file: %s", e)
            sys.exit(3)
    else:
        # print to stdout
        print(signed)


if __name__ == "__main__":
    main()
