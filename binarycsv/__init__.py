"""
Read csv files with binary (avoid "UnicodeDecodeError: 'charmap' codec
can't decode byte 0x9d in position 473: character maps to <undefined>"
during the codecs.charmap_decode call where 0x9d is any character not in
the encoding codec.
"""
from __future__ import print_function
import sys


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class reader:
    """Read CSV files containing binary data with no encoding.
    """
    # formerly BinaryCSVReader
    def __init__(self, stream, delimiter=b";", quotechar=b'"'):
        self.stream = stream
        self.line_number = 0  # stay on the line number last processed
        #  for error tracing (increment during __next__ on newline).
        self.cur = 0
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.prev_newline = None
        self.allow_literal_newlines = False  # Not fully implemented

    def __iter__(self):
        return self

    def __next__(self):
        fields = []
        in_quote = None
        in_newline = None
        field = b""
        prev_char = None
        while True:
            ch = self.stream.read(1)
            self.cur += 1
            if sys.version_info.major >= 3:
                if not isinstance(ch, bytes):
                    raise ValueError(
                        "The stream should be in binary mode 'rb'"
                        " but is not (probably was 'r')."
                    )
            if len(ch) < 1:
                if len(field) > 0:
                    fields.append(field)
                # echo0("Done reading %s at pos %s (line %s)"
                #       % ("binary CSV file", self.cur, self.line_number+1))
                raise StopIteration()
            if in_quote is not None:
                if ch == self.quotechar:
                    in_quote = None
                    in_newline = None
                    if prev_char == self.quotechar:
                        # Two quotes is a literal quote in CSV (add as 1 quote)
                        field += ch
                else:
                    field += ch
                if self.allow_literal_newlines:
                    in_newline = None  # Don't treat it as a line delimiter
            else:
                if ch == self.quotechar:
                    in_quote = ch
                    in_newline = None
                elif ch in (b"\r", b"\n"):
                    if in_newline is None:
                        if ((self.prev_newline is not None)
                                and (self.prev_newline != ch)):
                            in_newline = ch
                            # Skip it, the newline resumed from the
                            #   previous call (must be two-part Windows
                            #   "\r\n" CR+LF newline.
                        else:
                            self.line_number += 1
                            # ^ the *last* line number, for error tracing
                            #   such as syntax errors; starts at 1 though
                            #   is at 0 *before* the line is completed
                            #   (The line is completed in this case).
                            fields.append(field)
                            # ^ includes quotes
                            field = b""
                            self.prev_newline = ch
                            break  # return the fields only on newline/EOF
                    in_newline = ch
                elif ch == self.delimiter:
                    fields.append(field)
                    field = b""
                    in_newline = None
                else:
                    field += ch
                    in_newline = None
            prev_char = ch
            self.prev_newline = in_newline

        return fields


def ascii_string(value):
    """Prevent UnicodeDecodeError when using for Tkinter widget text.

    Circumvent errors such as "UnicodeDecodeError: 'ascii' codec can't
    decode byte 0xd4 in position 8: ordinal not in range(128)"
    """
    result = ""
    if not isinstance(value, str):
        echo0("[ascii_string] Warning: value is %s not str: %s"
              % (type(value).__name__, value))
        return value
    print("input=%s" % value)
    for ch in value:
        if ord(ch) > 127:
            result += "."
            continue
        result += ch
    return result


def safe_string(value):
    """Make the string able to be used in the GUI.
    """
    if sys.version_info.major >= 3:
        # In Python 3, every string is safe for tkinter.
        return value
    return ascii_string(value)


def pformat(value, prefer_quote='"'):
    result = ""
    if type(value).__name__ in ("str", "unicode", "bytes", "bytearray"):
        v_str = str(value)
        opener = "bytearray("
        if v_str.startswith(opener) and v_str.endswith(")"):
            # Such as 'bytearray(b"some value")'
            v_str = v_str[len(opener):-1]
        if v_str.startswith('b"') and v_str.endswith('"'):
            v_str = v_str[2:-1]
        elif v_str.startswith("b'") and v_str.endswith("'"):
            v_str = v_str[2:-1]
        return prefer_quote + v_str + prefer_quote
    elif hasattr(value, "items"):
        result = "{"
        for k, v in value.items():
            k_str = pformat(k, prefer_quote="'")
            result += "%s: %s, " % (k_str, pformat(v))
        result += "}"
    else:
        result = str(value)
    return result
