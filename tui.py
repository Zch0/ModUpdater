import curses
from typing import Any, Callable, List, Dict, Optional
from tools import check_update, display_mod_list, exit_gui, get_display_length, set_mod_directory, set_update_source

MENU_ITEMS: List[Dict[str, Any]] = [
    {"name": "检查更新", "action": "check_update"},
    {"name": "查看mod列表", "action": "display_mod_list"},
    {
        "name": "设置",
        "submenu": [
            {"name": "mod目录", "action": "set_mod_directory"},
            {"name": "更新来源", "submenu": [
                {"name": "Modrinth", "action": "set_update_source_modrinth"},
                {"name": "Github", "action": "set_update_source_github"},
                {"name": "返回", "action": "back"}
            ]},
            {"name": "返回", "action": "back"}
        ]
    },
    {"name": "退出", "action": "exit_gui"}
]
ACTIONS: Dict[str, Callable[..., Any]] = {
    "start_update": lambda: print("开始更新..."),
    "check_update": lambda stdscr: check_update(stdscr),
    "display_mod_list": lambda stdscr: display_mod_list(stdscr),
    "set_mod_directory": lambda stdscr: (set_mod_directory(stdscr), navigate_menu(stdscr, MENU_ITEMS[2]["submenu"])),
    "set_update_source_modrinth": lambda stdscr: (set_update_source("Modrinth", stdscr), navigate_menu(stdscr, MENU_ITEMS[3]["submenu"][1]["submenu"])),
    "set_update_source_github": lambda stdscr: (set_update_source("Github", stdscr), navigate_menu(stdscr, MENU_ITEMS[3]["submenu"][1]["submenu"])),
    "exit_gui": lambda stdscr: exit_gui(),
    "back": lambda stdscr: None
}


def print_menu(stdscr: Any, selected_row_idx: int, menu: List[Dict[str, Any]], offset: int = 0) -> None:
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


def navigate_menu(stdscr: Any, menu: List[Dict[str, Any]], parent: Optional[List[Dict[str, Any]]] = None) -> None:
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


def main_loop(stdscr: Any) -> None:
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


def main() -> None:
    curses.wrapper(main_loop)


if __name__ == "__main__":
    main()
