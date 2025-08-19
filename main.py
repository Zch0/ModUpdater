import os
from pydoc import cli
import tomllib
from turtle import update
from unittest import loader
import download_from_github
import read_mod
from modrinth_api_wrapper import Client
with open("config.toml", "rb") as f:
    config = tomllib.load(f)
mod_folder: str = config.get("modFolder", "./mods")
sourceURL_from: list[str] = config.get("sourceURL_from", ["sources"])
update_from: str = config.get("update_from", "modrinth")
update_game_version_from: str | None = config.get("updateGameVersionFrom")
update_game_version_to: str | None = config.get("updateGameVersionTo")
def get_mod_versions(mod_name: str) -> dict | None:
    # 从modrinth获取mod信息
    version_list:list=client.list_project_versions(mod_name)
    if not version_list:
        print(f"No versions found for {mod_name}.")
        return None
    versions=dict()
    for version in version_list:
        loaders = version.loaders
        if 'fabric' not in loaders:continue
        # 只处理fabric加载器的版本
        version_number = version.version_number
        game_versions:list=version.game_versions
        files= version.files
        versions[version_number] = {
            "game_versions": game_versions,
            "files": files
        }
    return versions
if __name__ == "__main__":
    if not os.path.exists(mod_folder):
        print(f"Mod folder '{mod_folder}' does not exist.")
        quit()
    # for mod_file in os.listdir(mod_folder):
    #     if mod_file.endswith(".jar"):
    #         try:
    #             mod_config = read_mods.read_mod_config(mod_folder,mod_file)
    #             repo = read_mods.extract_mod_source_url(sourceURL_from,mod_config)
    #         except Exception as e:
    #             print(f"Error reading {mod_file}: {e}")
            
    #         if not repo:
    #             print(f"No source URL found for {mod_file}.")
    #             continue
    #         print(f"Mod: {mod_file}, source: {repo}")
    #         print(f"Github release:{download_from_github.get_releases_from_github(repo)}")
    if update_from.lower()=="modrinth":
        #Modrinth support
        client = Client()
        for mod_file in os.listdir(mod_folder):
            if mod_file.endswith(".jar"):
                try:
                    mod_config = read_mod.read_mod_config(mod_folder,mod_file)
                    mod_name = read_mod.extract_mod_name(mod_config)
                except Exception as e:
                    print(f"Error reading {mod_file}: {e}")
                
                if not mod_name:
                    print(f"No name found for {mod_file}.")
                    continue
                versions= get_mod_versions(mod_name)
                if not versions:
                    print(f"No versions found for {mod_name}.")
                    continue
                # print(f"Mod: {mod_file}, versions: {versions}")

                # 筛选支持指定版本的文件，并列出列表
                for version_number,version_detail in versions.items():
                    game_versions = version_detail["game_versions"]
                    if update_game_version_to not in game_versions:
                        # print(f"Version {version_number} of {mod_name} does not support {target_game_version}.")
                        continue
                    file_list = version_detail["files"]
                    files=dict()
                    for file in file_list:
                        filename = file.filename
                        download_url = file.url
                        dhash=file.hash
                        files[version_number]={
                            "filename":filename,
                            "download_url":download_url,
                            "hash":hash
                        }
                    
                        # Here you would implement the actual download logic



                break

