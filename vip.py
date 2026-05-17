import curses
import os
import copy
import re

MENU = " ^W Write  ^E Insert  ^Q Quit  ^Y Commit  ^X Save&Exit Wr  ^B Save&Exit Ins  ^T Esc Ins  ^G Save&Exit All  ^F Find  ^Z Undo "

SYNTAX_RULES = [
    (r'\b(def|class|return|if|elif|else|for|while|break|continue|import|from|as|in|is|not|and|or|try|except|raise|with|pass|lambda|None|True|False)\b', 3),
    (r'(\d+)', 4),
    (r'(\".*?\"|\'.*?\')', 5),
    (r'(#.*$)', 6),
]

class Buffer:
    def __init__(self, path=None, lines=None, cx=0, cy=0, scroll=0, hscroll=0):
        self.path = path
        self.lines = lines if lines else [""]
        self.cx = cx
        self.cy = cy
        self.scroll = scroll
        self.hscroll = hscroll

    @classmethod
    def from_file(cls, path):
        if os.path.exists(path):
            lines = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    lines.append(line.rstrip("\r\n"))
            return cls(path, lines if lines else [""])
        return cls(path, [""])

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
        
        match = re.match(r'^(\s*)', left)
        indent = match.group(1) if match else ""
        
        self.lines[self.cy] = left
        self.lines.insert(self.cy + 1, indent + right)
        self.cy += 1
        self.cx = len(indent)

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

    def home(self):
        self.cx = 0

    def end(self):
        self.cx = len(self.lines[self.cy])

    def adjust_scroll(self, height, width):
        if self.cy < self.scroll:
            self.scroll = self.cy
        elif self.cy >= self.scroll + height:
            self.scroll = self.cy - height + 1

        if self.cx < self.hscroll:
            self.hscroll = self.cx
        elif self.cx >= self.hscroll + width:
            self.hscroll = self.cx - width + 1

def save_chunked(path, buffer):
    with open(path, "w", encoding="utf-8") as f:
        for line in buffer.lines:
            f.write(line + "\n")

def resolve_path(inp):
    home = os.path.expanduser("~")
    return os.path.abspath(os.path.join(home, inp.strip()))

def safe_addstr(stdscr, y, x, text, attr=0):
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    available = max(0, w - x)
    if available <= 0:
        return
    try:
        stdscr.addstr(y, x, text[:available], attr)
    except:
        pass

def draw_highlighted_line(stdscr, y, start_x, line, hscroll, max_w, highlight_enabled):
    visible_line = line[hscroll:]
    if not visible_line:
        return
    if not highlight_enabled:
        safe_addstr(stdscr, y, start_x, visible_line)
        return

    tokens = [(len(visible_line), 0)]
    for pattern, color_idx in SYNTAX_RULES:
        for match in re.finditer(pattern, line):
            start, end = match.start(), match.end()
            v_start = max(0, start - hscroll)
            v_end = max(0, end - hscroll)
            if v_start >= len(visible_line) or v_start == v_end:
                continue
            
            new_tokens = []
            for t_len, t_attr in tokens:
                t_str = visible_line[len(visible_line)-t_len:] if t_len > 0 else ""
                curr_start_idx = len(visible_line) - t_len
                curr_end_idx = curr_start_idx + t_len
                
                if v_end <= curr_start_idx or v_start >= curr_end_idx:
                    new_tokens.append((t_len, t_attr))
                    continue
                
                overlap_start = max(v_start, curr_start_idx)
                overlap_end = min(v_end, curr_end_idx)
                
                if overlap_start > curr_start_idx:
                    new_tokens.append((overlap_start - curr_start_idx, t_attr))
                new_tokens.append((overlap_end - overlap_start, curses.color_pair(color_idx)))
                if overlap_end < curr_end_idx:
                    new_tokens.append((curr_end_idx - overlap_end, t_attr))
            tokens = new_tokens

    curr_x = start_x
    accumulated_len = 0
    for t_len, t_attr in tokens:
        if curr_x - start_x >= max_w:
            break
        chunk = visible_line[accumulated_len:accumulated_len + t_len]
        safe_addstr(stdscr, y, curr_x, chunk, t_attr)
        curr_x += len(chunk)
        accumulated_len += t_len

def search_prompt(stdscr, h, w):
    curses.echo()
    curses.curs_set(1)
    prompt = "Find text: "
    stdscr.attron(curses.color_pair(1))
    stdscr.move(h - 1, 0)
    stdscr.clrtoeol()
    safe_addstr(stdscr, h - 1, 0, prompt, curses.color_pair(1))
    stdscr.refresh()
    try:
        search_bytes = stdscr.getstr(h - 1, len(prompt), 60)
        search_str = search_bytes.decode('utf-8', errors='ignore')
    except:
        search_str = ""
    curses.noecho()
    return search_str

def push_history(history_stack, buffer_obj):
    history_stack.append(copy.deepcopy(buffer_obj.lines))
    if len(history_stack) > 100:
        history_stack.pop(0)

def editor(stdscr, original_path):
    curses.raw()
    curses.start_color()
    curses.use_default_colors()
    
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_BLUE, -1)
    curses.init_pair(6, curses.COLOR_RED, -1)
    
    curses.curs_set(1)
    stdscr.keypad(True)

    original_name = os.path.basename(original_path)
    is_python = original_path.lower().endswith('.py')
    
    write_buffer = Buffer.from_file(original_path)
    insert_buffer = Buffer.from_file(original_path)

    mode = "WRITE"
    active = write_buffer
    
    history = []
    push_history(history, active)

    gutter_width = 6

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        if h < 3 or w < 30:
            safe_addstr(stdscr, 0, 0, "Terminal too small.")
            stdscr.refresh()
            continue

        pos_str = f" Ln {active.cy + 1}, Col {active.cx + 1} "
        base_header = f" VIP Editor 1.0.1 | File: {original_name} | Mode: {mode} "
        space_count = max(1, w - len(base_header) - len(pos_str))
        header = base_header + (" " * space_count) + pos_str
        safe_addstr(stdscr, 0, 0, header, curses.color_pair(1))

        visible_height = h - 2
        visible_width = w - gutter_width
        active.adjust_scroll(visible_height, visible_width)

        for i in range(visible_height):
            idx = active.scroll + i
            if idx >= len(active.lines):
                break
            
            line_num_str = f"{idx + 1:>{gutter_width - 2}}  "
            safe_addstr(stdscr, i + 1, 0, line_num_str, curses.color_pair(2))
            
            line = active.lines[idx]
            draw_highlighted_line(stdscr, i + 1, gutter_width, line, active.hscroll, visible_width, is_python)

        menu_space = max(0, w - len(MENU))
        full_menu = MENU + (" " * menu_space)
        safe_addstr(stdscr, h - 1, 0, full_menu, curses.color_pair(1))

        cy = active.cy - active.scroll + 1
        cx = active.cx - active.hscroll + gutter_width

        if 1 <= cy < h - 1 and gutter_width <= cx < w:
            try:
                stdscr.move(cy, cx)
            except:
                pass

        stdscr.refresh()
        key = stdscr.getch()

        if key == 23:
            mode = "WRITE"
            active = write_buffer

        elif key == 5:
            mode = "INSERT"
            insert_buffer = Buffer(
                path=write_buffer.path,
                lines=copy.deepcopy(write_buffer.lines),
                cx=write_buffer.cx,
                cy=write_buffer.cy,
                scroll=write_buffer.scroll,
                hscroll=write_buffer.hscroll
            )
            active = insert_buffer

        elif key == 17:
            break

        elif key == 2:
            if mode == "INSERT":
                save_chunked(original_path, insert_buffer)
                break

        elif key == 25:
            if mode == "INSERT":
                write_buffer = Buffer(
                    path=insert_buffer.path,
                    lines=copy.deepcopy(insert_buffer.lines),
                    cx=insert_buffer.cx,
                    cy=insert_buffer.cy,
                    scroll=insert_buffer.scroll,
                    hscroll=insert_buffer.hscroll
                )
                active = write_buffer
                mode = "WRITE"
                push_history(history, active)

        elif key == 24:
            save_chunked(original_path, write_buffer)
            break

        elif key == 20:
            active = write_buffer
            mode = "WRITE"

        elif key == 7:
            if mode == "INSERT":
                save_chunked(original_path, insert_buffer)
            else:
                save_chunked(original_path, write_buffer)
            break

        elif key == 6:
            query = search_prompt(stdscr, h, w)
            if query:
                found = False
                start_row = active.cy
                start_col = active.cx + 1
                
                for r in range(start_row, len(active.lines)):
                    line = active.lines[r]
                    c = line.find(query, start_col if r == start_row else 0)
                    if c != -1:
                        active.cy = r
                        active.cx = c
                        found = True
                        break
                
                if not found:
                    for r in range(0, start_row + 1):
                        line = active.lines[r]
                        limit = start_col if r == start_row else len(line)
                        c = line.find(query, 0)
                        if c != -1 and c < limit:
                            active.cy = r
                            active.cx = c
                            break

        elif key == 26:
            if len(history) > 1:
                history.pop()
                active.lines = copy.deepcopy(history[-1])
                active.cy = min(active.cy, len(active.lines) - 1)
                active.cx = min(active.cx, len(active.lines[active.cy]))

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            active.backspace()
            if mode != "INSERT":
                push_history(history, active)

        elif key in (10, 13):
            active.newline()
            if mode != "INSERT":
                push_history(history, active)

        elif key == curses.KEY_LEFT:
            active.left()

        elif key == curses.KEY_RIGHT:
            active.right()

        elif key == curses.KEY_UP:
            active.up()

        elif key == curses.KEY_DOWN:
            active.down()

        elif key == curses.KEY_HOME:
            active.home()

        elif key == curses.KEY_END:
            active.end()

        elif 32 <= key <= 126:
            active.insert(chr(key))
            if mode != "INSERT":
                push_history(history, active)

def boot():
    print("========================================")
    print("          Welcome to VIP Editor         ")
    print("========================================")

    path_input = input("File to Create/Edit:\n")
    full_path = resolve_path(path_input)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    if not os.path.exists(full_path):
        with open(full_path, "w", encoding="utf-8") as f:
            pass

    curses.wrapper(editor, full_path)

if __name__ == "__main__":
    boot()
