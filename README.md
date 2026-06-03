# AXD-TUI

A lightweight, DOS-style Text User Interface for the terminal — blue background, white panels, arrow key navigation. Built entirely with Python’s standard library. No pip installs, no dependencies.

Built for Ubuntu. Also works on Debian.

What it looks like

The UI is split into two panels side by side. The left panel is a terminal where you type commands. The right panel is a file explorer you navigate with arrow keys. Everything sits on a blue background with white bordered boxes, styled like a classic DOS installer screen.

Features

	•	File Explorer — browse your filesystem with arrow keys, open folders, execute files directly
	•	Terminal — full passthrough to your real shell; sudo, vim, ssh, top and any interactive program all work correctly
	•	DOS-style UI — blue desktop, white panels, keyboard-driven
	•	Zero dependencies — uses only Python’s built-in curses module

Requirements

	•	Python 3.6 or newer
	•	A terminal emulator (GNOME Terminal, xterm, Konsole, etc.)

That’s it. No pip, no virtualenv, nothing to install.

Running it

python3 axd.py

Controls

Arrow keys — navigate the file list
Enter — open folder, execute file, or run a command
Tab — switch between Terminal and Explorer panels
F7 — create new directory
F8 — delete selected file or directory
F10 — quit
Backspace — delete a character in the terminal input

How the terminal works

When you type a command and press Enter, the TUI fully suspends and hands your real terminal directly to the subprocess — stdin, stdout, stderr, all of it. This means sudo password prompts work normally, and interactive programs like vim, nano, top, htop, and ssh all work exactly as they would in a regular terminal. Colours and terminal formatting are preserved.

When the command finishes, press Enter to return to the TUI. This is the same technique used by Midnight Commander and other established TUI tools. The shell=True flag and curses.endwin() call are both intentional for this reason.

The only commands handled inside the TUI without suspending are cd and clear.

Auto-open on login

Pick whichever method matches how you log in.

Option A — GNOME Terminal (Ubuntu default)

Open Settings, go to Apps, then Startup Applications. Click Add and fill in the name as AXD TUI, the command as gnome-terminal – python3 /full/path/to/axd.py, and a comment if you want one. Click Save. Replace /full/path/to/axd.py with the actual path on your machine, for example /home/yourname/axd.py.

Option B — .bashrc (opens with every terminal window)

Add the following line to the bottom of your ~/.bashrc file:

python3 /full/path/to/axd.py

This will open AXD TUI every time you open a new terminal window. Press F10 to exit back to a normal shell.

Option C — systemd user service (for headless or advanced setups)

Create the directory ~/.config/systemd/user if it doesn’t exist, then create a file called axd-tui.service inside it. Paste in the following:

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

Then run these two commands to enable and start it:

systemctl –user enable axd-tui.service
systemctl –user start axd-tui.service

Option D — .bash_profile (login shells and SSH sessions)

Add this line to your ~/.bash_profile:

python3 /full/path/to/axd.py

This runs once when you log into a TTY or SSH session.

Compatibility

Ubuntu 20.04 and newer — fully supported
Ubuntu 22.04 and newer — fully supported
Debian 11 (Bullseye) and newer — works
Debian 12 (Bookworm) — works
Other Debian-based distros — likely works, not tested

Requires Python 3.6 or newer. Check your version by running python3 –version in your terminal
