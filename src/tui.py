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
    "check_update": lambda: check_update(tui_modules.stdscr),
    "display_mod_list": lambda: display_mod_list(tui_modules.stdscr),
    "set_update_source_modrinth": lambda: (set_update_source("Modrinth", tui_modules.stdscr), tui_modules.navigate_menu(MENU_ITEMS[2]["submenu"][1]["submenu"])),
    "set_update_source_github": lambda: (set_update_source("Github", tui_modules.stdscr), tui_modules.navigate_menu(MENU_ITEMS[2]["submenu"][1]["submenu"])),
    "reload_config": lambda: (reload_config(tui_modules.stdscr)),
    "exit_gui": lambda: exit_gui(),
    "back": lambda: None
}
class TUI:
    def __init__(self,stdscr:curses.window):
        self.stdscr: curses.window = stdscr
    def print_menu(self, selected_row_idx: int, menu: list[dict[str, Any]], offset: int = 0) -> None:
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()

        for idx, item in enumerate(menu):
            text = item["name"]
            text_len = get_display_length(text)
            x = w // 2 - text_len // 2
            y = h // 2 - len(menu) // 2 + idx + offset
            if idx == selected_row_idx:
                self.stdscr.attron(curses.color_pair(1))
                self.stdscr.addstr(y, x, text)
                self.stdscr.attroff(curses.color_pair(1))
            else:
                self.stdscr.addstr(y, x, text)
        self.stdscr.refresh()


    def navigate_menu(self, menu: list[dict[str, Any]], parent: list[dict[str, Any]] | None = None) -> None:
        current_row = 0
        while True:
            self.print_menu(current_row, menu)
            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                current_row = max(0, current_row - 1)
            elif key == curses.KEY_DOWN:
                current_row = min(len(menu) - 1, current_row + 1)
            elif key == ord('\n'):
                selected_item = menu[current_row]
                if selected_item.get("action") == "back":
                    return  # 返回上一级菜单
                if "submenu" in selected_item:
                    self.navigate_menu(selected_item["submenu"], parent=menu)
                else:
                    action = selected_item["action"]
                    func = ACTIONS.get(action)
                    if func:
                        func()
                    else:
                        self.stdscr.addstr(0, 0, "Unknown Action")
                        self.stdscr.refresh()
                        self.stdscr.getch()
                    return

    def input_module(self, prompt: str, default: str) -> str:
        while True:
            curses.echo()
            self.stdscr.clear()
            h, w = self.stdscr.getmaxyx()
            prompt_full = f"{prompt} (当前: {default}，直接回车使用)"
            self.stdscr.addstr(h // 2 - 1, w // 2 - len(prompt_full) // 2, prompt_full)
            self.stdscr.refresh()
            self.stdscr.move(h // 2, w // 2 - 20)
            current = self.stdscr.getstr(h // 2, w // 2 - 20, 40).decode('utf-8').strip()
            curses.noecho()
            if not current:
                current = default
            self.stdscr.addstr(h // 2 + 2, w // 2 - 10, f"已设置: {current}")
            self.stdscr.refresh()
            self.stdscr.getch()
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
    global tui_modules
    tui_modules=TUI(stdscr)
    while True:
        stdscr.clear()
        tui_modules.navigate_menu(MENU_ITEMS)
def input_loop(stdscr: curses.window) -> None:
    tui_modules=TUI(stdscr)
    stdscr.clear()
    from tomli_w import dump
    from tomllib import load
    updateGameVersionFrom=tui_modules.input_module("请输入原游戏版本", "")
    config=load(open("config.toml", "rb"))
    config["updateGameVersionFrom"]=updateGameVersionFrom
    dump(config, open("config.toml", "wb"))
    stdscr.clear()
    updateGameVersionTo=tui_modules.input_module("请输入目标游戏版本", "")
    config=load(open("config.toml", "rb"))
    config["updateGameVersionTo"]=updateGameVersionTo
    dump(config, open("config.toml", "wb"))
def start_menu() -> None:
    curses.wrapper(main_loop)
def start_input() -> None:
    curses.wrapper(input_loop)
if __name__ == "__main__":
    start_menu()
