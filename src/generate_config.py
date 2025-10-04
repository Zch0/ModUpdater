import tomlkit


def generate_config():
    config=tomlkit.document()
    config["updateGameVersionFrom"]=tomlkit.item("").comment("源mod版本")
    config["updateGameVersionTo"]=tomlkit.item("").comment("目标mod版本")
    config["modFolderFrom"]=tomlkit.item("").comment("源mod目录")
    config["modFolderTo"]=tomlkit.item("").comment("目标mod目录")
    config["backupFolder"]=tomlkit.item("").comment("备份目录")
    config["cacheFolder"]=tomlkit.item("./.cache").comment("缓存目录")
    config["updateSource"]=tomlkit.item("Modrinth").comment("更新来源")
    config["maxRetries"]=tomlkit.item(5).comment("最大重试次数")
    with open("config.toml", "w") as f:
        tomlkit.dump(config,f)
