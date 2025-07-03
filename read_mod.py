import json
import os
import pathlib
import re

import zipfile



def read_mod_config(mod_folder,mod_file_name):
    mod_file_path=pathlib.Path(mod_folder)/mod_file_name
    with zipfile.ZipFile(mod_file_path, 'r') as jar:
        with jar.open("fabric.mod.json") as f:
            mod_config = json.load(f)
    return mod_config

def extract_mod_source_url(sourceURL_from,mod_config):
    contact=mod_config.get("contact", {})
    for source in sourceURL_from:
        if source in contact:
            return contact[source]
    else:
        return None

def extract_mod_name(mod_config):
    return mod_config.get("name", None)

def extract_mod_version(mod_config):
    return mod_config.get("version", None)
