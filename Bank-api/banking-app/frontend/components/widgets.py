from tkinter import Button, Label, Entry, Frame

class WidgetFactory:
    @staticmethod
    def create_button(master, text, command=None):
        return Button(master, text=text, command=command)

    @staticmethod
    def create_label(master, text):
        return Label(master, text=text)

    @staticmethod
    def create_entry(master):
        return Entry(master)

    @staticmethod
    def create_frame(master):
        return Frame(master)