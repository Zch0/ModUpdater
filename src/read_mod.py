import json
import os
import pathlib
import re
import zipfile
from typing import Any, Dict, Optional, List


def read_mod_config(mod_folder: str, mod_file_name: str) -> dict:
    mod_file_path = pathlib.Path(mod_folder) / mod_file_name
    with zipfile.ZipFile(mod_file_path, 'r') as jar:
        with jar.open("fabric.mod.json") as f:
            mod_config = json.load(f)
    return mod_config


def extract_mod_source_url(sourceURL_from: list[str], mod_config: dict) -> str | None:
    contact = mod_config.get("contact", {})
    for source in sourceURL_from:
        if source in contact:
            return contact[source]
    return None


def extract_mod_name(mod_config: dict) -> str | None:
    return mod_config.get("name", None)


def extract_mod_version(mod_config: dict) -> str | None:
    return mod_config.get("version", None)
