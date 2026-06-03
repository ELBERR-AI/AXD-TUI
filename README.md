AXD TUI

A lightweight, DOS-style Text User Interface that runs entirely inside your terminal — blue background, white panels, arrow key navigation. Built with Python’s standard library. No pip installs, no dependencies, no desktop required.

Built for Ubuntu. Also works on Debian.

What it looks like

The UI is split into two panels side by side. The left panel is a terminal where you type and run commands. The right panel is a file explorer you navigate with arrow keys. Everything sits on a blue background with white bordered boxes, styled like a classic DOS installer screen. It all runs inside your existing terminal window.

Features

	•	File Explorer — browse your filesystem with arrow keys, open folders, execute files directly
	•	Terminal — full passthrough to your real shell; sudo, vim, ssh, top and any interactive program all work correctly
	•	DOS-style UI — blue background, white panels, fully keyboard-driven
	•	Zero dependencies — uses only Python’s built-in curses module

Requirements

	•	Python 3.6 or newer
	•	Any terminal (gnome-terminal, xterm, tty, ssh session, anything)

That’s it. No pip, no virtualenv, no desktop environment needed.

Running it

Open a terminal and run:

python3 axd.py

Controls

Arrow keys — navigate the file list
Enter — open a folder, execute a file, or run a typed command
Tab — switch between the Terminal and Explorer panels
F7 — create a new directory
F8 — delete the selected file or directory
F10 — quit
Backspace — delete a character in the terminal input

How the terminal works

When you type a command and press Enter, AXD TUI fully suspends and hands control of your terminal directly to the subprocess — stdin, stdout, stderr, all of it. This means sudo password prompts work normally, and interactive programs like vim, nano, top, htop, and ssh all behave exactly as they would in a plain terminal session. Colours and formatting are preserved.

When the command finishes, press Enter to return to the TUI. This is the same technique used by tools like Midnight Commander. The shell=True flag and curses.endwin() call in the source are both intentional for this reason.

The only commands handled inside the TUI without suspending are cd and clear.

Auto-open on login


These methods all work without a desktop environment.

Option A — .bashrc (opens AXD TUI every time you open a terminal)

Add this line to the bottom of your ~/.bashrc file:

python3 /full/path/to/axd.py

Every time you open a terminal, AXD TUI will launch automatically. Press F10 to drop back to a normal shell prompt.

Option B — .bash_profile (runs once on login, works over SSH too)

Add this line to your ~/.bash_profile:

python3 /full/path/to/axd.py

This runs once when you log into a TTY session or connect over SSH.

Option C — systemd user service (automatic launch on login, no interaction needed)

Create the directory ~/.config/systemd/user if it doesn’t exist, then create a file called axd-tui.service inside it and paste in the following:

[Unit]
Description=AXD TUI
After=default.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /full/path/to/axd.py
StandardInput=tty
TTYPath=/dev/tty1
Restart=on-failure

[Install]
WantedBy=default.target

Then run these two commands:

systemctl –user enable axd-tui.service
systemctl –user start axd-tui.service

This will start AXD TUI on tty1 automatically every time you log in.

Compatibility

Ubuntu 20.04 and newer — fully supported
Ubuntu 22.04 and newer — fully supported
Debian 11 (Bullseye) and newer — works
Debian 12 (Bookworm) — works
Other Debian-based distros — likely works, not tested

Requires Python 3.6 or newer. Check yours with python3 –version.
