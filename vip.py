import curses
import os
import shutil

MENU = "^W Write Mode  ^I Insert mode  ^Q Exit No Save  ^Y Save Insert  ^X Exit Write  ^T Exit Insert  ^G Exit Save All"

class Buffer:
    def __init__(self, lines=None):
        self.lines = lines if lines else [""]
        self.cx = 0
        self.cy = 0
        self.scroll = 0

    @classmethod
    def from_file(cls, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            return cls(lines if lines else [""])
        return cls([""])

    def text(self):
        return "\n".join(self.lines)

    def insert(self, ch):
        line = self.lines[self.cy]
        self.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
        self.cx += 1

    def newline(self):
        line = self.lines[self.cy]
        left = line[:self.cx]
        right = line[self.cx:]
        self.lines[self.cy] = left
        self.lines.insert(self.cy + 1, right)
        self.cy += 1
        self.cx = 0

    def backspace(self):
        if self.cx > 0:
            line = self.lines[self.cy]
            self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
            self.cx -= 1
        elif self.cy > 0:
            prev = self.lines[self.cy - 1]
            current = self.lines[self.cy]
            self.cx = len(prev)
            self.lines[self.cy - 1] = prev + current
            del self.lines[self.cy]
            self.cy -= 1

    def left(self):
        if self.cx > 0:
            self.cx -= 1
        elif self.cy > 0:
            self.cy -= 1
            self.cx = len(self.lines[self.cy])

    def right(self):
        if self.cx < len(self.lines[self.cy]):
            self.cx += 1
        elif self.cy < len(self.lines) - 1:
            self.cy += 1
            self.cx = 0

    def up(self):
        if self.cy > 0:
            self.cy -= 1
            self.cx = min(self.cx, len(self.lines[self.cy]))

    def down(self):
        if self.cy < len(self.lines) - 1:
            self.cy += 1
            self.cx = min(self.cx, len(self.lines[self.cy]))

    def adjust_scroll(self, height):
        if self.cy < self.scroll:
            self.scroll = self.cy
        elif self.cy >= self.scroll + height:
            self.scroll = self.cy - height + 1

def save(path, buffer):
    with open(path, "w", encoding="utf-8") as f:
        f.write(buffer.text())

def resolve_path(inp):
    home = os.path.expanduser("~")
    return os.path.abspath(os.path.join(home, inp.strip()))

def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()

    if y < 0 or y >= h:
        return

    if x < 0 or x >= w:
        return

    available = max(0, w - x - 1)

    if available <= 0:
        return

    try:
        stdscr.addstr(y, x, text[:available], attr)
    except:
        pass

def editor(stdscr, original_path):
    curses.raw()
    curses.curs_set(1)
    stdscr.keypad(True)

    original_name = os.path.basename(original_path)
    temp_path = original_path + ".txt"

    write_buffer = Buffer.from_file(original_path)
    insert_buffer = Buffer.from_file(original_path)

    mode = "WRITE"
    active = write_buffer

    while True:
        stdscr.erase()

        h, w = stdscr.getmaxyx()

        if h < 3 or w < 20:
            safe_addstr(stdscr, 0, 0, "Terminal too small.")
            stdscr.refresh()
            continue

        header = f" VIP Editor | File: {original_name} | Mode: {mode} "
        safe_addstr(stdscr, 0, 0, header, curses.A_REVERSE)

        visible_height = h - 2

        active.adjust_scroll(visible_height)

        for i in range(visible_height):
            idx = active.scroll + i

            if idx >= len(active.lines):
                break

            line = active.lines[idx]
            safe_addstr(stdscr, i + 1, 0, line)

        safe_addstr(stdscr, h - 1, 0, MENU, curses.A_REVERSE)

        cy = active.cy - active.scroll + 1
        cx = min(active.cx, w - 2)

        if 1 <= cy < h - 1:
            try:
                stdscr.move(cy, cx)
            except:
                pass

        stdscr.refresh()

        key = stdscr.getch()

        if key == 23:
            mode = "WRITE"
            active = write_buffer

        elif key == 9:
            mode = "INSERT"

            if not os.path.exists(temp_path):
                save(temp_path, write_buffer)

            insert_buffer = Buffer.from_file(temp_path)
            active = insert_buffer

        elif key == 17:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            break

        elif key == 25:
            save(temp_path, insert_buffer)

        elif key == 24:
            save(original_path, write_buffer)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            break

        elif key == 20:
            save(temp_path, insert_buffer)

            if os.path.exists(original_path):
                os.remove(original_path)

            os.rename(temp_path, original_path)
            break

        elif key == 7:
            save(original_path, write_buffer)
            save(temp_path, insert_buffer)
            shutil.copyfile(temp_path, original_path)
            break

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            active.backspace()

        elif key in (10, 13):
            active.newline()

        elif key == curses.KEY_LEFT:
            active.left()

        elif key == curses.KEY_RIGHT:
            active.right()

        elif key == curses.KEY_UP:
            active.up()

        elif key == curses.KEY_DOWN:
            active.down()

        elif 32 <= key <= 126:
            active.insert(chr(key))

def boot():
    print("========================================")
    print("          Welcome to VIP Editor         ")
    print("========================================")

    path_input = input("File to Create/Edit (include full folder path, vip looks from home directory.)\n")

    full_path = resolve_path(path_input)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    if not os.path.exists(full_path):
        with open(full_path, "w", encoding="utf-8"):
            pass

    curses.wrapper(editor, full_path)

if __name__ == "__main__":
    boot()
