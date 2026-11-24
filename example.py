"""
TrafficEye example: recognize license plates and vehicles in images.

Usage:
    python example.py                      # analyze the bundled example images
    python example.py photo.jpg            # analyze your own image
    python example.py https://.../car.jpg  # analyze an image from a URL
    python example.py --json               # print the full JSON response
"""
import argparse
import json
import os
import sys
from pathlib import Path

from trafficeye import TrafficEyeClient, TrafficEyeError

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # .env support is optional; plain environment variables still work

EXAMPLES_DIR = Path(__file__).parent / "images"
DEFAULT_IMAGES = [str(EXAMPLES_DIR / "example_image_01.jpg"), str(EXAMPLES_DIR / "example_image_02.jpg")]


def value(node: dict, key: str) -> str:
    """Read the 'value' of a result field such as mmr["make"], or '-' if missing."""
    return (node.get(key) or {}).get("value", "-")


def print_summary(result: dict) -> None:
    combinations = result.get("data", {}).get("combinations", [])
    road_users = [ru for combo in combinations for ru in combo.get("roadUsers", [])]
    if not road_users:
        print("  No vehicles found.")
        return

    for number, road_user in enumerate(road_users, start=1):
        mmr = road_user.get("mmr", {})
        plates = ", ".join(value(plate, "text") for plate in road_user.get("plates", [])) or "-"
        print(
            f"  Vehicle {number}: plate={plates} | "
            f"{value(mmr, 'make')} {value(mmr, 'model')} | "
            f"color={value(mmr, 'color')} | category={value(mmr, 'category')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="TrafficEye API example")
    parser.add_argument("images", nargs="*", default=DEFAULT_IMAGES, help="image paths or URLs")
    parser.add_argument("--json", action="store_true", help="print the full JSON response")
    args = parser.parse_args()

    api_key = os.environ.get("TRAFFICEYE_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        print("Missing API key. Get one at https://trafficeye.ai/user/licenses")
        print("then set it in .env (see .env.example) or run: export TRAFFICEYE_API_KEY=...")
        return 1

    client = TrafficEyeClient(api_key)

    try:
        print("Account info:", json.dumps(client.info()))
        for image in args.images:
            print(f"\n{image}")
            result = client.recognition(image)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print_summary(result)
    except TrafficEyeError as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
