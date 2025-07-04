import logging
import os
from pathlib import Path
import tomllib
import urllib.request
import tomli_w
import urllib  # 用于写入TOML文件
import get_mod_info
import read_mod
import curses
import unicodedata
import asyncio
from typing import Dict, Any, Callable

logging.basicConfig(
    filename='modupdater.log',
    filemode='w',  # 每次运行时覆盖日志文件
    level=logging.INFO,
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
                        "local_version_number": mod_version,
                        "local_filename": mod_file
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
                display_str = f"{pos + idx + 1}. {mod[0]} ({mod[1]['local_version_number']})"
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

def check_update(stdscr: Any) -> None:
    mod_dict = get_mod_dict(config.get("modFolder", "./mods"))
    update_done = threading.Event()

    def fetch_all_latest() -> None:
        def get_mod_by_mod_file(mod_folder: str, mod_file: str) -> tuple[str, str]:
            current_version = get_mod_info.get_mod_current_version(mod_folder, mod_file)
            project_id = get_mod_info.get_mod_project_id(current_version)
            latest_version = get_mod_info.get_mod_latest_version(project_id, config["current_version"])
            return current_version, latest_version
        async def fetch_and_update(mod: tuple[str, dict]) -> None:
            max_retries = config.get("maxRetries", 3)  # 从配置中获取最大重试次数
            retries = 0
            while True:
                try:
                    current_version, latest_version = await asyncio.to_thread(get_mod_by_mod_file, mod_folder=config["modFolder"], mod_file=mod[1]["local_filename"])
                    mod_dict[mod[0]]["current_version"] = current_version
                    mod_dict[mod[0]]["latest_version"] = latest_version
                    mod_dict[mod[0]]["current_version_number"] = get_mod_info.get_mod_version_number(current_version)
                    mod_dict[mod[0]]["latest_version_number"] = get_mod_info.get_mod_version_number(latest_version) or "No compatible version"
                    logging.info(f"Fetched update for {mod[0]}: {current_version} → {latest_version}")
                    break  # 成功则退出循环
                except Exception as e:
                    if e.__class__.__name__ == "NotFoundException":
                        mod_dict[mod[0]]["latest_version_number"] = "Not Found"
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
    def cut(s, width_ref, w):
        out = ''
        for c in s:
            w_c = get_display_length(c)
            if width_ref[0] + w_c > w-1:
                break
            out += c
            width_ref[0] += w_c
        return out
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
                local_version_number = mod[1]["local_version_number"]
                current_version_number = mod[1].get("current_version_number", local_version_number)
                latest_version_number = mod[1].get("latest_version_number", None)
                y = idx + 1
                # 构造各部分字符串
                prefix = f"{pos + idx + 1}. "
                left_paren = "("
                right_paren = ")"
                old_ver = current_version_number
                arrow = " → "
                new_ver = f"{latest_version_number}" if latest_version_number is not None else ""
                # 统一cut逻辑
                width = [0]
                cut_prefix = cut(prefix, width, w)
                cut_name = cut(name, width, w)
                cut_left = cut(left_paren, width, w)
                cut_old = cut(old_ver, width, w)
                cut_arrow = cut(arrow if latest_version_number and current_version_number != latest_version_number else '', width, w)
                cut_new = cut(new_ver if latest_version_number and current_version_number != latest_version_number else '', width, w)
                cut_right = cut(right_paren, width, w)
                # 高亮和着色
                x = 0
                stdscr.addstr(y, x, cut_prefix)
                x += get_display_length(cut_prefix)
                stdscr.addstr(y, x, cut_name)
                x += get_display_length(cut_name)
                stdscr.addstr(y, x, cut_left, curses.color_pair(4))
                x += get_display_length(cut_left)
                # 旧版本号
                if latest_version_number is None:
                    stdscr.addstr(y, x, cut_old, curses.color_pair(4))
                elif current_version_number == latest_version_number:
                    stdscr.addstr(y, x, cut_old, curses.color_pair(2))
                else:
                    stdscr.addstr(y, x, cut_old, curses.color_pair(3))
                x += get_display_length(cut_old)
                # 箭头和新版本号
                if cut_arrow:
                    stdscr.addstr(y, x, cut_arrow)
                    x += get_display_length(cut_arrow)
                if cut_new:
                    stdscr.addstr(y, x, cut_new, curses.color_pair(2 if latest_version_number != "Not Found" and latest_version_number != "No compatible version" else 5))
                    x += get_display_length(cut_new)
                stdscr.addstr(y, x, cut_right, curses.color_pair(4))
            # 进度百分比
            total = len(mod_dict)
            finished = len([mod for mod in mod_dict.values() if mod.get("latest_version_number") is not None])
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
                choose_update_mods(stdscr, mod_dict)
                return  # 直接返回根菜单
        time.sleep(0.01)  # 防止CPU占用过高
    stdscr.nodelay(False)  # 恢复阻塞模式

def choose_update_mods(stdscr, mod_dict) -> None:
    # 只显示有可用更新的mod
    update_mods = [
        (name, mod_dict[name])
        for name in mod_dict
        if mod_dict[name].get("latest_version_number") and mod_dict[name].get("current_version_number") != mod_dict[name].get("latest_version_number") and mod_dict[name].get("latest_version_number") != "Not Found" and mod_dict[name].get("latest_version_number") != "No compatible version"
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
        for idx, (name, mod) in enumerate(visible_mods):
            checked_box = "[*]" if (pos + idx) in checked else "[ ]"
            prefix = f"{pos + idx + 1}. "
            left_paren = "("
            right_paren = ")"
            name_str = name
            old_ver = mod['current_version_number'] or mod['version_number']
            arrow = " → "
            new_ver = f"{mod['latest_version_number']}" if mod['latest_version_number'] is not None else ""
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
        elif key == ord('a') or key == ord('A'):
            # 全选或取消全选
            if len(checked) < total:
                checked = set(range(total))
            else:
                checked.clear()
        elif key == ord('\n'):
            selected_mods = [update_mods[i] for i in checked if i < len(update_mods)]
            if not selected_mods:
                continue
            pos2 = 0
            while True:
                stdscr.clear()
                h, w = stdscr.getmaxyx()
                stdscr.addstr(0, 0, "即将更新下列mod：")
                max_lines = h - 2
                visible_mods = selected_mods[pos2:pos2+max_lines]
                for idx, (mod_name, _) in enumerate(visible_mods):
                    display_str = f"{pos2 + idx + 1}. {mod_name}"
                    cut_str = ''
                    width = 0
                    for c in display_str:
                        w_c = get_display_length(c)
                        if width + w_c > w-1:
                            break
                        cut_str += c
                        width += w_c
                    stdscr.addstr(idx + 1, 0, cut_str)
                stdscr.addstr(h-1, 0, f"共 {len(selected_mods)} 个mod，当前{pos2+1}-{pos2+len(visible_mods)}，上下键翻页，回车继续，q返回")
                stdscr.refresh()
                key2 = stdscr.getch()
                if key2 in (ord('q'), ord('Q')):
                    break  # 返回到选择界面
                elif key2 == curses.KEY_UP:
                    if pos2 > 0:
                        pos2 -= 1
                elif key2 == curses.KEY_DOWN:
                    if pos2 + max_lines < len(selected_mods):
                        pos2 += 1
                elif key2 == ord('\n'):
                    start_update_mods(stdscr, selected_mods)
                    return  # 直接返回主菜单

def start_update_mods(stdscr: Any, selected_mods: list) -> None:
    for mod_name, mod_info in selected_mods:
        stdscr.clear()
        mod_local_name = mod_info["local_filename"]
        mod_latest_version = mod_info["latest_version"]
        stdscr.addstr(0, 0, f"正在更新mod {mod_name} ({mod_local_name}) 到版本 {mod_latest_version.version_number}...")
        stdscr.refresh()
        logging.info(f"Updating mod {mod_name} ({mod_local_name}) to version {mod_latest_version.version_number}")
        update_mod(mod_latest_version, mod_local_name,stdscr=stdscr)
    # 下载全部完成后提示
    stdscr.clear()
    stdscr.addstr(0, 0, "已更新完毕，按任意键继续")
    stdscr.refresh()
    stdscr.getch()
    # 返回主菜单（直接 return 即可，主流程会回到主菜单）

def update_mod(mod_version: Any, mod_local_name: str, stdscr: Any=None) -> None:
    mod_folder = config.get("modFolder", "./mods")
    cache_folder = config.get("cacheFolder", "./cache")
    download_mod(mod_folder, cache_folder, mod_version, stdscr=stdscr)
    backup_old_mod(mod_folder, mod_local_name)

def download_mod(mod_folder, cache_folder, mod_version, stdscr=None, progress_line=1):
    mod_folder = Path(mod_folder)
    cache_folder = Path(cache_folder)
    mod_file = mod_version.files[0]
    file_sha1 = mod_file.hashes.sha1
    file_url = mod_file.url
    file_name = mod_file.filename
    cache_folder.mkdir(exist_ok=True)
    cache_file_path = cache_folder / file_name

    def show_progress(block_num, block_size, total_size):
        if total_size <= 0:
            percent = 0
        else:
            percent = min(100, block_num * block_size * 100 // total_size)
        if stdscr:
            h, w = stdscr.getmaxyx()
            bar_len = max(10, w - len(file_name) - 20)
            filled_len = int(bar_len * percent // 100)
            bar = '█' * filled_len + '-' * (bar_len - filled_len)
            progress_str = f"[下载进度] {file_name}: |{bar}| {percent}%"
            stdscr.addstr(progress_line, 0, progress_str[:w-1])
            stdscr.clrtoeol()
            stdscr.refresh()
        else:
            from sys import stdout
            bar_len = 40
            filled_len = int(bar_len * percent // 100)
            bar = '█' * filled_len + '-' * (bar_len - filled_len)
            stdout.write(f'\r[下载进度] {file_name}: |{bar}| {percent}%')
            stdout.flush()
            if percent == 100:
                print()  # 换行

    logging.info(f"Downloading {file_name} from {file_url} to {cache_folder}")
    urllib.request.urlretrieve(file_url, cache_file_path, reporthook=show_progress)
    logging.info(f"Downloaded {file_name} to {cache_folder}")
    downloaded_file_hash = get_mod_info.get_file_sha1(cache_file_path)
    if downloaded_file_hash != file_sha1:
        logging.error(f"Hash mismatch for {file_name}: {downloaded_file_hash} != {file_sha1}")
        return False
    mod_file_path = mod_folder / file_name
    if not mod_file_path.exists():
        logging.info(f"Moving {file_name} to {mod_folder}")
        os.rename(cache_file_path, mod_file_path)
    else:
        logging.warning(f"File {file_name} already exists in {mod_folder}, skipping download.")

def backup_old_mod(mod_folder: str, mod_file: str) -> None:
    mod_path = Path(mod_folder) / mod_file
    if not mod_path.exists():
        logging.warning(f"Mod file {mod_file} does not exist in {mod_folder}.")
        return
    backup_folder = Path(mod_folder) / "backup"
    backup_folder.mkdir(exist_ok=True)
    backup_path = backup_folder / mod_file
    if backup_path.exists():
        logging.warning(f"Backup file {backup_path} already exists, skipping backup.")
        return
    os.rename(mod_path, backup_path)
    logging.info(f"Backed up {mod_file} to {backup_path}.")

