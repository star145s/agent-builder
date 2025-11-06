import time
import requests
import argparse
import bittensor as bt


API_URL = "https://star145s-agent-score-backup.hf.space/weights/array"


def fetch_weights():
    """
    Fetch weights array from remote API.
    Returns (weights, num_uids).
    """
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        weights = data.get("weights", [])
        num_uids = data.get("num_uids", len(weights))
        if not weights:
            raise ValueError("Empty weights received.")
        return weights, num_uids
    except Exception as e:
        print(f"[{time.strftime('%X')}] Error fetching weights: {e}")
        return None, None


def set_weights_onchain(netuid: int, wallet: bt.Wallet, weights):
    """
    Submit the weights to the Bittensor network.
    """
    subtensor = bt.Subtensor(network="finney")

    uids = list(range(len(weights)))
    weights = [float(w) for w in weights]

    ok, err = subtensor.set_weights(
        netuid=netuid,
        uids=uids,
        weights=weights,
        wallet=wallet,
        wait_for_inclusion=True,
        wait_for_finalization=False
    )

    if not ok:
        print(f"[{time.strftime('%X')}] ❌ Error setting weights: {err}")
    else:
        print(f"[{time.strftime('%X')}] ✅ Weights set successfully on subnet {netuid}")


def validator_loop(interval_secs: float, netuid: int, wallet: bt.Wallet):
    """
    Loop to continuously fetch and set weights every `interval_secs` seconds.
    """
    subtensor = bt.Subtensor(network="finney")
    try:
        while True:
            try:
                weights, num_uids = fetch_weights()
                if weights:
                    print(f"[{time.strftime('%X')}] Fetched {len(weights)} weights (sum={sum(weights):.6f})")
                    set_weights_onchain(netuid, wallet, weights)
                else:
                    print(f"[{time.strftime('%X')}] Skipping weight set due to fetch error.")
            except Exception as e:
                print(f"[{time.strftime('%X')}] Error in validator loop: {e}")
            subtensor.wait_for_block()  # wait for next block to avoid rate limit
            time.sleep(interval_secs)
    except KeyboardInterrupt:
        print("Loop stopped by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validator auto weight setter for Bittensor.")
    parser.add_argument("--wallet", type=str, required=True, help="Wallet name (coldkey name)")
    parser.add_argument("--hotkey", type=str, required=True, help="Hotkey name")
    parser.add_argument("--netuid", type=int, default=80, help="Subnet netuid (default: 80)")
    parser.add_argument("--interval", type=float, default=30.0, help="Interval between updates (seconds)")
    args = parser.parse_args()

    wallet = bt.Wallet(name=args.wallet, hotkey=args.hotkey)

    print(f"Starting validator weight loop on subnet {args.netuid} using wallet={args.wallet}/{args.hotkey}")
    validator_loop(args.interval, args.netuid, wallet)
