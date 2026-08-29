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
        "api_url": "https://generativelanguage.googleapis.com/v1beta",
        "model_path": "models/gemini-3.6-flash:generateContent",
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

    def chat(self, prompt: str, timeout: int = 30) -> AIResponse:
        ...


class GeminiProvider:

    def __init__(self, api_key: str, api_url: str, model_path: str = ""):
        self.api_key = api_key
        self.api_url = api_url
        self.model_path = model_path

    def chat(self, prompt: str, timeout: int = 30) -> AIResponse:
        import requests

        # Build full URL from base + model path
        full_url = f"{self.api_url}/{self.model_path}".rstrip("/")

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key,
        }
        data = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(full_url, headers=headers, json=data, timeout=timeout)
            if not response.ok:
                try:
                    err_json = response.json()
                    msg = err_json.get("error", {}).get("message", response.text)
                except Exception:
                    msg = response.text
                raise RuntimeError(f"Gemini API error ({response.status_code}): {msg}")
            output = response.json()
            text = output["candidates"][0]["content"]["parts"][0]["text"].strip()
            return AIResponse(text=text, provider="gemini")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Gemini API error: {e}")


class OpenAIProvider:

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, prompt: str, timeout: int = 30) -> AIResponse:
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
            response = requests.post(self.api_url, headers=headers, json=data, timeout=timeout)
            if not response.ok:
                try:
                    err_json = response.json()
                    msg = err_json.get("error", {}).get("message", response.text)
                except Exception:
                    msg = response.text
                raise RuntimeError(f"OpenAI API error ({response.status_code}): {msg}")
            output = response.json()
            text = output["choices"][0]["message"]["content"].strip()
            return AIResponse(text=text, provider="openai")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"OpenAI API error: {e}")


class AnthropicProvider:

    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, prompt: str, timeout: int = 30) -> AIResponse:
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
            response = requests.post(self.api_url, headers=headers, json=data, timeout=timeout)
            if not response.ok:
                try:
                    err_json = response.json()
                    msg = err_json.get("error", {}).get("message", response.text)
                except Exception:
                    msg = response.text
                raise RuntimeError(f"Anthropic API error ({response.status_code}): {msg}")
            output = response.json()
            text = output["content"][0]["text"].strip()
            return AIResponse(text=text, provider="anthropic")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
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


def dump_toml(data: dict) -> str:
    lines = []
    for k, v in data.items():
        if not isinstance(v, dict):
            lines.append(f'{k} = "{v}"')
    for section, table in data.items():
        if isinstance(table, dict):
            lines.append(f"\n[{section}]")
            for k, v in table.items():
                if isinstance(v, str):
                    val = v.replace("\\", "\\\\").replace('"', '\\"')
                    lines.append(f'{k} = "{val}"')
                elif isinstance(v, bool):
                    lines.append(f'{k} = {"true" if v else "false"}')
                elif isinstance(v, (int, float)):
                    lines.append(f"{k} = {v}")
    return "\n".join(lines).strip() + "\n"


def save_config(config: dict) -> None:
    ensure_config_dir()
    content = dump_toml(config)
    CONFIG_FILE.write_text(content, encoding="utf-8")
    CONFIG_FILE.chmod(0o600)


def get_provider(config: dict) -> Optional[AIProvider]:
    if "ai" not in config:
        return None

    ai_config = config["ai"]
    provider_name = ai_config.get("provider")
    api_key = ai_config.get("api_key")
    api_url = ai_config.get("api_url", "")

    if not provider_name or not api_key:
        return None

    if provider_name == "gemini":
        # Get model_path from defaults or config
        model_path = ai_config.get("model_path", PROVIDER_DEFAULTS["gemini"]["model_path"])
        return GeminiProvider(api_key, api_url, model_path)
    elif provider_name == "openai":
        return OpenAIProvider(api_key, api_url)
    elif provider_name == "anthropic":
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
            value = _password_input(prompt)
        else:
            value = input(prompt + ": ")

        value = value.strip()
        if value:
            return value
        if default:
            return default
        print("This field is required. Try again.")


def _password_input(prompt: str) -> str:
    """Get password input with visual dots feedback."""
    import sys
    print(prompt + ": ", end="", flush=True)
    sys.stdout.flush()

    # Read character by character and print dots
    chars = []
    import tty
    import termios

    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(sys.stdin)

        while True:
            ch = sys.stdin.read(1)
            if ch == '\n' or ch == '\r':
                print()  # New line after Enter
                break
            if ch == '\x03':  # Ctrl+C
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                raise KeyboardInterrupt
            if ch == '\x7f' or ch == '\b':  # Backspace
                if chars:
                    chars.pop()
                    # Erase last dot (go back, space, go back)
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            else:
                chars.append(ch)
                sys.stdout.write('*')
                sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return ''.join(chars)


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
        response = ai_provider.chat("Hello", timeout=8)
        print("Connection successful!")
    except Exception as e:
        error_msg = str(e)
        # Check for common issues
        if "401" in error_msg or "API key" in error_msg.lower():
            msg = "Invalid API key. Check your credentials and try again."
        elif "404" in error_msg:
            msg = "API endpoint not found. The service may have changed."
        elif "429" in error_msg:
            msg = "Rate limited. Wait a moment and retry."
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            msg = "Connection timed out. Check your internet connection."
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            msg = "Network error. Check your internet connection."
        else:
            msg = f"An error occurred: {error_msg[:100]}"

        print(f"[-] Connection failed: {msg}")

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
        model_path = PROVIDER_DEFAULTS["gemini"]["model_path"]
        return GeminiProvider(api_key, api_url, model_path)
    elif provider == "openai":
        return OpenAIProvider(api_key, api_url)
    elif provider == "anthropic":
        return AnthropicProvider(api_key, api_url)
    raise ValueError(f"Unknown provider: {provider}")