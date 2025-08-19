from src.tui import tui,input_module
import os
from src.generate_config import generate_config
if __name__ == "__main__":
    if not os.path.isfile("config.toml"):
        generate_config()
        input_module(None, "请输入原mod目录", "./mods")
    tui()
