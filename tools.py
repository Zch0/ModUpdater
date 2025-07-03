import logging
import os
import tomllib
import tomli_w  # 用于写入TOML文件
import get_mod_info
import read_mod
import curses
import unicodedata
import asyncio
from typing import Dict, Any, Callable

with open("config.toml", "rb") as f:
    config: dict = tomllib.load(f)

def exit_gui() -> None:
    raise SystemExit

def get_mod_dict(mod_folder: str) -> Dict[str, dict]:
    mod_dict: Dict[str, dict] = {}
    for mod_file in os.listdir(mod_folder):
        if mod_file.endswith(".jar"):
            try:
                mod_config = read_mod.read_mod_config(mod_folder, mod_file)
                mod_name = read_mod.extract_mod_name(mod_config)
                mod_version = read_mod.extract_mod_version(mod_config)
                if mod_name:
                    mod_dict[mod_name] = {
                        "version": mod_version,
                        "file": mod_file
                    }
            except Exception as e:
                print(f"Error reading {mod_file}: {e}")
    return mod_dict

def get_display_length(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in s)

def display_mod_list(stdscr: Any) -> None:
    mod_dict = get_mod_dict(config.get("modFolder", "./mods"))
    mod_list = list(mod_dict.items())
    from tools import get_display_length
    pos = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        if not mod_dict:
            stdscr.addstr(0, 0, "没有找到任何mod。")
            stdscr.addstr(1, 0, "按q返回主菜单...")
        else:
            stdscr.addstr(0, 0, "Mod列表(上下键翻页，q返回):")
            max_lines = h - 2
            visible_mods = mod_list[pos:pos+max_lines]
            for idx, mod in enumerate(visible_mods):
                display_str = f"{pos + idx + 1}. {mod[0]} ({mod[1]['version']})"
                cut_str = ''
                width = 0
                for c in display_str:
                    w_c = get_display_length(c)
                    if width + w_c > w-1:
                        break
                    cut_str += c
                    width += w_c
                stdscr.addstr(idx + 1, 0, cut_str)
            stdscr.addstr(h-1, 0, f"共 {len(mod_list)} 个mod，当前{pos+1}-{pos+len(visible_mods)}，上下键翻页，q返回")
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        elif key == curses.KEY_UP:
            if pos > 0:
                pos -= 1
        elif key == curses.KEY_DOWN:
            if pos + max_lines < len(mod_list):
                pos += 1

def set_update_source(platform: str, stdscr: Any) -> None:
    config["update_from"] = platform
    with open("config.toml", "wb") as f:
        tomli_w.dump(config, f)
    stdscr.addstr(0, 0, f"更新来源已设置为{platform}。按任意键返回...")
    stdscr.refresh()
    stdscr.getch()

def set_mod_directory(stdscr: Any, prompt: str = "请输入mods目录路径") -> str:
    while True:
        curses.echo()
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        default_path = config.get("modFolder", "./mods")
        prompt_full = f"{prompt} (当前: {default_path}，直接回车使用)"
        stdscr.addstr(h // 2 - 1, w // 2 - len(prompt_full) // 2, prompt_full)
        stdscr.refresh()
        stdscr.move(h // 2, w // 2 - 20)
        path = stdscr.getstr(h // 2, w // 2 - 20, 40).decode('utf-8').strip()
        curses.noecho()
        if not path:
            path = default_path
        if os.path.isdir(path):
            config["modFolder"] = path
            with open("config.toml", "wb") as f:
                tomli_w.dump(config, f)
            stdscr.addstr(h // 2 + 2, w // 2 - 10, f"已设置: {path}")
            stdscr.refresh()
            stdscr.getch()
            return path
        else:
            stdscr.addstr(h // 2 + 2, w // 2 - 12, f"目录不存在: {path}")
            stdscr.addstr(h // 2 + 3, w // 2 - 12, "按任意键重新输入...")
            stdscr.refresh()
            stdscr.getch()

import threading
import time
import curses

def check_update(stdscr: Any) -> None:
    mod_dict = get_mod_dict(config.get("modFolder", "./mods"))
    latest_versions: Dict[str, Any] = {}
    update_done = threading.Event()

    def fetch_all_latest() -> None:
        def get_mod_by_mod_file(mod_folder: str, mod_file: str) -> tuple[str, str]:
            current_version = get_mod_info.get_mod_current_version(mod_folder, mod_file)
            current_version_number = get_mod_info.get_mod_version_number(current_version) or "?"
            project_id = get_mod_info.get_mod_project_id(current_version)
            if not project_id:return current_version_number, "?"
            latest_version = get_mod_info.get_mod_latest_version(project_id, config["current_version"])
            latest_version_number = get_mod_info.get_mod_version_number(latest_version) or "?"
            return current_version_number, latest_version_number
        async def fetch_and_update(mod: tuple[str, dict]) -> None:
            try:
                current_ver, latest_ver = await asyncio.to_thread(get_mod_by_mod_file, mod_folder=config["modFolder"], mod_file=mod[1]["file"])
                mod_dict[mod[0]]["current_version"] = current_ver
                latest_versions[mod[0]] = latest_ver
            except Exception:
                latest_versions[mod[0]] = None
        async def main_async() -> None:
            tasks = [fetch_and_update(mod) for mod in mod_dict.items()]
            await asyncio.gather(*tasks)
            update_done.set()
        asyncio.run(main_async())

    threading.Thread(target=fetch_all_latest, daemon=True).start()
    pos = 0
    stdscr.nodelay(True)  # 设置非阻塞
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        if not mod_dict:
            stdscr.addstr(0, 0, "没有找到任何mod。")
            stdscr.addstr(1, 0, "按q返回主菜单...")
        else:
            stdscr.addstr(0, 0, "Mod更新检查(上下键翻页，q返回):")
            max_lines = h - 2
            visible_mods = list(mod_dict.items())[pos:pos+max_lines]
            for idx, mod in enumerate(visible_mods):
                name = mod[0]
                local_ver = mod[1]["version"]
                current_ver = mod[1].get("current_version", local_ver)
                latest_ver = latest_versions.get(name)
                y = idx + 1
                display_str = f"{pos + idx + 1}. {name} ("
                stdscr.addstr(y, 0, display_str)
                x = len(display_str)
                if latest_ver is None:
                    stdscr.addstr(y, x, current_ver, curses.color_pair(4))
                    x += len(current_ver)
                elif current_ver == latest_ver:
                    stdscr.addstr(y, x, current_ver, curses.color_pair(2))
                    x += len(current_ver)
                else:
                    stdscr.addstr(y, x, current_ver, curses.color_pair(3))
                    x += len(current_ver)
                    stdscr.addstr(y, x, f" → {latest_ver}", curses.color_pair(2))
                end_x = x
                if latest_ver and current_ver != latest_ver:
                    end_x += len(f" → {latest_ver}")
                if end_x >= w:
                    end_x = w - 1
                stdscr.addstr(y, end_x, ")", curses.color_pair(4))
            # 进度百分比
            total = len(mod_dict)
            finished = len(latest_versions)
            percent = int(finished / total * 100) if total else 100
            stdscr.addstr(h-1, 0, f"共 {total} 个mod，当前{pos+1}-{pos+len(visible_mods)}，上下键翻页，q返回   进度：{percent}%")
        stdscr.refresh()
        key = stdscr.getch()
        if key != -1:
            if key in (ord('q'), ord('Q')):
                break
            elif key == curses.KEY_UP:
                if pos > 0:
                    pos -= 1
            elif key == curses.KEY_DOWN:
                if pos + max_lines < len(mod_dict):
                    pos += 1
        time.sleep(0.05)  # 防止CPU占用过高
    stdscr.nodelay(False)  # 恢复阻塞模式