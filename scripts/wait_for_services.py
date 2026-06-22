import os
import time

import requests


def wait_for(url: str, name: str, retries: int = 60) -> None:
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=3)
            if response.status_code < 500:
                print(f"{name} is ready")
                return
        except requests.RequestException:
            pass
        print(f"Waiting for {name} ({attempt}/{retries})")
        time.sleep(2)
    raise TimeoutError(f"{name} did not become ready")


if __name__ == "__main__":
    wait_for(os.getenv("QDRANT_URL", "http://localhost:6333"), "Qdrant")
    wait_for(f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/tags", "Ollama")
