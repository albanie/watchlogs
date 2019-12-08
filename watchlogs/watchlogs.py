"""A simple log file watcher to provide `tail -F` style functionality across multilple
logfiles.  The syntax is simply: `watchlogs --log_files log1.txt,log2.txt,....`
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


class Watcher:

    def __init__(self, watched_logs, verbose=False):
        self._watched_logs = {}
        self.verbose = verbose
        colors = sns.color_palette("husl", len(watched_logs)).as_hex()

        # read contents of existing logs
        for path, color in zip(watched_logs, colors):
            path = Path(path).resolve()
            if not path.exists():
                with open(path, "w") as f:
                    f.write("")
            self._watched_logs[str(path)] = {
                "color": color,
                "pygtail": Pygtail(str(path))
            }
            # time.sleep(0.1)
            

    def log_content(self, path, lines, last_mod=False):
        color = self._watched_logs[path]["color"]
        for line in lines:
            summary = f"{path} >>> {line}"
            if last_mod:
                summary = f"[stale log] ({last_mod}): {summary}"
            print(colored.stylize(summary, colored.fg(color)), flush=True)
        sys.stdout.flush()

    def watch_log(self, path):
        while True:
            try:
                for line in self._watched_logs[path]["pygtail"]:
                    lines = [line.rstrip()]
                    self.log_content(path, lines)
            except UnicodeDecodeError as error:
                print(f"Skipping line due to decoding failure {error}")

    def run(self):
        threads = []
        for path in self._watched_logs:
            x = threading.Thread(target=self.watch_log, args=(path,))
            threads.append(x)
            x.start()
        for x in threads:
            x.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_files", required=True,
                        help="comma-separated list of logfiles to watch")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    watched_logs = args.log_files.split(",")
    Watcher(watched_logs, verbose=args.verbose).run()


if __name__ == "__main__":
    main()
