import curses
from tabnanny import check

from tools import check_update, display_mod_list, exit_gui, get_display_length, set_mod_directory, set_update_source

# 定义菜单结构
MENU_ITEMS = [
    {"name": "开始更新", "action": "start_update"},
    {"name": "检查更新", "action": "check_update"},
    {"name": "查看mod列表", "action": "display_mod_list"},
    {
        "name": "设置",
        "submenu": [
            {"name": "mod目录", "action": "set_mod_directory"},
            {"name": "更新来源", "submenu": [
                {"name": "Modrinth", "action": "set_update_source_modrinth"},
                {"name": "Github", "action": "set_update_source_github"},
            ]},
        ]
    },
    {"name": "退出", "action": "exit_gui"}
]
ACTIONS = {
    "start_update": lambda: print("开始更新..."),
    "check_update": lambda stdscr: check_update(stdscr),
    "display_mod_list": lambda stdscr: display_mod_list(stdscr),
    "set_mod_directory": lambda stdscr: set_mod_directory(stdscr),
    "set_update_source_modrinth": lambda stdscr: set_update_source("Modrinth", stdscr),
    "set_update_source_github": lambda stdscr: set_update_source("Github", stdscr),
    "exit_gui": exit_gui
}


def print_menu(stdscr, selected_row_idx, menu, offset=0):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    for idx, item in enumerate(menu):
        text = item["name"]
        # 使用 display length 来计算居中位置
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


def navigate_menu(stdscr, menu, parent=None):
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
            if "submenu" in selected_item:
                navigate_menu(stdscr, selected_item["submenu"], parent=menu)
            else:
                action = selected_item["action"]
                # 直接执行 action
                func = ACTIONS.get(action)
                if func:
                    func(stdscr)
                else:
                    stdscr.addstr(0, 0, "Unknown Action")
                    stdscr.refresh()
                    stdscr.getch()
                # 执行完 action 后返回菜单
                return


def main_loop(stdscr):
    # 初始化颜色
    curses.curs_set(0)
    curses.start_color()
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # 菜单选中
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # 绿色
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # 红色
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)  # 白色
    while True:
        stdscr.clear()
        navigate_menu(stdscr, MENU_ITEMS)


def main():
    curses.wrapper(main_loop)


if __name__ == "__main__":
    main()
