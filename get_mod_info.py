import os

import hashlib
from sys import version

def get_file_sha1(filepath):
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()
#Modrinth
from modrinth_api_wrapper import Client


def get_mod_current_version(mod_folder,mod_file):
    client= Client()
    mod_path= os.path.join(mod_folder, mod_file)
    if not os.path.exists(mod_path):
        print(f"Mod file '{mod_file}' does not exist.")
        return None
    version_info=client.get_version_from_hash(sha1=get_file_sha1(mod_path))
    if not version_info:
        print(f"No version found for mod file '{mod_file}'.")
        return None
    return version_info
def get_mod_project_id(version_info):
    """
    获取modrinth的项目ID
    :param version_info: modrinth版本信息
    :return: 项目ID
    """
    if not version_info:
        return None
    return version_info.project_id
def get_mod_version_number(version_info):
    """
    获取modrinth的版本号
    :param version_info: modrinth版本信息
    :return: 版本号
    """
    if not version_info:
        return None
    return version_info.version_number
def get_mod_versions_by_id(project_id):
    client = Client()
    versions = []
    # 从modrinth获取mod信息
    version_list:list=client.list_project_versions(project_id)
    for version in version_list:
        loaders = version.loaders
        if 'fabric' not in loaders:continue
        # 只处理fabric加载器的版本
        versions.append(version)
    return versions

def get_mod_latest_version(project_id,game_version):
    versions = get_mod_versions_by_id(project_id)
    if not versions:
        return None
    for version in versions:
        if game_version in version.game_versions:
            return version
    return None