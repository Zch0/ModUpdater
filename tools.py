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

logging.basicConfig(
    filename='modupdater.log',
    filemode='w',  # 每次运行时覆盖日志文件
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(message)s',
    encoding='utf-8'
)

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
                logging.error(f"Error reading {mod_file}: {e}", exc_info=True)
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
    # latest_versions: Dict[str, Any] = {}
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
            max_retries = config.get("maxRetries", 3)  # 从配置中获取最大重试次数
            retries = 0
            while True:
                try:
                    current_version, latest_version = await asyncio.to_thread(get_mod_by_mod_file, mod_folder=config["modFolder"], mod_file=mod[1]["file"])
                    mod_dict[mod[0]]["current_version"] = current_version
                    mod_dict[mod[0]]["latest_version"] = latest_version
                    # latest_versions[mod[0]] = latest_version
                    break  # 成功则退出循环
                except Exception as e:
                    if e.__class__.__name__ == "NotFoundException":
                        mod_dict[mod[0]]["latest_version"] = "Not Found"
                        logging.error(f"Mod {mod[0]} not found on Modrinth.")
                        break  # 直接跳过
                    else:
                        retries += 1
                        logging.error(f"Error fetching update for {mod[0]} (retry {retries}): {e}")
                        if retries >= max_retries:
                            break  # 达到最大重试次数才算失败
                        await asyncio.sleep(1)  # 等待后重试
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
                latest_ver = mod[1].get("latest_version", None)
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
                    stdscr.addstr(y, x, f" → {latest_ver}", curses.color_pair(2 if latest_ver != "Not Found" else 5))
                end_x = x
                if latest_ver and current_ver != latest_ver:
                    end_x += len(f" → {latest_ver}")
                if end_x >= w:
                    end_x = w - 1
                stdscr.addstr(y, end_x, ")", curses.color_pair(4))
            # 进度百分比
            total = len(mod_dict)
            finished = len([mod for mod in mod_dict.values() if mod.get("latest_version") is not None])
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
            elif key == ord('\n'):
                stdscr.nodelay(False)  # 恢复阻塞模式
                start_update(stdscr, mod_dict)
        time.sleep(0.01)  # 防止CPU占用过高
    stdscr.nodelay(False)  # 恢复阻塞模式

def start_update(stdscr, mod_dict) -> None:
    # 只显示有可用更新的mod
    update_mods = [
        (name, mod_dict[name], mod_dict[name].get("latest_version", None))
        for name in mod_dict
        if mod_dict[name].get("latest_version") and mod_dict[name].get("current_version") != mod_dict[name].get("latest_version") and mod_dict[name].get("latest_version") != "Not Found"
    ]
    if not update_mods:
        stdscr.clear()
        stdscr.addstr(0, 0, "没有可用更新的mod。按任意键返回...")
        stdscr.refresh()
        stdscr.getch()
        return
    pos = 0  # 当前页面起始下标
    checked = set()  # 选中的mod下标
    cursor = 0  # 当前页面内高亮光标位置
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        max_lines = h - 2
        total = len(update_mods)
        # 保证cursor在当前页
        if cursor < 0:
            cursor = 0
        if cursor >= min(max_lines, total-pos):
            cursor = min(max_lines-1, total-pos-1)
        visible_mods = update_mods[pos:pos+max_lines]
        stdscr.addstr(0, 0, "选择要更新的mod(空格选中/取消，回车开始更新，q返回):")
        for idx, (name, mod, latest_ver) in enumerate(visible_mods):
            checked_box = "[*]" if (pos + idx) in checked else "[ ]"
            prefix = f"{pos + idx + 1}. "
            left_paren = "("
            right_paren = ")"
            name_str = name
            old_ver = mod['current_version'] or mod['version']
            arrow = " → "
            new_ver = f"{latest_ver}"
            box_str = checked_box
            # 计算各部分宽度，防止超出
            width = 0
            def cut(s):
                nonlocal width
                out = ''
                for c in s:
                    w_c = get_display_length(c)
                    if width + w_c > w-1:
                        break
                    out += c
                    width += w_c
                return out
            cut_prefix = cut(prefix)
            cut_name = cut(name_str)
            cut_left = cut(left_paren)
            cut_old = cut(old_ver)
            cut_arrow = cut(arrow)
            cut_new = cut(new_ver)
            cut_right = cut(right_paren)
            cut_box = cut(' ' + box_str)
            y = idx + 1
            x = 0
            # 高亮行
            if idx == cursor:
                stdscr.addstr(y, x, cut_prefix + cut_name + cut_left + cut_old + cut_arrow + cut_new + cut_right + cut_box, curses.A_REVERSE)
                continue
            # 普通行
            stdscr.addstr(y, x, cut_prefix)
            x += get_display_length(cut_prefix)
            # 选中mod名为黄色
            if (pos + idx) in checked:
                stdscr.addstr(y, x, cut_name, curses.color_pair(5))
            else:
                stdscr.addstr(y, x, cut_name)
            x += get_display_length(cut_name)
            # 左括号白色
            stdscr.addstr(y, x, cut_left, curses.color_pair(4))
            x += get_display_length(cut_left)
            # 旧版本红色
            stdscr.addstr(y, x, cut_old, curses.color_pair(3))
            x += get_display_length(cut_old)
            # 箭头
            stdscr.addstr(y, x, cut_arrow)
            x += get_display_length(cut_arrow)
            # 新版本绿色
            stdscr.addstr(y, x, cut_new, curses.color_pair(2))
            x += get_display_length(cut_new)
            # 右括号白色
            stdscr.addstr(y, x, cut_right, curses.color_pair(4))
            x += get_display_length(cut_right)
            # 复选框
            stdscr.addstr(y, x, cut_box)
        stdscr.addstr(h-1, 0, f"共 {len(update_mods)} 个可更新mod，当前{pos+1}-{pos+len(visible_mods)}，上下键移动，空格选中，回车更新，q返回")
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord('q'), ord('Q')):
            break
        elif key == curses.KEY_UP:
            if cursor > 0:
                cursor -= 1
            elif pos > 0:
                pos -= 1
        elif key == curses.KEY_DOWN:
            if cursor < len(visible_mods) - 1:
                cursor += 1
            elif pos + max_lines < total:
                pos += 1
        elif key == ord(' '):
            highlight_idx = pos + cursor
            if highlight_idx < total:
                if highlight_idx in checked:
                    checked.remove(highlight_idx)
                else:
                    checked.add(highlight_idx)
        elif key == ord('\n'):
            selected_mods = [update_mods[i] for i in checked if i < len(update_mods)]
            stdscr.clear()
            stdscr.addstr(0, 0, f"即将更新 {len(selected_mods)} 个mod，按任意键返回...")
            stdscr.refresh()
            stdscr.getch()
            break