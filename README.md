# 项目介绍  
这是一个可以一键更新MinecraftMod的Python脚本，可以同版本、跨版本更新Mod，减少玩家的重复劳动。  

采用控制台操作，可兼容多种设备

目前仅支持从Modrinth上获取Mod，这意味着有部分未上架Modrinth的Mod无法更新，暂时请手动更新。


# 环境要求
- 开发使用Python 3.12版本，其他版本不保证运行
- 建议使用虚拟环境
- 建议在Linux下运行
# 运行方法
1. 安装依赖  
`pip3 install -r requirements.txt`  
**注意**：Windows用户需要额外安装`windows-curses`库
2. 运行主程序  
``python3 main.py``  
**使用时请注意修改配置文件**  

# TODO
1. 优化UI，完成设置页面
2. 添加多种更新Mod的来源可供选择  


