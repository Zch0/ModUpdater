from .src.tui import tui
import os
from .src.generate_config import generate_config
if __name__ == "__main__":
    if not os.path.isfile("config.toml"):
        generate_config()
    tui()
