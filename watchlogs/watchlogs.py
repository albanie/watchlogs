"""A simple log file watcher to provide `tail -F` style functionality across multilple
logfiles.  The syntax is simply: `watchlogs --log_files log1.txt,log2.txt,....`

NOTE: We apply a small monkey patch to Pygtail to let us handle decoding errors more
gracefully.
"""

import os
import sys
import time
import argparse
import datetime
import threading
from pathlib import Path

import colored
import seaborn as sns
from pygtail import Pygtail


# =============================================================
#  Monkey patching
# =============================================================

def _get_next_line(self):
    """We catch the Unicode decoding issues and arbitrarily remap decode the bytes
    as latin1.  There isn't much rationale to this.
    """
    curr_offset = self._filehandle().tell()
    try:
        line = self._filehandle().readline()
    except UnicodeDecodeError:
        prev_encoding = self._fh.encoding
        self._fh.reconfigure(encoding="latin1")
        line = self._filehandle().readline()
        self._fh.reconfigure(encoding=prev_encoding)
    if self._full_lines:
        if not line.endswith('\n'):
            self._filehandle().seek(curr_offset)
            raise StopIteration
    if not line:
        raise StopIteration
    self._since_update += 1
    return line


Pygtail._get_next_line = _get_next_line


class Watcher:

    def __init__(self, watched_logs, verbose=False):
        self._watched_logs = {}
        self.verbose = verbose
        colors = sns.color_palette("husl", len(watched_logs)).as_hex()
        self.last_path = None

        # read contents of existing logs
        for path, color in zip(watched_logs, colors):
            path = Path(path).resolve()
            if not path.exists():
                with open(path, "w") as f:
                    f.write("")
            self._watched_logs[str(path)] = {
                "color": color,
                "pygtail": Pygtail(str(path), full_lines=False)
            }

    def log_content(self, path, lines, last_mod=False):
        color = self._watched_logs[path]["color"]
        for line in lines:
            summary = ""
            if path != self.last_path:
                summary += f"{path} >>>\n"
            summary += line
            if last_mod:
                summary = f"[stale log] ({last_mod}): {summary}"
            print(colored.stylize(summary, colored.fg(color)), flush=True)
            self.last_path = path
        sys.stdout.flush()

    def watch_log(self, path):
        with open(path, "r") as f:
            lines = f.read().splitlines()
        self.log_content(path, lines)
        while True:
            for line in self._watched_logs[path]["pygtail"]:
                lines = [line.rstrip()]
                self.log_content(path, lines)

    def run(self):
        if len(self._watched_logs) > 1:
            threads = []
            for path in self._watched_logs:
                x = threading.Thread(target=self.watch_log, args=(path,))
                threads.append(x)
                x.start()
            for x in threads:
                x.join()
        else:
            self.watch_log(list(self._watched_logs.keys())[0])


def main():
    parser = argparse.ArgumentParser(description="watchlogs tool")
    parser.add_argument("log_files", help="comma-separated list of logfiles to watch")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    watched_logs = args.log_files.split(",")
    Watcher(watched_logs, verbose=args.verbose).run()


if __name__ == "__main__":
    main()
