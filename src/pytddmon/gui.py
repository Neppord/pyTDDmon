import sys
import platform

ON_PYTHON3 = sys.version_info[0] == 3
ON_WINDOWS = platform.system() == "Windows"

def import_tkinter():
    "imports tkinter from python 3.x or python 2.x"
    if not ON_PYTHON3:
        import Tkinter as tkinter
    else:
        import tkinter
    return tkinter


def import_tk_font():
    "imports tkFont from python 3.x or python 2.x"
    if not ON_PYTHON3:
        import tkFont as tk_font
    else:
        from tkinter import font as tk_font
    return tk_font


class TKGUIButton(object):
    """Encapsulate the button(label)"""
    def __init__(self, tkinter, tk_font, toplevel, display_log_callback):
        self.font = tk_font.Font(name="Helvetica", size=28)
        self.label = tkinter.Label(
            toplevel,
            text="loading...",
            relief='raised',
            font=self.font,
            justify=tkinter.CENTER,
            anchor=tkinter.CENTER
        )
        self.bind_click(display_log_callback)
        self.pack()

    def bind_click(self, display_log_callback):
        """Binds the left mous button click event to trigger the logg_windows\
        diplay method"""
        self.label.bind(
            '<Button-1>',
            display_log_callback
        )

    def pack(self):
        "packs the lable"
        self.label.pack(
            expand=1,
            fill='both'
        )

    def update(self, text, color):
        "updates the collor and displayed text."
        self.label.configure(
            bg=color,
            activebackground=color,
            text=text
        )


class TkGUI(object):
    """Connect pytddmon engine to Tkinter GUI toolkit"""
    def __init__(self, pytddmon, tkinter, tk_font):
        self.pytddmon = pytddmon
        self.tkinter = tkinter
        self.tk_font = tk_font
        self.color_picker = ColorPicker()
        self.root = None
        self.building_root()
        self.title_font = None
        self.building_fonts()
        self.frame = None
        self.building_frame()
        self.button = TKGUIButton(
            tkinter,
            tk_font,
            self.frame,
            self.display_log_message
        )
        self.status_bar = None
        self.building_status_bar()
        self.frame.grid()
        self.message_window = None
        self.text = None

        if ON_WINDOWS:
            buttons_width = 25
        else:
            buttons_width = 75
        self.root.minsize(
            width=self.title_font.measure(
                self.pytddmon.project_name
            ) + buttons_width,
            height=0
        )
        self.frame.pack(expand=1, fill="both")
        self.create_text_window()
        self.update_text_window()

    def building_root(self):
        """take hold of the tk root object as self.root"""
        self.root = self.tkinter.Tk()
        self.root.wm_attributes("-topmost", 1)
        if ON_WINDOWS:
            self.root.attributes("-toolwindow", 1)
            print("Minimize me!")

    def building_fonts(self):
        "building fonts"
        self.title_font = self.tk_font.nametofont("TkCaptionFont")

    def building_frame(self):
        """Creates a frame and assigns it to self.frame"""
        # Calculate the width of the tilte + buttons
        self.frame = self.tkinter.Frame(
            self.root
        )
        # Sets the title of the gui
        self.frame.master.title(self.pytddmon.project_name)
        # Forces the window to not be resizeable
        self.frame.master.resizable(False, False)
        self.frame.pack(expand=1, fill="both")

    def building_status_bar(self):
        """Add status bar and assign it to self.status_bar"""
        self.status_bar = self.tkinter.Label(
            self.frame,
            text="n/a"
        )
        self.status_bar.pack(expand=1, fill="both")

    def _update_and_get_color(self):
        "Calculate the current color and trigger pulse"
        self.color_picker.set_result(
            self.pytddmon.result.passed,
            self.pytddmon.result.total,
        )
        light, color = self.color_picker.pick()
        rgb = self.color_picker.translate_color(light, color)
        self.color_picker.pulse()
        return rgb

    def _get_text(self):
        "Calculates the text to show the user(passed/total or Error!)"
        if self.pytddmon.result.total.imag != 0:
            text = "?ERROR"
        else:
            text = "%r/%r" % (
                self.pytddmon.result.passed,
                self.pytddmon.result.total
            )
        return text

    def update(self):
        """updates the tk gui"""
        rgb = self._update_and_get_color()
        text = self._get_text()
        self.button.update(text, rgb)
        self.root.configure(bg=rgb)
        self.update_status(self.pytddmon.get_status_message())

        if self.pytddmon.change_detected:
            self.update_text_window()

    def update_status(self, message):
        self.status_bar.configure(
            text=message
        )
        self.status_bar.update_idletasks()

    def get_text_message(self):
        """returns the logmessage from pytddmon"""
        message = self.pytddmon.get_log()
        return message

    def create_text_window(self):
        """creates new window and text widget"""
        win = self.tkinter.Toplevel()
        if ON_WINDOWS:
            win.attributes("-toolwindow", 1)
        win.title('Details')
        self.message_window = win
        self.text = self.tkinter.Text(win)
        self.message_window.withdraw()

    def update_text_window(self):
        """inserts/replaces the log message in the text widget"""
        text = self.text
        text['state'] = self.tkinter.NORMAL
        text.delete(1.0, self.tkinter.END)
        text.insert(self.tkinter.INSERT, self.get_text_message())
        text['state'] = self.tkinter.DISABLED
        text.pack(expand=1, fill='both')
        text.focus_set()

    def display_log_message(self, _arg):
        """displays/close the logmessage from pytddmon in a window"""
        if self.message_window.state() == 'normal':
            self.message_window.state('iconic')
        else:
            self.message_window.state('normal')

    def loop(self):
        """the main loop"""
        if self.pytddmon.get_and_set_change_detected():
            self.update_status('Testing...')
            self.pytddmon.run_tests()
        self.update()
        self.frame.after(750, self.loop)

    def run(self):
        """starts the main loop and goes into sleep"""
        self.loop()
        self.root.mainloop()


class ColorPicker:
    """
    ColorPicker decides the background color the pytddmon window,
    based on the number of green tests, and the total number of
    tests. Also, there is a "pulse" (light color, dark color),
    to increase the feeling of continous testing.
    """
    color_table = {
        (True, 'green'): '0f0',
        (False, 'green'): '0c0',
        (True, 'red'): 'f00',
        (False, 'red'): 'c00',
        (True, 'orange'): 'fc0',
        (False, 'orange'): 'ca0',
        (True, 'gray'): '999',
        (False, 'gray'): '555'
    }

    def __init__(self):
        self.color = 'green'
        self.light = True

    def pick(self):
        "returns the tuple (light, color) with the types(bool ,str)"
        return (self.light, self.color)

    def pulse(self):
        "updates the light state"
        self.light = not self.light

    def reset_pulse(self):
        "resets the light state"
        self.light = True

    def set_result(self, green, total):
        "calculates what color should be used and may reset the lightness"
        old_color = self.color
        self.color = 'green'
        if green.imag or total.imag:
            self.color = "orange"
        elif green == total - 1:
            self.color = 'red'
        elif green < total - 1:
            self.color = 'gray'
        if self.color != old_color:
            self.reset_pulse()

    @classmethod
    def translate_color(cls, light, color):
        """helper method to create a rgb string"""
        return "#" + cls.color_table[(light, color)]
