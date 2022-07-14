#!/usr/bin/env python
import urwid


def main():
    def show_or_exit(key):
        if key in ("q", "Q"):
            raise urwid.ExitMainLoop()
        txt.set_text(repr(key))

    txt = urwid.Text("Hello World")
    fill = urwid.Filler(txt, "top")
    loop = urwid.MainLoop(fill, unhandled_input=show_or_exit)
    loop.run()


if __name__ == "__main__":
    main()
