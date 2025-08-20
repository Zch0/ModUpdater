if __name__ == "__main__":
    import os
    from src.generate_config import generate_config
    if not os.path.isfile("config.toml"):
        generate_config()
        from src.tui import start_menu,start_input
        start_input()
    else:from src.tui import start_menu,start_input
    start_menu()
