import argparse
import getpass
import re
import sys
import time
from urllib.parse import urlparse, urlunparse

import requests

DEFAULT_TIMEOUT = 10
DEFAULT_MAX_TOKENS = 64

THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_think_tags(text):
    if not text:
        return text, False
    had_think = bool(THINK_TAG_RE.search(text))
    stripped = THINK_TAG_RE.sub("", text).strip()
    return stripped, had_think


def normalize_base_url(raw_url):
    raw_url = raw_url.strip()
    if "://" not in raw_url:
        raw_url = "http://" + raw_url

    parsed = urlparse(raw_url)
    path = parsed.path.rstrip("/")

    if not path:
        path = "/v1"
    elif not any(seg.startswith("v") and seg[1:].isdigit() for seg in path.split("/") if seg):
        path = path + "/v1"

    normalized = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
    return normalized


def try_request(url: str, headers: dict, timeout=DEFAULT_TIMEOUT):
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        return resp, None
    except requests.exceptions.ConnectionError as e:
        return None, f"Connection error: {e}"
    except requests.exceptions.Timeout:
        return None, "Request timed out."
    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {e}"


def requires_auth(status_code: int) -> bool:
    return status_code in (401, 403)


def get_api_key_if_needed(base_url):
    models_url = f"{base_url}/models"
    print(f"Probing {models_url} (no credentials) ...")

    resp, err = try_request(models_url, headers={})
    if err:
        print(f"  Could not reach endpoint without auth check: {err}")
        print("  Will still ask in case a key is needed, press Enter to skip.")
        key = getpass.getpass("  Enter API key (leave blank to skip): ").strip()
        return key or None

    if resp.status_code == 200:
        print("  No authentication required. Skipping API key prompt.")
        return None

    if requires_auth(resp.status_code):
        print(f"  Server responded with {resp.status_code}: authentication appears required.")
        key = getpass.getpass("  Enter API key: ").strip()
        return key or None

    print(f"  Unexpected status {resp.status_code} on unauthenticated probe; "
          f"will still try without a key.")
    return None


def list_models(base_url, api_key):
    models_url = f"{base_url}/models"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    resp, err = try_request(models_url, headers=headers)
    if err:
        print(f"Could not list models: {err}")
        return []

    if resp.status_code != 200:
        print(f"Model listing failed with status {resp.status_code}: {resp.text[:300]}")
        return []

    try:
        data = resp.json()
    except ValueError:
        print("Model listing endpoint did not return valid JSON.")
        return []

    models = [m.get("id") for m in data.get("data", []) if m.get("id")]
    if models:
        print(f"Found {len(models)} model(s):")
        for m in models:
            print(f"  - {m}")
    else:
        print("No models returned by the endpoint (or unexpected response shape).")
    return models


def check_liveness(base_url, api_key, model,
                    timeout=DEFAULT_TIMEOUT, max_tokens=DEFAULT_MAX_TOKENS):
    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": max_tokens,
    }

    print(f"\nChecking liveness of model '{model}' at {url} ...")
    start = time.monotonic()
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError as e:
        print(f"  Liveness check failed: connection error: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"  Liveness check failed: request timed out after {timeout}s.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  Liveness check failed: {e}")
        return False
    elapsed = time.monotonic() - start

    if resp.status_code == 200:
        try:
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            raw_content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason", "unknown")
        except (ValueError, IndexError, KeyError):
            raw_content = "<unparseable response body>"
            finish_reason = "unknown"

        stripped_content, had_think = strip_think_tags(raw_content)

        print(f"  Model is responsive. Latency: {elapsed:.2f}s")
        print(f"  Finish reason: {finish_reason}")

        if had_think:
            print("  Note: response included a <think> reasoning block (stripped below).")

        if stripped_content:
            print(f"  Sample reply: {stripped_content!r}")
        elif had_think:
            print(f"  Sample reply: <empty after stripping think block; "
                  f"try --max-tokens higher than {max_tokens} to see the actual answer>")
        else:
            print(f"  Sample reply: {raw_content!r}")

        return True
    else:
        print(f"  Model did not respond successfully. Status: {resp.status_code}")
        print(f"  Body: {resp.text[:300]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Probe an OpenAI-compatible endpoint.")
    parser.add_argument("--url", help="Base URL of the OpenAI-compatible API.")
    parser.add_argument("--key", help="API key, if known. If omitted, will auto-detect/prompt.")
    parser.add_argument("--model", help="Model id to use for the liveness check. "
                                         "If omitted, the first discovered model is used.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                         help="Request timeout in seconds (default: 10).")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                         help=f"Max tokens for the liveness check reply "
                              f"(default: {DEFAULT_MAX_TOKENS}). Raise this for "
                              f"reasoning models that emit <think> blocks before "
                              f"their answer.")
    args = parser.parse_args()

    raw_url = args.url or input("Enter the OpenAI-compatible base URL: ").strip()
    if not raw_url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    base_url = normalize_base_url(raw_url)
    print(f"Normalized base URL: {base_url}\n")

    api_key = args.key if args.key else get_api_key_if_needed(base_url)

    print()
    models = list_models(base_url, api_key)

    model_to_test = args.model or (models[0] if models else None)
    if not model_to_test:
        model_to_test = input("\nNo model discovered. Enter a model id to test "
                               "(or leave blank to skip liveness check): ").strip()

    if model_to_test:
        check_liveness(base_url, api_key, model_to_test,
                        timeout=args.timeout, max_tokens=args.max_tokens)
    else:
        print("\nSkipping liveness check: no model id available.")

    print("\nDone.")


if __name__ == "__main__":
    main()