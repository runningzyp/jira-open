#!/usr/bin/env python

import urwid


class PopUpDialog(urwid.WidgetWrap):
    """A dialog that appears with nothing but a close button"""

    signals = ["close"]

    def __init__(self):
        close_button = urwid.Button("that's pretty cool")
        urwid.connect_signal(close_button, "click", lambda button: self._emit("close"))
        pile = urwid.Pile(
            [
                urwid.Text(
                    "^^  I'm attached to the widget that opened me. "
                    "Try resizing the window!\n"
                ),
                close_button,
            ]
        )
        fill = urwid.Filler(pile)
        self.__super.__init__(urwid.AttrWrap(fill, "popbg"))


class ThingWithAPopUp(urwid.PopUpLauncher):
    def __init__(self, widget):
        super().__init__(widget)
        urwid.connect_signal(widget, "click", lambda widget: self.open_pop_up())

    def create_pop_up(self):
        pop_up = PopUpDialog()
        urwid.connect_signal(pop_up, "close", lambda button: self.close_pop_up())
        return pop_up

    def get_pop_up_parameters(self):
        return {"left": 0, "top": 1, "overlay_width": 32, "overlay_height": 7}
