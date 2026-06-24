"""
Stability AI image generation utility (Stable Image Core, SDXL-based).
Usage: python image_gen.py "<prompt>" "<output_path>" [--negative "<negative_prompt>"] [--style "<style_preset>"] [--aspect "<aspect_ratio>"]
Requires: STABILITY_API_KEY in socialMedia/.env, pip install requests python-dotenv

style_preset (optional, enum): 3d-model, analog-film, anime, cinematic, comic-book, digital-art,
enhance, fantasy-art, isometric, line-art, low-poly, modeling-compound, neon-punk, origami,
photographic, pixel-art, tile-texture
"""

import sys
import os
import argparse
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def generate(prompt: str, output_path: str, negative_prompt: str = "", style_preset: str = "", aspect_ratio: str = "1:1") -> None:
    api_key = os.environ.get("STABILITY_API_KEY")
    if not api_key:
        print("Error: STABILITY_API_KEY not found.")
        print("Add it to socialMedia/.env:  STABILITY_API_KEY=sk-...")
        sys.exit(1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Generating image...")
    print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    if negative_prompt:
        print(f"Negative prompt: {negative_prompt[:80]}{'...' if len(negative_prompt) > 80 else ''}")
    if style_preset:
        print(f"Style preset: {style_preset}")

    data = {
        "prompt": prompt,
        "output_format": "png",
        "aspect_ratio": aspect_ratio,
    }
    if negative_prompt:
        data["negative_prompt"] = negative_prompt
    if style_preset:
        data["style_preset"] = style_preset

    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={
            "authorization": f"Bearer {api_key}",
            "accept": "image/*",
        },
        files={"none": ""},
        data=data,
        timeout=60,
    )

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        size_kb = len(response.content) // 1024
        print(f"Saved: {output_path} ({size_kb} KB)")
    else:
        print(f"Error {response.status_code}: {response.text}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("prompt")
    parser.add_argument("output_path")
    parser.add_argument("--negative", default="", dest="negative_prompt")
    parser.add_argument("--style", default="", dest="style_preset")
    parser.add_argument("--aspect", default="1:1", dest="aspect_ratio")

    if len(sys.argv) < 3:
        print("Usage: python image_gen.py \"<prompt>\" \"<output_path>\" [--negative \"...\"] [--style \"...\"] [--aspect \"1:1\"]")
        sys.exit(1)

    args = parser.parse_args()
    generate(args.prompt, args.output_path, args.negative_prompt, args.style_preset, args.aspect_ratio)
