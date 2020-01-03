"""A simple log file watcher to provide `tail -F` style functionality across multilple
logfiles.  The syntax is simply: `watchlogs --log_files log1.txt,log2.txt,....`

NOTE: We apply a small monkey patch to Pygtail to let us handle decoding errors more
gracefully.
"""

import sys
import time
import math
import argparse
import datetime
import threading
import numpy as np
from pathlib import Path

import colored
import seaborn as sns
from pygtail import Pygtail

import humanize
import psutil


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


def memory_summary():
    vmem = psutil.virtual_memory()
    msg = (
        f">>> Currently using {vmem.percent}% of system memory "
        f"{humanize.naturalsize(vmem.used)}/{humanize.naturalsize(vmem.available)}"
    )
    print(msg)


class Watcher:

    def __init__(self, watched_logs, conserve_resources, heartbeat, verbose=False):
        self._watched_logs = {}
        self.verbose = verbose
        self.heartbeat = heartbeat
        self.conserve_resources = conserve_resources
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

    def watch_log(self, path, watcher_idx, total_watchers):
        with open(path, "r") as f:
            lines = f.read().splitlines()
        self.log_content(path, lines)
        num_digits = int(np.ceil(math.log(total_watchers, 10)))
        if not lines:
            lines = [""]
        latest = {"line": lines[-1], "tic": time.time()}
        while True:
            if self.heartbeat:
                if latest["line"] == lines[-1]:
                    delta = time.time() - latest["tic"]
                    duration = time.strftime('%Hh%Mm%Ss', time.gmtime(delta))
                    watcher_str = f"{watcher_idx}".zfill(num_digits)
                    summary = f"Log {watcher_str}/{total_watchers}"
                    msg = f"\r{summary} has had no update for {duration}"
                    print(msg, end="", flush=True)
            if self.conserve_resources:
                time.sleep(1)
            try:
                for line in self._watched_logs[path]["pygtail"]:
                    lines = [line.rstrip()]
                    self.log_content(path, lines)
                    latest = {"line": lines[-1], "tic": time.time()}
            except FileNotFoundError:
                msg = f"Log at {path} has been removed, exiting watcher thread..."
                print(msg, flush=True)
                sys.exit()

    def run(self):
        if len(self._watched_logs) > 1:
            threads = []
            total = len(self._watched_logs)
            for ii, path in enumerate(self._watched_logs):
                x = threading.Thread(target=self.watch_log, args=(path, ii, total))
                threads.append(x)
                x.start()
            for x in threads:
                x.join()
        else:
            path = list(self._watched_logs.keys())[0]
            self.watch_log(path, watcher_idx=0, total_watchers=1)


def main():
    parser = argparse.ArgumentParser(description="watchlogs tool")
    parser.add_argument("log_files", help="comma-separated list of logfiles to watch")
    parser.add_argument("--pattern",
                        help=("if supplied, --log_files should point to a directory and "
                              "`pattern` will be used to glob for files"))
    parser.add_argument("--conserve_resources", type=int, default=1,
                        help=("if true, add a short sleep between log checks to reduce"
                              "CPU load"))
    parser.add_argument("--heartbeat", type=int, default=1,
                        help=("if true, print out markers showing that the log watching"
                              "is still active"))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if args.pattern:
        msg = "if args.pattern is supplied, args.log_files should point to a directory"
        assert Path(args.log_files).is_dir(), msg
        watched_logs = sorted(list(Path(args.log_files).glob(f"*{args.pattern}")))
        print(f"Found {len(watched_logs)} matching pattern: {args.pattern}")
    else:
        watched_logs = args.log_files.split(",")
    memory_summary()
    Watcher(
        verbose=args.verbose,
        watched_logs=watched_logs,
        heartbeat=args.heartbeat,
        conserve_resources=args.conserve_resources,
    ).run()


if __name__ == "__main__":
    main()
