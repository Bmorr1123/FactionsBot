import discord, psutil, atexit

def on_close():
    pass


def main():
    atexit.register(on_close)


if __name__ == '__main__':
    main()

