"""
SPM Analyzer

Analyze CSV files exported from Electronic Team's
[Serial Port Monitor](https://www.serial-port-monitor.org/).

Author: Jake Gustafson

Usage:
py -3 spmanalyzer.py <path>
"""
from __future__ import print_function
# import csv
import os
import platform
import sys

from datetime import datetime

if sys.version_info.major >= 3:  # try:
    from tkinter import messagebox
    from tkinter import filedialog
    # from tkinter import simpledialog
    import tkinter as tk
    import tkinter.font as tkFont
    from tkinter import ttk
    # from tkinter import tix
else:  # except ImportError:
    # Python 2
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
    # import tkSimpleDialog as simpledialog
    import Tkinter as tk
    import tkFont
    import ttk
    # import Tix as tix


from collections import OrderedDict


import binarycsv

from binarycsv import (
    pformat,
    safe_string,
    echo0,
)

enable_gui = True

HOME = None
if platform.system() == "Windows":
    HOME = os.environ['USERPROFILE']
else:
    HOME = os.environ['HOME']

path = None
try_name = "ENC W update with 1.88 - fail no valid sound files found.csv"

PROPRIETARY_TEST_PATHS = [
    os.path.join(HOME, "Desktop", try_name),
    os.path.join("F:\\", try_name),
]

SPM_TIME_FMT = "%d/%m/%Y %H:%M:%S"



def analyze_spm_log(src):
    """
    Analyze a CSV exported from Serial Port Monitor using Right-click,
    Export while selecting row(s) of data that was captured.

    This function uses csv.DictReader which requires that the first row
    is titles.
    """
    header_row = None
    with open(src, mode='rb') as stream:
        # _reader = csv._reader(stream)
        # ^ Can't read binary
        # _reader = csv.DictReader(stream)
        # ^ Can't read binary
        _reader = binarycsv.reader(stream)
        number = 0
        for row in _reader:
            number += 1
            if header_row is None:
                header_row = []
                for name in row:
                    header_row.append(name.decode('utf-8'))
                print("header row[{}]={}".format(number, pformat(row)))
                continue
            if len(header_row) != len(row):
                echo0('"{}", Line {}: incorrect column count'
                      ''.format(src, _reader.line_number))
                raise ValueError(
                    ' {} length is {} but there are {} columns'
                    ' in header row: {}'
                    ''.format(row, len(row),
                              len(header_row), header_row)
                )
            meta = OrderedDict()
            for i in range(len(header_row)):
                key = header_row[i]
                meta[key] = row[i]  # store current field in this row
            if len(meta['Time']) > 0:
                meta['Time'] = datetime.strptime(meta['Time'], SPM_TIME_FMT)
            print("row[{}]={}".format(number, pformat(meta)))
            data = meta['Data']
            data_chars = meta['Data (chars)']
            print("  data={}".format(data))
            print("  data_chars={}".format(data_chars))


class MainApplication(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        self.style = ttk.Style()
        if platform.system() == "Windows":
            if 'winnative' in self.style.theme_names():
                self.style.theme_use('winnative')
        elif platform.system() == "Darwin":
            if 'aqua' in self.style.theme_names():
                self.style.theme_use('aqua')
        ttk.Frame.__init__(self, parent, *args, **kwargs)

        self.meta_lookup = {}  # Lookup a dict using its str representation
        self.row = 0
        self.columnspan = 3
        self.container = self
        container = self.container
        for row in range(10):
            container.rowconfigure(index=row, weight=1)
        for column in range(self.columnspan):
            weight = 1
            # if column == 1:
            #     weight = 4
            container.columnconfigure(index=column, weight=weight)

        self.parent = parent

        self.sourceLabel = ttk.Label(
            container,
            text="CSV (exported from SPM)",
        )
        self.sourceLabel.grid(row=container.row, column=0)
        self.sourceVar = tk.StringVar(container)
        self.sourceEntry = ttk.Entry(
            container,
            textvariable=self.sourceVar,
        )
        self.sourceEntry.grid(
            row=container.row,
            column=1,
            sticky="we",
        )

        self.sourceButton = ttk.Button(
            container,
            text="Browse...",
            command=self.browseFile1,
        )
        self.sourceButton.grid(row=self.row, column=2)
        self.row += 1

        self.analyzeBtn = ttk.Button(
            container,
            text="Analyze 1",
            command=self.analyze,
        )
        self.analyzeBtn.grid(row=self.row, column=2)
        self.row += 1

        self.analyze10Btn = ttk.Button(
            container,
            text="Analyze 10",
            command=self.analyze10,
        )
        self.analyze10Btn.grid(row=self.row, column=2)
        self.row += 1

        self.analyzeAllBtn = ttk.Button(
            container,
            text="Analyze All",
            command=self.analyzeAll,
        )
        self.analyzeAllBtn.grid(row=self.row, column=2)
        self.row += 1

        self.logLabel = ttk.Label(
            container,
            text="Log   -->",
        )
        self.logLabel.grid(row=self.row, column=0)
        self.writeLabel = ttk.Label(
            container,
            text="WRITE",
        )
        self.writeLabel.grid(row=self.row, column=1)
        self.readLabel = ttk.Label(
            container,
            text="READ",
        )
        self.readLabel.grid(row=self.row, column=2)
        self.row += 1

        light_framestyle = ttk.Style()
        light_framestyle.configure('light.TFrame', background='#7AC5CD')

        self.column = 0
        self.listLabels = OrderedDict(
            log=self.logLabel,
            read=self.readLabel,
            write=self.writeLabel,
        )
        self.listboxes = OrderedDict()

        self.pack_list("log")
        self.pack_list("write")
        self.pack_list("read")
        self.row += 1
        self.column = 0

        self.statusVar = tk.StringVar(container)
        self.statusLabel = ttk.Entry(
            container,
            text="",
            textvariable=self.statusVar,
            state="readonly",
        )
        self.statusLabel.grid(
            row=self.row,
            column=0,
            columnspan=self.columnspan,
            sticky="we",
        )
        self.row += 1

        for row in range(self.row):
            container.rowconfigure(index=row, weight=1)
        for column in range(self.columnspan):
            container.columnconfigure(index=column, weight=1)
        root.after(1, self.validate_settings)
        # self.driveEntry.bind("<Button-1>", self.on_drive_combo_mousedown)
        screenW = root.winfo_screenwidth()
        screenH = root.winfo_screenheight()
        winW = int(screenW * .66)
        winH = int(screenH * .1)
        root.minsize(winW, winH)
        x_coordinate = int((screenW/2) - (winW/2))
        y_coordinate = int((screenH/2) - (winH/2))
        root.geometry("+{}+{}".format(x_coordinate, y_coordinate))
        self.stream = None
        self.number = None
        self._reader = None
        self.header_row = None
        self.source = None
        self.read_total = 0
        self.write_total = 0

    def pack_list(self, list_name, container=None):
        if container is None:
            container = self

        listContainer = ttk.Frame(
            container,
            # bg="darkgray",  only for tk not ttk
            style="light.TFrame",
        )

        scrollbar = ttk.Scrollbar(listContainer)
        # ttk.Treeview can be displayed similarly to tk.Listbox
        #   (See <https://stackoverflow.com/a/75609905>):
        listbox = ttk.Treeview(
            listContainer,
            yscrollcommand=scrollbar.set,
            show="tree",
        )
        scrollbar.configure(command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)
        # if list_name == "log":
        listbox.bind("<<TreeviewSelect>>", self.item_selected)

        self.listboxes[list_name] = listbox

        listContainer.grid(
            row=self.row,
            column=self.column,
            # columnspan=self.columnspan,
        )
        self.column += 1

    def item_selected(self, event):
        tree = event.widget
        # selection = [tree.item(item)["text"] for item in tree.selection()]
        # self.set_status("{}".format(selection))
        for item in tree.selection():
            item_dict = tree.item(item)
            if len(item_dict['values']) > 0:
                key = item_dict['values'][0]
                if key:
                    meta = self.meta_lookup[key]
                    print("got {} meta={}".format(type(meta).__name__, meta))
                    chars = meta['Data (chars)']
                    data = meta['Data']
                    self.set_status("{}={}".format(chars, data))
                    # ^ Use {} not %s to avoid ASCII out of range
                    #   error in Python 2
                else:
                    print("`values` arg was not str (str key was expected)"
                          " in the self.listbox.insert call.")
            else:
                print("`values` arg was not set"
                      " in the self.listbox.insert call.")

    def validate_settings(self):
        if not self.sourceVar.get().strip():
            for try_path in PROPRIETARY_TEST_PATHS:
                if os.path.isfile(try_path):
                    self.sourceVar.set(try_path)

    def add_message(self, text, meta=None):
        # Assumes listbox is ttk.Treeview
        listbox = self.listboxes["log"]
        key = None
        if meta:
            key = str(meta)
            self.meta_lookup[key] = meta
        listbox.insert("", tk.END, text=text, values=(key,))

    def add_read(self, text, meta=None):
        # Assumes listbox is ttk.Treeview
        bytes_count = len(text)
        hex_str = None
        hex_pairs = None
        key = None
        if meta:
            hex_str = meta['Data']
            hex_pairs = hex_str.split()
            bytes_count = len(hex_pairs)
            key = str(meta)
            self.meta_lookup[key] = meta

        self.read_total += bytes_count
        label = self.listLabels['read']
        label.configure(text="READ ({} byte(s))".format(self.read_total))

        listbox = self.listboxes["read"]
        listbox.insert("", tk.END, text=text, values=(key,))

    def add_write(self, text, meta=None):
        # Assumes listbox is ttk.Treeview
        bytes_count = len(text)
        hex_str = None
        hex_pairs = None
        if meta:
            hex_str = meta['Data']
            hex_pairs = hex_str.split()
            bytes_count = len(hex_pairs)
            key = str(meta)
            self.meta_lookup[key] = meta

        self.write_total += bytes_count
        label = self.listLabels['write']
        label.configure(text="WRITE ({} byte(s))".format(self.write_total))

        listbox = self.listboxes["write"]
        listbox.insert("", tk.END, text=text, values=(key,))

    def set_status(self, message):
        self.statusVar.set(message)

    def _browseFile(self, destVar):
        name = filedialog.askopenfilename()
        if name:
            destVar.set(name)
            self.enable_next_buttons(True)
        else:
            self.enable_next_buttons(False)

    def browseFile1(self):
        self._browseFile(self.sourceVar)

    def enable_next_buttons(self, enable):
        state = tk.NORMAL if enable else tk.DISABLED
        for button in (self.analyzeBtn, self.analyze10Btn, self.analyzeAllBtn):
            button.configure(state=state)

    def next_useful_meta(self):
        """Get the next useful capture from the log

        Only keep IRP_MJ_READ with Direction=="DOWN", or
        or IRP_MJ_WRITE with Direction=="UP". Otherwise, the
        data is UART ACK related and redundant.

        "If DOWN is displayed, the request was initiated by the
        application, otherwise by the device driver."
        -<https://help.electronic.us/support/solutions/articles
        /44002214665-introduction-to-serial-port-monitor>
        """
        while True:
            try:
                row = self._reader.__next__()  # emulate "for row in _reader"
            except StopIteration:
                self.set_status("Done reading data.")
                self.enable_next_buttons(False)
                self.close_file()
                break
            meta = OrderedDict()

            self.number += 1
            if self.header_row is None:
                self.header_row = []
                for name in row:
                    self.header_row.append(name.decode('utf-8'))
                self.set_status("header row[{}]={}"
                                "".format(self.number, pformat(row)))
                continue

            if len(self.header_row) != len(row):
                self.set_status('"{}", Line {}: incorrect column count'
                                ''.format(self.source, self._reader.line_number))
                raise ValueError(
                    ' {} length is {} but there are {} columns'
                    ' in header row: {}'
                    .format(row, len(row),
                            len(self.header_row), self.header_row)
                )

            for i in range(len(self.header_row)):
                key = self.header_row[i]
                text = row[i]
                if key != "Data (chars)":
                    if isinstance(text, bytes):
                        text = text.decode('utf-8')
                # else leave Data (chars) as bytes
                meta[key] = text  # store current field in this row
            if meta['Function'] == "IRP_MJ_READ":
                if meta['Direction'] == "UP":
                    self.add_read(meta['Data'], meta=meta)
                    break
            elif meta['Function'] == "IRP_MJ_WRITE":
                if meta['Direction'] == "DOWN":
                    self.add_write(meta['Data'], meta=meta)
                    break
            else:
                print("Unknown meta function {}".format(meta['Function']))
            # Data is ignored if no "break" occurs above
            print("Ignoring UART control data captured: {}".format(meta))
            meta = None
        if meta is None:
            raise StopIteration()
        return meta

    def analyze(self):
        self.source = self.sourceVar.get()
        # try:
        if self.stream is None:
            self.stream = open(self.source, mode='rb')
            self.number = 0
            self._reader = binarycsv.reader(self.stream)
            self.enable_next_buttons(True)
        # except

        meta = self.next_useful_meta()
        self.set_status("row[{}]={}".format(self.number, pformat(meta)))
        data = meta['Data']  # Hex chars (therefore in ASCII range)
        data_chars = meta['Data (chars)']
        # self.add_message("  data={}".format(data))
        # self.add_message("  data_chars={}".format(data_chars))
        data_len = meta['Data length']
        if len(data_len) > 0:
            data_len = int(data_len)
            self.add_message(
                "capture {}={} {}: {} (length {})={}".format(
                    int(meta['#']),
                    meta['Function'],
                    meta['Direction'],
                    data_chars,  # safe_string(data_chars),
                    # ^ non-ASCII already safe in py 2 if format not %s
                    data_len,
                    data,  # hex encoded (ASCII-safe)
                ),
                meta=meta,
            )
        else:
            print("Ingoring 0-length (non-data) capture: {}".format(meta))
            # ignore non-data UART protocol packet, such as:
            # ["OrderedDict([
            #   ('#', '17'),
            #   ('Time', '22/09/2023 10:50:54'), ('Function', 'IRP_MJ_READ'),
            #   ('Direction', 'DOWN'), ('Status', ''), ('Data', ''),
            #   ('Data (chars)', b''), ('Data length', ''), ('Req. length', '1'),
            #   ('Port', 'COM3'), ('Comments', ''), ('', '')])"
            # ]

    def analyze10(self):
        for _ in range(10):
            self.analyze()


    def analyzeAll(self):
        self.analyze()  # call once manually to initialize self.stream
        self.enable_next_buttons(False)
        while self.stream is not None:
            # ^ Must be set to None via close_file on StopIteration
            #   or this loop will be infinite (see next_useful_meta)!
            self.analyze()

    def close_file(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None



def usage():
    print(__doc__, file=sys.stderr)


def main():
    if os.path.isfile(try_path):
        path = try_path
    if path is None:
        if len(sys.argv) < 2:
            usage()
            echo0("Error: No path was specified. Specify a CSV file.")
            return 1
        path = sys.argv[1]
    analyze_spm_log(path)

    return 0


if __name__ == "__main__":
    if not enable_gui:
        sys.exit(main())

    root = tk.Tk()
    root.title("SPM Analyzer by Hierosoft")
    app = MainApplication(root)
    app.pack(side="top", fill="both", expand=True)
    # app.grid(
    #     row=0,
    #     column=0,
    #     sticky=tk.NSEW,
    # )
    # app.load_settings()
    root.mainloop()
    # app.save_settings()
    app.close_file()
