import tomli_w


def generate_config():
    config = {
        # 原mod版本
        "updateGameVersionFrom": "",
        # 新mod版本
        "updateGameVersionTo": "",
        # 原mod目录
        "modFolderFrom": "./mods",
        # 新mod目录
        "modFolderTo": "./newMods",
        # 备份目录
        "backupFolder": "./backup",
        # 缓存目录
        "cacheFolder": "./.cache",
        # 更新来源
        "updateSource": "Modrinth",
        # 最大重试次数
        "maxRetries": 5
    }
    tomli_w.dump(config, open("config.toml", "wb"))
