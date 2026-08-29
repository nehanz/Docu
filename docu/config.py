"""Configuration and AI provider management for docu."""

import os
import sys
from pathlib import Path
from typing import Optional, Protocol
from dataclasses import dataclass

try:
    import tomllib
except ImportError:
    import tomli as tomllib


# Provider defaults
PROVIDER_DEFAULTS = {
    "gemini": {
        "name": "Google Gemini",
        "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent",
        "api_key_hint": "AIza...",
    },
    "openai": {
        "name": "OpenAI GPT",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "api_key_hint": "sk-...",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "api_url": "https://api.anthropic.com/v1/messages",
        "api_key_hint": "sk-ant-api03-...",
    },
}


@dataclass
class AIResponse:
    text: str
    provider: str


class AIProvider(Protocol):

    def chat(self, prompt: str) -> AIResponse:
        ...


class GeminiProvider:

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, prompt: str) -> AIResponse:
        import requests

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key,
        }
        data = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            output = response.json()
            text = output["candidates"][0]["content"]["parts"][0]["text"].strip()
            return AIResponse(text=text, provider="gemini")
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")


class OpenAIProvider:

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, prompt: str) -> AIResponse:
        import requests

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            output = response.json()
            text = output["choices"][0]["message"]["content"].strip()
            return AIResponse(text=text, provider="openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


class AnthropicProvider:

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, prompt: str) -> AIResponse:
        import requests

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        data = {
            "model": "claude-sonnet-4-20250514",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            output = response.json()
            text = output["content"][0]["text"].strip()
            return AIResponse(text=text, provider="anthropic")
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")


# Config file paths
CONFIG_DIR = Path.home() / ".docu"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def ensure_config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}

    try:
        content = CONFIG_FILE.read_text(encoding="utf-8")
        return tomllib.loads(content)
    except Exception:
        return {}


def save_config(config: dict) -> None:
    import tomllib

    ensure_config_dir()
    content = tomllib.dumps(config)
    CONFIG_FILE.write_text(content, encoding="utf-8")
    CONFIG_FILE.chmod(0o600)


def get_provider(config: dict) -> Optional[AIProvider]:
    if "ai" not in config:
        return None

    ai_config = config["ai"]
    provider = ai_config.get("provider")
    api_key = ai_config.get("api_key")
    api_url = ai_config.get("api_url", "")

    if not provider or not api_key:
        return None

    if provider == "gemini":
        return GeminiProvider(api_key, api_url)
    elif provider == "openai":
        return OpenAIProvider(api_key, api_url)
    elif provider == "anthropic":
        return AnthropicProvider(api_key, api_url)

    return None


def is_configured(config: dict) -> bool:
    if "ai" not in config:
        return False
    ai = config["ai"]
    return bool(ai.get("provider") and ai.get("api_key"))


def prompt_choice(prompt_text: str, options: list[str], labels: list[str]) -> str:
    print(f"\n{prompt_text}")
    for i, (opt, label) in enumerate(zip(options, labels), 1):
        print(f"  {i}. {label}")

    while True:
        try:
            choice = input("\nEnter choice (1-{0}): ".format(len(options)))
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a number.")


def prompt_input(prompt_text: str, default: str = "", password: bool = False) -> str:
    prompt = prompt_text
    if default:
        prompt += f" [{default}]"

    while True:
        if password:
            import getpass
            value = getpass.getpass(prompt + ": ")
        else:
            value = input(prompt + ": ")

        value = value.strip()
        if value:
            return value
        if default:
            return default
        print("This field is required. Try again.")


def run_setup(interactive: bool = True) -> Optional[dict]:
    if not interactive:
        return None

    print("\n=== Docu AI Configuration ===\n")

    # Choose provider
    providers = list(PROVIDER_DEFAULTS.keys())
    labels = [PROVIDER_DEFAULTS[p]["name"] for p in providers]
    provider = prompt_choice("Choose AI provider:", providers, labels)

    info = PROVIDER_DEFAULTS[provider]
    api_url = info["api_url"]

    print(f"\n[{info['name']}]")
    print(f"API URL: {api_url}")
    print(f"API Key format: {info['api_key_hint']}")
    print()

    # Get API key with clear instructions
    print("Get your API key from:")
    if provider == "gemini":
        print("  -> https://aistudio.google.com/app/apikey")
    elif provider == "openai":
        print("  -> https://platform.openai.com/api-keys")
    elif provider == "anthropic":
        print("  -> https://console.anthropic.com/settings/keys")
    print()

    api_key = prompt_input("Paste your API key here", password=True)

    # Test connection
    print("\nTesting connection...")
    try:
        ai_provider = get_provider_from_config(provider, api_key, api_url)
        response = ai_provider.chat("Hello")
        print("[+] Connection successful!")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        print("\nTips:")
        print("  - Make sure your API key is correct")
        print("  - Check if the API service is available")
        print("  - Verify your account has access to the API")
        retry = input("\nRetry? (y/N): ").strip().lower()
        if retry == "y" or retry == "yes":
            return run_setup(True)
        print("Configuration saved but not verified.")

    # Save config
    config = load_config()
    config["ai"] = {
        "provider": provider,
        "api_url": api_url,
        "api_key": api_key,
    }
    save_config(config)
    print(f"\n[+] Configuration saved to {CONFIG_FILE}")
    print("Use 'docu askai' to talk to the AI assistant.")

    return config


def get_provider_from_config(provider: str, api_key: str, api_url: str) -> AIProvider:
    if provider == "gemini":
        return GeminiProvider(api_key, api_url)
    elif provider == "openai":
        return OpenAIProvider(api_key, api_url)
    elif provider == "anthropic":
        return AnthropicProvider(api_key, api_url)
    raise ValueError(f"Unknown provider: {provider}")