"""A simple log file watcher to provide `tail -F` style functionality across multilple
logfiles.  The syntax is simply: `watchlogs --log_files log1.txt,log2.txt,....`

"""
import os
import sys
import time
import argparse
from pathlib import Path

import colored
import seaborn as sns
import pyinotify
from pyinotify import IN_ATTRIB, IN_MODIFY


class Watcher(pyinotify.ProcessEvent):

    def __init__(self, watched_logs, verbose=False):
        self._manager = pyinotify.WatchManager()
        self._notify = pyinotify.Notifier(self._manager, self)
        self._watched_logs = {}
        if verbose:
            self.event_mask = pyinotify.ALL_EVENTS
        else:
            self.event_mask = (IN_MODIFY | IN_ATTRIB)
        self.verbose = verbose
        colors = sns.color_palette("husl", len(watched_logs)).as_hex()

        # read contents of existing logs
        for path, color in zip(watched_logs, colors):
            path = str(Path(path).resolve())
            self._watched_logs[path] = {"color": color}
            if Path(path).exists():
                last_mod = time.ctime(os.stat(path).st_mtime)
                with open(path, "r") as f:
                    lines = f.read().splitlines()
                    self.log_content(path=path, lines=lines, last_mod=last_mod)
            else:
                # TODO(Samuel): It seems odd to need to create the file to generate a
                # watch, but for now, this is the only way I can get to to work reliably
                Path(path).touch()
            self._manager.add_watch(path, mask=self.event_mask)
            fh = open(path, 'r')
            fh.seek(0, os.SEEK_END)
            inum = os.fstat(fh.fileno()).st_ino
            self._watched_logs[path].update({"handle": fh, "buffer": "", "inum": inum})

    def log_content(self, path, lines, last_mod=False):
        # print(f"logging {len(lines)} lines from", sys._getframe(1).f_code.co_name)
        color = self._watched_logs[path]["color"]
        for line in lines:
            summary = f"{path} >>> {line}"
            if last_mod:
                summary = f"[stale log] ({last_mod}): {summary}"
            print(colored.stylize(summary, colored.fg(color)))
        sys.stdout.flush()

    def update_log_state(self, path, state):
        if path not in self._watched_logs or state in {"rotate", "refresh"}:
            watch_map = {val.path: key for key, val in self._manager.watches.items()}
            # refresh watch (NOTE: update_watch() doesn't seem to work here)
            self._manager.rm_watch(watch_map[path])
            self._manager.add_watch(path, mask=self.event_mask)
            with open(path, "r") as f:
                print("logging content from update_log_state for ", state)
                self.log_content(
                    path=path,
                    lines=f.read().splitlines(),
                )
            fh = open(path, 'r')
            fh.seek(0, os.SEEK_END)
            inum = os.fstat(fh.fileno()).st_ino
            self._watched_logs[path].update({"handle": fh, "buffer": "", "inum": inum})

    def process_default(self, event):
        """Process any form of inotify event.
        """
        path = str(Path(event.pathname).resolve())
        state = None
        if event.maskname == "IN_ATTRIB":
            state = "rotate"
        elif event.maskname == "IN_MODIFY":
            state = "append"
        self.update_log_state(path, state)
        if state != "append":
            return
        fh, buf = self._watched_logs[path]["handle"], self._watched_logs[path]["buffer"]
        data = fh.read()
        lines = data.split('\n')
        # output previous incomplete line.
        if buf:
            lines[0] = buf + lines[0]
        # only output the last line if it was complete.
        if lines[-1]:
            buf = lines[-1]
        lines.pop()
        self.log_content(path=path, lines=lines)
        self._watched_logs[path]["buffer"] = buf

    def run(self):
        while True:
            self._notify.process_events()
            if self._notify.check_events():
                self._notify.read_events()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_files", required=True,
                        help="comma-separated list of logfiles to watch")
    args = parser.parse_args()
    watched_logs = args.log_files.split(",")
    Watcher(watched_logs).run()


if __name__ == "__main__":
    main()
