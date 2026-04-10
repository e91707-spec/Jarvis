import subprocess
import sys
import os

os.chdir("C:\\container")
subprocess.Popen(
    [sys.executable, "ui.py"],
    creationflags=0x08000000,
    close_fds=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)