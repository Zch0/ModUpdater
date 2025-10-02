from modrinth_api_wrapper import Client
import os
import hashlib
from typing import Any, List


def get_file_sha1(filepath: str) -> str:
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()


def get_mod_current_version(mod_folder: str, mod_file: str) -> Any | None:
    client = Client()
    mod_path = os.path.join(mod_folder, mod_file)
    if not os.path.exists(mod_path):
        print(f"Mod file '{mod_file}' does not exist.")
        return None
    version_info = client.get_version_from_hash(sha1=get_file_sha1(mod_path))
    if not version_info:
        print(f"No version found for mod file '{mod_file}'.")
        return None
    return version_info


def get_mod_project_id(version_info: Any) -> str | None:
    if not version_info:
        return None
    return getattr(version_info, "project_id", None)


def get_mod_version_number(version_info: Any) -> str | None:
    if not version_info:
        return None
    return getattr(version_info, "version_number", None)


def get_mod_versions_by_id(project_id: str) -> list[Any]:
    client = Client()
    versions: List[Any] = []
    version_list: List[Any] = client.list_project_versions(project_id)
    for version in version_list:
        loaders = getattr(version, "loaders", [])
        if 'fabric' not in loaders:
            continue
        versions.append(version)
    return versions


def get_mod_latest_version(project_id: str, game_version: str) -> Any | None:
    versions = get_mod_versions_by_id(project_id)
    if not versions:
        return None
    for version in versions:
        if game_version in getattr(version, "game_versions", []):
            return version
    return None
