#!/usr/bin/env python3
"""
AXD TUI — DOS-style blue UI
Terminal (left) + File Explorer (right)
Requires: Python 3.6+, stdlib only
Run: python3 axd.py
"""

import curses, os, subprocess, shutil, time, sys
from pathlib import Path

P_BG     = 1
P_PANEL  = 2
P_TITLE  = 3
P_SELECT = 4
P_STATUS = 5
P_DIR    = 6
P_ERR    = 7
P_PROMPT = 8

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(P_BG,     curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(P_PANEL,  curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(P_TITLE,  curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(P_SELECT, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(P_STATUS, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(P_DIR,    curses.COLOR_BLUE,  curses.COLOR_WHITE)
    curses.init_pair(P_ERR,    curses.COLOR_RED,   curses.COLOR_WHITE)
    curses.init_pair(P_PROMPT, curses.COLOR_BLUE,  curses.COLOR_WHITE)

def sa(win, y, x, text, attr=0, clip=None):
    mh, mw = win.getmaxyx()
    if y < 0 or y >= mh or x < 0 or x >= mw:
        return
    if clip is None:
        clip = mw - x - 1
    try:
        win.addstr(y, x, str(text)[:max(0, clip)], attr)
    except curses.error:
        pass

def fill(win, y, x, h, w, attr):
    for i in range(h):
        sa(win, y+i, x, " "*w, attr, w)

def box(win, y, x, h, w, title="", active=False):
    ba = curses.color_pair(P_STATUS)
    ta = curses.color_pair(P_TITLE) | curses.A_BOLD
    fill(win, y, x, h, w, curses.color_pair(P_PANEL))
    sa(win, y,     x, "+" + "-"*(w-2) + "+", ba, w)
    sa(win, y+h-1, x, "+" + "-"*(w-2) + "+", ba, w)
    for i in range(1, h-1):
        sa(win, y+i, x,     "|", ba)
        sa(win, y+i, x+w-1, "|", ba)
    fill(win, y+1, x+1, 1, w-2, ta)
    if title:
        lbl = f" {title} "
        sa(win, y+1, x + max(1,(w-len(lbl))//2), lbl, ta, w-2)
    if active:
        sa(win, y+1, x+w-3, "* ", ta)


# ── Terminal ──────────────────────────────────────────────────────
# Commands run with full stdin/stdout passthrough so sudo, vim,
# ssh, etc. all work normally. We pause curses, run the command,
# then restore curses when done.

class Terminal:
    def __init__(self):
        self.cwd = str(Path.home())
        self.log = []   # (kind, text)  shown between commands
        self.buf = ""
        self.env = os.environ.copy()

    def push(self, kind, text):
        for line in (text.splitlines() or [""]):
            self.log.append((kind, line))

    def run(self, scr, cmd):
        """
        Run cmd with full terminal passthrough.
        Curses is suspended for the duration so interactive
        programs (sudo, ssh, vim, top, etc.) work normally.
        """
        cmd = cmd.strip()
        if not cmd:
            return

        # Handle built-ins inside TUI without suspending
        parts = cmd.split()
        if parts[0] == "cd":
            t = os.path.expanduser(parts[1] if len(parts) > 1 else "~")
            if not os.path.isabs(t):
                t = os.path.join(self.cwd, t)
            try:
                os.chdir(t)
                self.cwd = os.getcwd()
                self.push("output", f"  -> {self.cwd}")
            except Exception as e:
                self.push("error", str(e))
            return

        if parts[0] == "clear":
            self.log.clear()
            return

        # ── Suspend curses, hand terminal to subprocess ──────────
        curses.endwin()

        print(f"\n\033[1;34m{os.path.basename(self.cwd)}\033[0m\033[1m> {cmd}\033[0m")

        try:
            proc = subprocess.run(
                cmd, shell=True,
                cwd=self.cwd,
                env=self.env
                # no capture — stdin/stdout/stderr inherited from process
            )
            if proc.returncode != 0:
                print(f"\033[31m[exit {proc.returncode}]\033[0m")
        except Exception as e:
            print(f"\033[31mError: {e}\033[0m")

        print("\n\033[2m[Press Enter to return to TUI]\033[0m", end="", flush=True)
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

        # ── Restore curses ───────────────────────────────────────
        scr.refresh()
        curses.doupdate()

    def execute_file(self, scr, path):
        ext  = os.path.splitext(path)[1].lower()
        name = os.path.basename(path)
        if ext == ".py":
            cmd = f'python3 "{path}"'
        elif os.access(path, os.X_OK):
            cmd = f'"{path}"'
        else:
            cmd = f'cat "{path}"'
        self.run(scr, cmd)

    def draw(self, win, y, x, h, w, active):
        box(win, y, x, h, w, "Terminal", active)
        inner_w = w - 2
        out_h   = h - 4

        # Show recent log lines
        visible = self.log[-out_h:] if len(self.log) > out_h else self.log
        for i in range(out_h):
            ry = y + 2 + i
            if i < len(visible):
                kind, line = visible[i]
                if kind == "prompt":
                    attr = curses.color_pair(P_PROMPT) | curses.A_BOLD
                elif kind == "error":
                    attr = curses.color_pair(P_ERR)
                else:
                    attr = curses.color_pair(P_PANEL)
                disp = line[:inner_w]
            else:
                attr = curses.color_pair(P_PANEL)
                disp = ""
            sa(win, ry, x+1, disp.ljust(inner_w), attr, inner_w)

        # Input row
        pr_y   = y + h - 2
        prompt = f">{self.buf}"
        sa(win, pr_y, x+1, prompt.ljust(inner_w),
           curses.color_pair(P_PROMPT) | curses.A_BOLD, inner_w)
        cx = x + 1 + len(prompt)
        if active and cx < x + w - 1:
            sa(win, pr_y, cx, "_", curses.color_pair(P_SELECT) | curses.A_BOLD)


# ── File Explorer ─────────────────────────────────────────────────

class Explorer:
    def __init__(self):
        self.cwd    = str(Path.home())
        self.entries= []
        self.cursor = 0
        self.scroll = 0
        self.msg    = ""
        self.refresh()

    def refresh(self):
        self.entries = []
        try:
            raw = sorted(os.listdir(self.cwd),
                         key=lambda e: (not os.path.isdir(os.path.join(self.cwd,e)), e.lower()))
            self.entries = [".."] + raw
        except PermissionError:
            self.msg = "Permission denied"
        self.cursor = min(self.cursor, max(0, len(self.entries)-1))

    def selected_path(self):
        if not self.entries: return None
        name = self.entries[self.cursor]
        return str(Path(self.cwd).parent) if name == ".." else os.path.join(self.cwd, name)

    def enter(self):
        if not self.entries: return None
        name = self.entries[self.cursor]
        if name == "..":
            self.cwd = str(Path(self.cwd).parent)
        else:
            full = os.path.join(self.cwd, name)
            if os.path.isdir(full):
                self.cwd = full
            else:
                return ("file", full)
        self.cursor = 0; self.scroll = 0
        self.refresh()
        return ("dir", self.cwd)

    def draw(self, win, y, x, h, w, active):
        box(win, y, x, h, w, "File Explorer", active)
        inner_w = w - 2
        list_h  = h - 5

        path = self.cwd
        if len(path) > inner_w - 2:
            path = "~" + path[-(inner_w-3):]
        sa(win, y+2, x+1, path.ljust(inner_w), curses.color_pair(P_STATUS), inner_w)

        if self.cursor < self.scroll:
            self.scroll = self.cursor
        if self.cursor >= self.scroll + list_h:
            self.scroll = self.cursor - list_h + 1

        for i in range(list_h):
            ry  = y + 3 + i
            idx = self.scroll + i
            if idx >= len(self.entries):
                sa(win, ry, x+1, " "*inner_w, curses.color_pair(P_PANEL), inner_w)
                continue
            name = self.entries[idx]
            full = os.path.join(self.cwd, name) if name != ".." else str(Path(self.cwd).parent)

            if name == "..":
                icon = "^ "; cp = curses.color_pair(P_DIR) | curses.A_BOLD
            elif os.path.isdir(full):
                icon = "/ "; cp = curses.color_pair(P_DIR) | curses.A_BOLD
            elif os.access(full, os.X_OK):
                icon = "* "; cp = curses.color_pair(P_PANEL) | curses.A_BOLD
            else:
                icon = "  "; cp = curses.color_pair(P_PANEL)

            label = (icon + name)[:inner_w-1]
            if idx == self.cursor:
                cp = curses.color_pair(P_SELECT) | curses.A_BOLD
            sa(win, ry, x+1, label.ljust(inner_w), cp, inner_w)

        hint = self.msg or "Enter=open  F7=mkdir  F8=delete"
        self.msg = ""
        sa(win, y+h-2, x+1, hint[:inner_w].ljust(inner_w), curses.color_pair(P_STATUS), inner_w)


# ── Dialogs ───────────────────────────────────────────────────────

def input_dlg(win, h, w, title, prompt):
    dw = min(50, w-6); dh = 6
    dy = (h-dh)//2;    dx = (w-dw)//2
    box(win, dy, dx, dh, dw, title)
    sa(win, dy+2, dx+2, prompt[:dw-4], curses.color_pair(P_PANEL))
    fw = dw - 4
    sa(win, dy+3, dx+2, " "*fw, curses.color_pair(P_SELECT), fw)
    win.refresh()
    curses.echo(); curses.curs_set(1)
    try:
        win.move(dy+3, dx+2)
        raw = win.getstr(dy+3, dx+2, fw-1)
        result = raw.decode("utf-8","replace").strip()
    except Exception:
        result = None
    curses.noecho(); curses.curs_set(0)
    return result or None

def confirm_dlg(win, h, w, msg):
    dw = min(44, w-6); dh = 5
    dy = (h-dh)//2;    dx = (w-dw)//2
    box(win, dy, dx, dh, dw, "Confirm")
    sa(win, dy+2, dx+2, msg[:dw-4], curses.color_pair(P_ERR)|curses.A_BOLD)
    sa(win, dy+3, dx+2, "Y = yes   any other key = no", curses.color_pair(P_PANEL))
    win.refresh()
    return win.getch() in (ord('y'), ord('Y'))


# ── Bottom bar ────────────────────────────────────────────────────

KEYS = [("Tab","Switch"),("F7","MkDir"),("F8","Delete"),("F10","Quit")]

def draw_bar(win, h, w):
    fill(win, h-1, 0, 1, w, curses.color_pair(P_STATUS))
    x = 1
    for k, lbl in KEYS:
        if x >= w-2: break
        sa(win, h-1, x, k,           curses.color_pair(P_SELECT)|curses.A_BOLD)
        x += len(k)
        seg = f" {lbl}  "
        sa(win, h-1, x, seg,         curses.color_pair(P_STATUS))
        x += len(seg)
    clock = time.strftime("%H:%M:%S")
    sa(win, h-1, w-len(clock)-2, clock, curses.color_pair(P_STATUS)|curses.A_BOLD)


# ── App ───────────────────────────────────────────────────────────

class App:
    TERM = 0; EXP = 1

    def __init__(self, scr):
        self.scr   = scr
        self.focus = self.EXP
        self.term  = Terminal()
        self.exp   = Explorer()
        curses.curs_set(0)
        self.scr.keypad(True)
        self.scr.timeout(1000)
        try:
            init_colors()
        except Exception:
            pass

    def layout(self):
        h, w   = self.scr.getmaxyx()
        term_w = max(24, w // 3)
        exp_w  = w - term_w
        ph     = h - 1
        return h, w, ph, term_w, exp_w

    def draw(self):
        h, w, ph, tw, ew = self.layout()
        self.scr.bkgd(" ", curses.color_pair(P_BG))
        self.scr.erase()
        self.term.draw(self.scr, 0, 0,  ph, tw, self.focus == self.TERM)
        self.exp.draw( self.scr, 0, tw, ph, ew, self.focus == self.EXP)
        draw_bar(self.scr, h, w)
        self.scr.refresh()

    def handle_exp(self, key):
        exp = self.exp
        h, w, ph, tw, ew = self.layout()

        if   key == curses.KEY_UP:    exp.cursor = max(0, exp.cursor - 1)
        elif key == curses.KEY_DOWN:  exp.cursor = min(len(exp.entries)-1, exp.cursor + 1)
        elif key == curses.KEY_PPAGE: exp.cursor = max(0, exp.cursor - (ph-6))
        elif key == curses.KEY_NPAGE: exp.cursor = min(len(exp.entries)-1, exp.cursor + (ph-6))
        elif key == curses.KEY_HOME:  exp.cursor = 0
        elif key == curses.KEY_END:   exp.cursor = len(exp.entries) - 1

        elif key in (curses.KEY_ENTER, 10, 13):
            res = exp.enter()
            if res and res[0] == "file":
                self.term.execute_file(self.scr, res[1])
                self.focus = self.TERM

        elif key == curses.KEY_F7:
            nm = input_dlg(self.scr, h, w, "New Directory", "Name:")
            if nm:
                try:
                    os.makedirs(os.path.join(exp.cwd, nm), exist_ok=True)
                    exp.msg = f"Created: {nm}"
                except Exception as e:
                    exp.msg = str(e)
                exp.refresh()

        elif key == curses.KEY_F8:
            path = exp.selected_path()
            if path and exp.entries[exp.cursor] != "..":
                name = exp.entries[exp.cursor]
                if confirm_dlg(self.scr, h, w, f"Delete {name}?"):
                    try:
                        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
                        exp.cursor = max(0, exp.cursor - 1)
                        exp.msg = f"Deleted: {name}"
                    except Exception as e:
                        exp.msg = str(e)
                    exp.refresh()

    def handle_term(self, key):
        t = self.term
        if key in (curses.KEY_BACKSPACE, 127, 8):
            t.buf = t.buf[:-1]
        elif key in (curses.KEY_ENTER, 10, 13):
            t.run(self.scr, t.buf)
            t.buf = ""
        elif 32 <= key <= 126:
            t.buf += chr(key)

    def run(self):
        while True:
            self.draw()
            key = self.scr.getch()
            if key == -1:
                continue
            if key == curses.KEY_F10:
                break
            elif key == 9:
                self.focus ^= 1
            elif key == curses.KEY_RESIZE:
                self.scr.clear()
            elif self.focus == self.EXP:
                self.handle_exp(key)
            else:
                self.handle_term(key)


def main():
    try:
        curses.wrapper(lambda s: App(s).run())
    except KeyboardInterrupt:
        pass
    print("\nBye!\n")

if __name__ == "__main__":
    main()
