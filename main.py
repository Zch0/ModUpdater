if __name__ == "__main__":
    import os
    from src.generate_config import generate_config
    if not os.path.isfile("config.toml"):
        generate_config()
        from src.tui import start_menu,start_fill_miss_config
        start_fill_miss_config()
    else:from src.tui import start_menu,start_fill_miss_config
    start_menu()
