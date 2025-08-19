'''
TODO: 
完成初始化配置文件逻辑，第一次打开需输入部分配置
将stdscr的传递改成class内传递！！！
用类封装tui！！！
'''
import curses
from typing import Any, Callable, List, Dict, Optional

from .tools import check_update, display_mod_list, exit_gui, get_display_length, set_update_source,reload_config
MENU_ITEMS: list[dict[str, Any]] = [
    {"name": "检查更新", "action": "check_update"},
    {"name": "查看mod列表", "action": "display_mod_list"},
    {
        "name": "设置",
        "submenu": [
            # {"name": "mod目录", "action": "set_mod_directory"},
            # {"name": "更新来源", "submenu": [
            #     {"name": "Modrinth", "action": "set_update_source_modrinth"},
            #     {"name": "CurseForge", "action": "set_update_source_curseforge"},
            #     {"name": "返回", "action": "back"}
            # ]},
            {"name":"重新载入配置文件", "action": "reload_config"},
            {"name": "返回", "action": "back"}
        ]
    },
    {"name": "退出", "action": "exit_gui"}
]

ACTIONS: dict[str, Callable[..., Any]] = {
    "start_update": lambda: print("开始更新..."),
    "check_update": lambda stdscr: check_update(stdscr),
    "display_mod_list": lambda stdscr: display_mod_list(stdscr),
    "set_update_source_modrinth": lambda stdscr: (set_update_source("Modrinth", stdscr), navigate_menu(stdscr, MENU_ITEMS[2]["submenu"][1]["submenu"])),
    "set_update_source_github": lambda stdscr: (set_update_source("Github", stdscr), navigate_menu(stdscr, MENU_ITEMS[2]["submenu"][1]["submenu"])),
    "reload_config": lambda stdscr: (reload_config(stdscr)),
    "exit_gui": lambda stdscr: exit_gui(),
    "back": lambda stdscr: None
}
def print_menu(stdscr: curses.window, selected_row_idx: int, menu: list[dict[str, Any]], offset: int = 0) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    for idx, item in enumerate(menu):
        text = item["name"]
        text_len = get_display_length(text)
        x = w // 2 - text_len // 2
        y = h // 2 - len(menu) // 2 + idx + offset
        if idx == selected_row_idx:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, text)
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, text)
    stdscr.refresh()


def navigate_menu(stdscr: curses.window, menu: list[dict[str, Any]], parent: list[dict[str, Any]] | None = None) -> None:
    current_row = 0
    while True:
        print_menu(stdscr, current_row, menu)
        key = stdscr.getch()

        if key == curses.KEY_UP:
            current_row = max(0, current_row - 1)
        elif key == curses.KEY_DOWN:
            current_row = min(len(menu) - 1, current_row + 1)
        elif key == ord('\n'):
            selected_item = menu[current_row]
            if selected_item.get("action") == "back":
                return  # 返回上一级菜单
            if "submenu" in selected_item:
                navigate_menu(stdscr, selected_item["submenu"], parent=menu)
            else:
                action = selected_item["action"]
                func = ACTIONS.get(action)
                if func:
                    func(stdscr)
                else:
                    stdscr.addstr(0, 0, "Unknown Action")
                    stdscr.refresh()
                    stdscr.getch()
                return

def input_module(stdscr: curses.window, prompt: str, default: str) -> str:
    while True:
        curses.echo()
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        prompt_full = f"{prompt} (当前: {default}，直接回车使用)"
        stdscr.addstr(h // 2 - 1, w // 2 - len(prompt_full) // 2, prompt_full)
        stdscr.refresh()
        stdscr.move(h // 2, w // 2 - 20)
        current = stdscr.getstr(h // 2, w // 2 - 20, 40).decode('utf-8').strip()
        curses.noecho()
        if not current:
            current = default
        stdscr.addstr(h // 2 + 2, w // 2 - 10, f"已设置: {current}")
        stdscr.refresh()
        stdscr.getch()
        return current
def main_loop(stdscr: curses.window) -> None:
    curses.curs_set(0)
    curses.start_color()
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    while True:
        stdscr.clear()
        navigate_menu(stdscr, MENU_ITEMS)


def tui() -> None:
    curses.wrapper(main_loop)
if __name__ == "__main__":
    tui()
