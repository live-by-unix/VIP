#!/usr/bin/env python3
"""VIP Editor - A terminal-based text editor with focus on data safety and performance."""

import curses
import os
import tempfile
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import re
import unicodedata

# Constants
MENU = " ^W Write  ^E Insert  ^Q Quit  ^Y Commit  ^X Save&Exit Wr  ^B Save&Exit Ins  ^T Esc Ins  ^G Save&Exit All  ^F Find  ^Z Undo "
VERSION = "2.0.0"
MAX_HISTORY = 100
HISTORY_SNAPSHOT_THRESHOLD = 50  # Snapshot after N edits in INSERT mode
VIEWPORT_OVERLAP = 256  # Extra chars to highlight around viewport
TAB_SIZE = 4

# Color pair indices
COLOR_HEADER = 1
COLOR_GUTTER = 2
COLOR_KEYWORD = 3
COLOR_NUMBER = 4
COLOR_STRING = 5
COLOR_COMMENT = 6
COLOR_ERROR = 7
COLOR_STATUS = 8


class NewlineStyle(Enum):
    """Supported newline styles."""
    LF = "\n"
    CRLF = "\r\n"
    UNKNOWN = "\n"


class EditorMode(Enum):
    """Editor editing modes."""
    WRITE = "WRITE"
    INSERT = "INSERT"


class OperationType(Enum):
    """Types of undo operations."""
    INSERT_CHAR = "insert_char"
    DELETE_CHAR = "delete_char"
    NEWLINE = "newline"
    BACKSPACE = "backspace"
    PASTE = "paste"
    SNAPSHOT = "snapshot"


@dataclass
class EditorState:
    """Complete editor state for undo/redo."""
    lines: List[str] = field(default_factory=lambda: [""])
    cx: int = 0
    cy: int = 0
    scroll: int = 0
    hscroll: int = 0


class EditorError(Exception):
    """Base exception for editor errors."""
    pass


class FileReadError(EditorError):
    """Raised when file reading fails."""
    pass


class FileWriteError(EditorError):
    """Raised when file writing fails."""
    pass


class TerminalTooSmallError(EditorError):
    """Raised when terminal is too small."""
    pass


# Compiled syntax rules for performance
SYNTAX_RULES: List[Tuple[re.Pattern, int]] = [
    (re.compile(r'\b(def|class|return|if|elif|else|for|while|break|continue|import|from|as|in|is|not|and|or|try|except|raise|with|pass|lambda|None|True|False|async|await|yield|global|nonlocal|assert|finally|del)\b'), COLOR_KEYWORD),
    (re.compile(r'(\b\d+\b|0x[0-9a-fA-F]+|0b[01]+|0o[0-7]+)'), COLOR_NUMBER),
    (re.compile(r'(r?b?u?f?\"[^\"\\]*(?:\\.[^\"\\]*)*\"|r?b?u?f?\'[^\'\\]*(?:\\.[^\'\\]*)*\')'), COLOR_STRING),
    (re.compile(r'(#.*$)'), COLOR_COMMENT),
]


class UndoManager:
    """Manages undo/redo operations with operation-based tracking."""
    
    def __init__(self):
        self.undo_stack: List[EditorState] = []
        self.redo_stack: List[EditorState] = []
        self.pending_edits: int = 0
    
    def push_state(self, state: EditorState) -> None:
        """Push a complete state snapshot."""
        self.undo_stack.append(EditorState(
            lines=list(state.lines),
            cx=state.cx,
            cy=state.cy,
            scroll=state.scroll,
            hscroll=state.hscroll
        ))
        self.redo_stack.clear()
        self._limit_stack()
    
    def _limit_stack(self) -> None:
        """Limit undo stack size."""
        if len(self.undo_stack) > MAX_HISTORY:
            self.undo_stack.pop(0)
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 1
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
    
    def undo(self, current: EditorState) -> EditorState:
        """Undo to previous state."""
        if not self.can_undo():
            return current
        
        # Save current state for redo
        self.redo_stack.append(EditorState(
            lines=list(current.lines),
            cx=current.cx,
            cy=current.cy,
            scroll=current.scroll,
            hscroll=current.hscroll
        ))
        
        # Pop and return previous state
        self.undo_stack.pop()
        prev = self.undo_stack[-1]
        return EditorState(
            lines=list(prev.lines),
            cx=prev.cx,
            cy=prev.cy,
            scroll=prev.scroll,
            hscroll=prev.hscroll
        )
    
    def redo(self, current: EditorState) -> EditorState:
        """Redo to next state."""
        if not self.can_redo():
            return current
        
        next_state = self.redo_stack.pop()
        self.undo_stack.append(EditorState(
            lines=list(next_state.lines),
            cx=next_state.cx,
            cy=next_state.cy,
            scroll=next_state.scroll,
            hscroll=next_state.hscroll
        ))
        return EditorState(
            lines=list(next_state.lines),
            cx=next_state.cx,
            cy=next_state.cy,
            scroll=next_state.scroll,
            hscroll=next_state.hscroll
        )
    
    def record_edit(self) -> None:
        """Record that an edit happened (for INSERT mode batching)."""
        self.pending_edits += 1
    
    def should_snapshot(self) -> bool:
        """Check if we should take a snapshot in INSERT mode."""
        return self.pending_edits >= HISTORY_SNAPSHOT_THRESHOLD
    
    def reset_pending(self) -> None:
        """Reset pending edit counter."""
        self.pending_edits = 0


class Buffer:
    """Text buffer with line-based storage."""
    
    def __init__(self, path: Optional[str] = None, lines: Optional[List[str]] = None,
                 cx: int = 0, cy: int = 0, scroll: int = 0, hscroll: int = 0,
                 newline_style: NewlineStyle = NewlineStyle.LF):
        self.path = path
        self.lines = lines if lines else [""]
        self.cx = cx
        self.cy = cy
        self.scroll = scroll
        self.hscroll = hscroll
        self.newline_style = newline_style
        self.modified = False
    
    @classmethod
    def from_file(cls, path: str) -> 'Buffer':
        """Load buffer from file with proper error handling."""
        if not os.path.exists(path):
            return cls(path, [""], newline_style=NewlineStyle.LF)
        
        lines = []
        newline_style = NewlineStyle.LF
        
        try:
            with open(path, "rb") as f:
                content = f.read()
            
            # Detect newline style
            if b"\r\n" in content:
                newline_style = NewlineStyle.CRLF
            
            # Decode with UTF-8, fallback to latin-1
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
            
            # Split while preserving empty lines
            if text:
                lines = text.splitlines()
                # Handle file without trailing newline
                if not text.endswith('\n') and lines:
                    pass  # Already correct
                elif text == '':
                    lines = ['']
            else:
                lines = ['']
                
        except IOError as e:
            raise FileReadError(f"Cannot read file '{path}': {e}")
        except Exception as e:
            raise FileReadError(f"Error loading file '{path}': {e}")
        
        return cls(path, lines if lines else [""], newline_style=newline_style)
    
    def to_state(self) -> EditorState:
        """Convert to EditorState for undo."""
        return EditorState(
            lines=list(self.lines),
            cx=self.cx,
            cy=self.cy,
            scroll=self.scroll,
            hscroll=self.hscroll
        )
    
    def from_state(self, state: EditorState) -> None:
        """Restore from EditorState."""
        self.lines = list(state.lines)
        self.cx = state.cx
        self.cy = state.cy
        self.scroll = state.scroll
        self.hscroll = state.hscroll
        self._clamp_cursor()
    
    def text(self) -> str:
        """Get full text with original newline style."""
        nl = self.newline_style.value
        return nl.join(self.lines)
    
    def insert(self, ch: str) -> None:
        """Insert character at cursor."""
        if not self.lines:
            self.lines = [""]
        if self.cy >= len(self.lines):
            self.cy = len(self.lines) - 1
        if self.cx > len(self.lines[self.cy]):
            self.cx = len(self.lines[self.cy])
        
        line = self.lines[self.cy]
        self.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
        self.cx += len(ch)
        self.modified = True
    
    def newline(self) -> None:
        """Split line at cursor with auto-indent."""
        if not self.lines:
            self.lines = [""]
        if self.cy >= len(self.lines):
            self.cy = len(self.lines) - 1
        if self.cx > len(self.lines[self.cy]):
            self.cx = len(self.lines[self.cy])
        
        line = self.lines[self.cy]
        left = line[:self.cx]
        right = line[self.cx:]
        
        # Auto-indent
        match = re.match(r'^(\s*)', left)
        indent = match.group(1) if match else ""
        
        self.lines[self.cy] = left
        self.lines.insert(self.cy + 1, indent + right)
        self.cy += 1
        self.cx = len(indent)
        self.modified = True
    
    def backspace(self) -> None:
        """Delete character before cursor or merge lines."""
        if not self.lines:
            self.lines = [""]
        if self.cy >= len(self.lines):
            self.cy = len(self.lines) - 1
        if self.cx > len(self.lines[self.cy]):
            self.cx = len(self.lines[self.cy])
        
        if self.cx > 0:
            line = self.lines[self.cy]
            # Handle multi-byte characters
            if self.cx <= len(line):
                self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
            self.cx = max(0, self.cx - 1)
        elif self.cy > 0:
            prev = self.lines[self.cy - 1]
            current = self.lines[self.cy]
            self.cx = len(prev)
            self.lines[self.cy - 1] = prev + current
            del self.lines[self.cy]
            self.cy -= 1
        self.modified = True
    
    def delete(self) -> None:
        """Delete character at cursor."""
        if not self.lines:
            return
        if self.cy >= len(self.lines):
            self.cy = len(self.lines) - 1
        
        if self.cx < len(self.lines[self.cy]):
            line = self.lines[self.cy]
            self.lines[self.cy] = line[:self.cx] + line[self.cx + 1:]
        elif self.cy < len(self.lines) - 1:
            # Merge with next line
            current = self.lines[self.cy]
            next_line = self.lines[self.cy + 1]
            self.lines[self.cy] = current + next_line
            del self.lines[self.cy + 1]
        self.modified = True
    
    def left(self) -> None:
        """Move cursor left."""
        if self.cx > 0:
            self.cx -= 1
        elif self.cy > 0:
            self.cy -= 1
            self.cx = len(self.lines[self.cy])
        self._clamp_cursor()
    
    def right(self) -> None:
        """Move cursor right."""
        if self.cx < len(self.lines[self.cy]):
            self.cx += 1
        elif self.cy < len(self.lines) - 1:
            self.cy += 1
            self.cx = 0
        self._clamp_cursor()
    
    def up(self) -> None:
        """Move cursor up."""
        if self.cy > 0:
            self.cy -= 1
            self.cx = min(self.cx, len(self.lines[self.cy]))
        self._clamp_cursor()
    
    def down(self) -> None:
        """Move cursor down."""
        if self.cy < len(self.lines) - 1:
            self.cy += 1
            self.cx = min(self.cx, len(self.lines[self.cy]))
        self._clamp_cursor()
    
    def home(self) -> None:
        """Move cursor to start of line."""
        self.cx = 0
    
    def end(self) -> None:
        """Move cursor to end of line."""
        self.cx = len(self.lines[self.cy])
    
    def page_up(self, height: int) -> None:
        """Move up one page."""
        self.cy = max(0, self.cy - height)
        self.cx = min(self.cx, len(self.lines[self.cy]))
        self._clamp_cursor()
    
    def page_down(self, height: int) -> None:
        """Move down one page."""
        self.cy = min(len(self.lines) - 1, self.cy + height)
        self.cx = min(self.cx, len(self.lines[self.cy]))
        self._clamp_cursor()
    
    def _clamp_cursor(self) -> None:
        """Ensure cursor is within valid bounds."""
        if not self.lines:
            self.lines = [""]
        self.cy = max(0, min(self.cy, len(self.lines) - 1))
        self.cx = max(0, min(self.cx, len(self.lines[self.cy])))
    
    def adjust_scroll(self, height: int, width: int) -> None:
        """Adjust scroll position to keep cursor visible."""
        self._clamp_cursor()
        
        # Vertical scroll
        if self.cy < self.scroll:
            self.scroll = self.cy
        elif self.cy >= self.scroll + height:
            self.scroll = self.cy - height + 1
        
        # Horizontal scroll
        if self.cx < self.hscroll:
            self.hscroll = self.cx
        elif self.cx >= self.hscroll + width:
            self.hscroll = self.cx - width + 1


def save_atomic(path: str, buffer: Buffer) -> Tuple[bool, Optional[str]]:
    """Atomically save buffer to file with error handling.
    
    Returns:
        Tuple of (success, error_message)
    """
    if not buffer.lines:
        return True, None
    
    # Create parent directories if needed
    parent_dir = os.path.dirname(path)
    if parent_dir:
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except OSError as e:
            return False, f"Cannot create directory '{parent_dir}': {e}"
    
    # Write to temporary file first
    temp_fd = None
    temp_path = None
    
    try:
        temp_fd, temp_path = tempfile.mkstemp(
            prefix='.vip_temp_',
            dir=os.path.dirname(path) if os.path.dirname(path) else None
        )
        
        nl = buffer.newline_style.value
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            for line in buffer.lines:
                f.write(line + nl)
            f.flush()
            os.fsync(f.fileno())
        
        # Atomic replace
        os.replace(temp_path, path)
        
        buffer.modified = False
        return True, None
        
    except PermissionError as e:
        return False, f"Permission denied writing to '{path}': {e}"
    except OSError as e:
        return False, f"OS error writing to '{path}': {e}"
    except Exception as e:
        return False, f"Unexpected error saving '{path}': {e}"
    finally:
        # Clean up temp file if it still exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass


def resolve_path(inp: str) -> str:
    """Resolve path relative to home directory."""
    home = os.path.expanduser("~")
    return os.path.abspath(os.path.join(home, inp.strip()))


def safe_addstr(stdscr: Any, y: int, x: int, text: str, attr: int = 0) -> None:
    """Safely add string to curses window."""
    h, w = stdscr.getmaxyx()
    if y < 0 or y >= h or x < 0 or x >= w:
        return
    available = w - x
    if available <= 0:
        return
    try:
        stdscr.addstr(y, x, text[:available], attr)
    except curses.error:
        pass


def expand_tabs(line: str, tab_size: int = TAB_SIZE) -> str:
    """Expand tabs to spaces for display."""
    result = []
    col = 0
    for ch in line:
        if ch == '\t':
            spaces = tab_size - (col % tab_size)
            result.append(' ' * spaces)
            col += spaces
        else:
            result.append(ch)
            col += 1
    return ''.join(result)


def get_line_highlighting(line: str, start_col: int, end_col: int) -> List[Tuple[int, int, int]]:
    """Get syntax highlighting for a line segment.
    
    Returns:
        List of (start, end, color_pair) tuples
    """
    if start_col >= end_col:
        return []
    
    # Expand tabs for accurate highlighting
    expanded = expand_tabs(line)
    segment = expanded[start_col:end_col]
    
    if not segment:
        return [(start_col, end_col, 0)]
    
    # Build attribute map for the segment
    attrs = [0] * len(segment)
    
    # Apply rules in order (later rules override earlier ones)
    for pattern, color_idx in SYNTAX_RULES:
        for match in pattern.finditer(expanded):
            m_start, m_end = match.start(), match.end()
            # Check if match overlaps with our segment
            overlap_start = max(m_start, start_col)
            overlap_end = min(m_end, end_col)
            
            if overlap_start < overlap_end:
                # Map to segment coordinates
                seg_start = overlap_start - start_col
                seg_end = overlap_end - start_col
                for i in range(seg_start, seg_end):
                    if 0 <= i < len(attrs):
                        attrs[i] = curses.color_pair(color_idx)
    
    # Compress into runs
    runs = []
    i = 0
    while i < len(attrs):
        attr = attrs[i]
        run_start = i
        while i < len(attrs) and attrs[i] == attr:
            i += 1
        runs.append((start_col + run_start, start_col + i, attr))
    
    return runs


def draw_highlighted_line(stdscr: Any, y: int, start_x: int, line: str,
                         hscroll: int, max_w: int, highlight_enabled: bool) -> None:
    """Draw a single line with syntax highlighting (viewport-only)."""
    if not line:
        return
    
    expanded = expand_tabs(line)
    visible_len = min(len(expanded) - hscroll, max_w)
    
    if visible_len <= 0:
        return
    
    if not highlight_enabled:
        safe_addstr(stdscr, y, start_x, expanded[hscroll:hscroll + max_w])
        return
    
    # Get highlighting for visible portion with overlap
    start_col = max(0, hscroll - VIEWPORT_OVERLAP)
    end_col = min(len(expanded), hscroll + max_w + VIEWPORT_OVERLAP)
    
    runs = get_line_highlighting(expanded, start_col, end_col)
    
    # Draw only visible portion
    for run_start, run_end, attr in runs:
        # Skip if before visible area
        if run_end <= hscroll:
            continue
        # Clip if after visible area
        if run_start >= hscroll + max_w:
            continue
        
        draw_start = max(run_start, hscroll)
        draw_end = min(run_end, hscroll + max_w)
        
        if draw_start < draw_end:
            screen_x = start_x + (draw_start - hscroll)
            text = expanded[draw_start:draw_end]
            safe_addstr(stdscr, y, screen_x, text, attr)


class SearchState:
    """State for search operations."""
    
    def __init__(self):
        self.query = ""
        self.case_sensitive = False
        self.matches: List[Tuple[int, int]] = []  # (line, col)
        self.current_match = -1
    
    def find_all(self, lines: List[str]) -> None:
        """Find all matches in buffer."""
        self.matches = []
        if not self.query:
            return
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(re.escape(self.query), flags)
        except re.error:
            return
        
        for line_idx, line in enumerate(lines):
            for match in pattern.finditer(line):
                self.matches.append((line_idx, match.start()))
    
    def next_match(self, lines: List[str], start_line: int, start_col: int) -> Optional[Tuple[int, int]]:
        """Find next match from position."""
        if not self.query:
            return None
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(re.escape(self.query), flags)
        except re.error:
            return None
        
        # Search forward from current position
        for line_idx in range(start_line, len(lines)):
            line = lines[line_idx]
            search_col = start_col if line_idx == start_line else 0
            match = pattern.search(line, search_col)
            if match:
                return (line_idx, match.start())
        
        # Wrap around
        for line_idx in range(0, start_line + 1):
            line = lines[line_idx]
            limit = start_col if line_idx == start_line else len(line)
            match = pattern.search(line)
            if match and match.start() < limit:
                return (line_idx, match.start())
        
        return None
    
    def prev_match(self, lines: List[str], start_line: int, start_col: int) -> Optional[Tuple[int, int]]:
        """Find previous match from position."""
        if not self.query:
            return None
        
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(re.escape(self.query), flags)
        except re.error:
            return None
        
        # Search backward from current position
        for line_idx in range(start_line, -1, -1):
            line = lines[line_idx]
            matches = list(pattern.finditer(line))
            if matches:
                if line_idx == start_line:
                    # Find match before cursor
                    for match in reversed(matches):
                        if match.start() < start_col:
                            return (line_idx, match.start())
                else:
                    # Last match on line
                    return (line_idx, matches[-1].start())
        
        # Wrap around
        for line_idx in range(len(lines) - 1, start_line - 1, -1):
            line = lines[line_idx]
            matches = list(pattern.finditer(line))
            if matches:
                if line_idx == start_line:
                    for match in reversed(matches):
                        if match.start() >= start_col:
                            return (line_idx, match.start())
                else:
                    return (line_idx, matches[-1].start())
        
        return None


def search_prompt(stdscr: Any, h: int, w: int, initial_query: str = "") -> Tuple[str, bool]:
    """Prompt for search query.
    
    Returns:
        Tuple of (query, case_sensitive)
    """
    curses.echo()
    curses.curs_set(1)
    
    prompt = f"Find: {initial_query}"
    stdscr.move(h - 1, 0)
    stdscr.clrtoeol()
    safe_addstr(stdscr, h - 1, 0, prompt, curses.color_pair(COLOR_HEADER))
    stdscr.refresh()
    
    try:
        search_bytes = stdscr.getstr(h - 1, len(prompt), min(60, w - len(prompt) - 10))
        search_str = search_bytes.decode('utf-8', errors='ignore')
    except Exception:
        search_str = initial_query
    
    curses.noecho()
    return search_str, False


def show_message(stdscr: Any, message: str, color_pair: int = COLOR_STATUS) -> None:
    """Show a status message."""
    h, w = stdscr.getmaxyx()
    safe_addstr(stdscr, h - 1, 0, message.ljust(w)[:w], color_pair)
    stdscr.refresh()


def confirm_quit(stdscr: Any, buffer: Buffer) -> bool:
    """Ask user to confirm quit if modified."""
    if not buffer.modified:
        return True
    
    h, w = stdscr.getmaxyx()
    prompt = "Unsaved changes. Quit anyway? (y/n): "
    safe_addstr(stdscr, h - 1, 0, prompt, curses.color_pair(COLOR_ERROR))
    stdscr.refresh()
    
    try:
        key = stdscr.getch()
        return key in (ord('y'), ord('Y'))
    except Exception:
        return False
    finally:
        stdscr.clrtoeol()


def editor(stdscr: Any, original_path: str) -> None:
    """Main editor loop."""
    curses.raw()
    curses.start_color()
    curses.use_default_colors()
    
    # Initialize color pairs
    curses.init_pair(COLOR_HEADER, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(COLOR_GUTTER, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_KEYWORD, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_NUMBER, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_STRING, curses.COLOR_BLUE, -1)
    curses.init_pair(COLOR_COMMENT, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_ERROR, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(COLOR_STATUS, curses.COLOR_WHITE, curses.COLOR_BLUE)
    
    curses.curs_set(1)
    stdscr.keypad(True)
    
    original_name = os.path.basename(original_path)
    is_python = original_path.lower().endswith('.py')
    
    # Load write buffer
    try:
        write_buffer = Buffer.from_file(original_path)
    except FileReadError as e:
        print(f"Error: {e}")
        return
    
    # Initialize undo manager
    undo_mgr = UndoManager()
    undo_mgr.push_state(write_buffer.to_state())
    
    # Insert buffer (lazy-loaded)
    insert_buffer: Optional[Buffer] = None
    
    mode = EditorMode.WRITE
    active = write_buffer
    
    search_state = SearchState()
    status_message = ""
    status_color = COLOR_STATUS
    
    gutter_width = 6
    
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        
        # Handle terminal too small
        if h < 3 or w < 30:
            safe_addstr(stdscr, 0, 0, "Terminal too small. Press Ctrl+Q to quit.", curses.color_pair(COLOR_ERROR))
            stdscr.refresh()
            
            # Still process quit shortcuts
            try:
                key = stdscr.getch()
                if key == 17:  # ^Q
                    break
                elif key == 3:  # Ctrl+C
                    break
            except Exception:
                pass
            continue
        
        # Modified indicator
        modified_marker = "*" if active.modified else " "
        
        pos_str = f" Ln {active.cy + 1}, Col {active.cx + 1} "
        base_header = f" VIP Editor {VERSION} | {modified_marker} {original_name} | Mode: {mode.value} "
        space_count = max(1, w - len(base_header) - len(pos_str))
        header = base_header + (" " * space_count) + pos_str
        safe_addstr(stdscr, 0, 0, header, curses.color_pair(COLOR_HEADER))
        
        visible_height = h - 2
        visible_width = w - gutter_width
        active.adjust_scroll(visible_height, visible_width)
        
        # Draw content
        for i in range(visible_height):
            idx = active.scroll + i
            if idx >= len(active.lines):
                break
            
            line_num_str = f"{idx + 1:>{gutter_width - 2}}  "
            safe_addstr(stdscr, i + 1, 0, line_num_str, curses.color_pair(COLOR_GUTTER))
            
            line = active.lines[idx]
            draw_highlighted_line(stdscr, i + 1, gutter_width, line,
                                   active.hscroll, visible_width, is_python)
        
        # Draw menu or status
        if status_message:
            menu_space = max(0, w - len(status_message))
            full_menu = status_message + (" " * menu_space)
            safe_addstr(stdscr, h - 1, 0, full_menu, curses.color_pair(status_color))
        else:
            menu_space = max(0, w - len(MENU))
            full_menu = MENU + (" " * menu_space)
            safe_addstr(stdscr, h - 1, 0, full_menu, curses.color_pair(COLOR_HEADER))
        
        # Position cursor
        cy = active.cy - active.scroll + 1
        cx = active.cx - active.hscroll + gutter_width
        
        # Adjust for tab expansion
        if active.cy < len(active.lines):
            line_before_cursor = active.lines[active.cy][:active.cx]
            expanded_before = expand_tabs(line_before_cursor)
            cx = active.hscroll + len(expanded_before) - active.hscroll + gutter_width
            cx = len(expanded_before) - active.hscroll + gutter_width
        
        if 1 <= cy < h - 1 and gutter_width <= cx < w:
            try:
                stdscr.move(cy, cx)
            except curses.error:
                pass
        
        stdscr.refresh()
        
        try:
            key = stdscr.getch()
        except Exception:
            continue
        
        # Clear status on most keys
        if key not in (6, 26):  # Not search or undo
            status_message = ""
        
        # Handle Commands
        if key == 23:  # ^W - Switch to WRITE mode
            mode = EditorMode.WRITE
            active = write_buffer
        
        elif key == 5:  # ^E - Switch to INSERT mode
            mode = EditorMode.INSERT
            # Lazy-create insert buffer
            if insert_buffer is None:
                insert_buffer = Buffer(
                    path=write_buffer.path,
                    lines=list(write_buffer.lines),
                    cx=write_buffer.cx,
                    cy=write_buffer.cy,
                    scroll=write_buffer.scroll,
                    hscroll=write_buffer.hscroll,
                    newline_style=write_buffer.newline_style
                )
            else:
                # Update insert buffer from current write state
                insert_buffer.lines = list(write_buffer.lines)
                insert_buffer.cx = write_buffer.cx
                insert_buffer.cy = write_buffer.cy
                insert_buffer.scroll = write_buffer.scroll
                insert_buffer.hscroll = write_buffer.hscroll
            active = insert_buffer
            undo_mgr.reset_pending()
        
        elif key == 17:  # ^Q - Quit
            if confirm_quit(stdscr, active):
                break
        
        elif key == 2:  # ^B - Save and exit (INSERT mode)
            if mode == EditorMode.INSERT and insert_buffer:
                success, error = save_atomic(original_path, insert_buffer)
                if success:
                    break
                else:
                    status_message = f"Save failed: {error}"
                    status_color = COLOR_ERROR
            elif mode == EditorMode.WRITE:
                success, error = save_atomic(original_path, write_buffer)
                if success:
                    break
                else:
                    status_message = f"Save failed: {error}"
                    status_color = COLOR_ERROR
        
        elif key == 25:  # ^Y - Commit INSERT to WRITE
            if mode == EditorMode.INSERT and insert_buffer:
                write_buffer.lines = list(insert_buffer.lines)
                write_buffer.cx = insert_buffer.cx
                write_buffer.cy = insert_buffer.cy
                write_buffer.scroll = insert_buffer.scroll
                write_buffer.hscroll = insert_buffer.hscroll
                write_buffer.modified = True
                active = write_buffer
                mode = EditorMode.WRITE
                undo_mgr.push_state(write_buffer.to_state())
                status_message = "Changes committed to WRITE buffer"
                status_color = COLOR_STATUS
        
        elif key == 24:  # ^X - Save and exit (WRITE mode)
            success, error = save_atomic(original_path, write_buffer)
            if success:
                break
            else:
                status_message = f"Save failed: {error}"
                status_color = COLOR_ERROR
        
        elif key == 20:  # ^T - Escape INSERT mode
            active = write_buffer
            mode = EditorMode.WRITE
            status_message = "Discarded INSERT changes"
            status_color = COLOR_STATUS
        
        elif key == 7:  # ^G - Save all and exit
            if mode == EditorMode.INSERT and insert_buffer:
                success, error = save_atomic(original_path, insert_buffer)
                if not success:
                    status_message = f"Save failed: {error}"
                    status_color = COLOR_ERROR
                    continue
            else:
                success, error = save_atomic(original_path, write_buffer)
                if not success:
                    status_message = f"Save failed: {error}"
                    status_color = COLOR_ERROR
                    continue
            break
        
        elif key == 6:  # ^F - Find
            query, case_sensitive = search_prompt(stdscr, h, w, search_state.query)
            if query:
                search_state.query = query
                search_state.case_sensitive = case_sensitive
                match = search_state.next_match(active.lines, active.cy, active.cx)
                if match:
                    active.cy, active.cx = match
                    status_message = f"Found: {query}"
                    status_color = COLOR_STATUS
                else:
                    status_message = f"Not found: {query}"
                    status_color = COLOR_ERROR
        
        elif key == 26:  # ^Z - Undo
            if undo_mgr.can_undo():
                prev_state = undo_mgr.undo(active.to_state())
                active.from_state(prev_state)
                status_message = "Undo"
                status_color = COLOR_STATUS
            else:
                status_message = "Nothing to undo"
                status_color = COLOR_ERROR
        
        elif key == 18:  # ^R - Redo
            if undo_mgr.can_redo():
                next_state = undo_mgr.redo(active.to_state())
                active.from_state(next_state)
                status_message = "Redo"
                status_color = COLOR_STATUS
            else:
                status_message = "Nothing to redo"
                status_color = COLOR_ERROR
        
        # Navigation & Mutation
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            active.backspace()
            if mode == EditorMode.WRITE:
                undo_mgr.push_state(active.to_state())
            else:
                undo_mgr.record_edit()
                if undo_mgr.should_snapshot():
                    undo_mgr.push_state(active.to_state())
                    undo_mgr.reset_pending()
        
        elif key == curses.KEY_DC:  # Delete key
            active.delete()
            if mode == EditorMode.WRITE:
                undo_mgr.push_state(active.to_state())
            else:
                undo_mgr.record_edit()
                if undo_mgr.should_snapshot():
                    undo_mgr.push_state(active.to_state())
                    undo_mgr.reset_pending()
        
        elif key in (10, 13):  # Enter
            active.newline()
            if mode == EditorMode.WRITE:
                undo_mgr.push_state(active.to_state())
            else:
                undo_mgr.record_edit()
                if undo_mgr.should_snapshot():
                    undo_mgr.push_state(active.to_state())
                    undo_mgr.reset_pending()
        
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
        
        elif key == curses.KEY_PPAGE:  # Page Up
            active.page_up(visible_height)
        
        elif key == curses.KEY_NPAGE:  # Page Down
            active.page_down(visible_height)
        
        elif key == 9:  # Tab
            active.insert('\t')
            if mode == EditorMode.WRITE:
                undo_mgr.push_state(active.to_state())
            else:
                undo_mgr.record_edit()
                if undo_mgr.should_snapshot():
                    undo_mgr.push_state(active.to_state())
                    undo_mgr.reset_pending()
        
        elif 32 <= key <= 126 or key > 255:  # Printable chars and Unicode
            try:
                ch = chr(key)
                active.insert(ch)
                if mode == EditorMode.WRITE:
                    undo_mgr.push_state(active.to_state())
                else:
                    undo_mgr.record_edit()
                    if undo_mgr.should_snapshot():
                        undo_mgr.push_state(active.to_state())
                        undo_mgr.reset_pending()
            except (ValueError, OverflowError):
                pass  # Invalid character


def boot() -> None:
    """Bootstrap the editor."""
    print("========================================")
    print(f"       Welcome to VIP Editor {VERSION}")
    print("========================================")
    
    path_input = input("File to Create/Edit: ")
    if not path_input.strip():
        print("Invalid file path.")
        return
    
    full_path = resolve_path(path_input)
    
    # Create parent directories if needed
    parent_dir = os.path.dirname(full_path)
    if parent_dir:
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory: {e}")
            return
    
    # Initialize file if it doesn't exist
    if not os.path.exists(full_path):
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                pass
        except OSError as e:
            print(f"Error initializing file: {e}")
            return
    
    try:
        curses.wrapper(editor, full_path)
    except Exception as e:
        print(f"Editor error: {e}")


if __name__ == "__main__":
    boot()
