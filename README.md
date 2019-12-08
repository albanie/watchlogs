## watchlogs

`watchlogs` is a simple python utility (requires >= 3.7) for watching multilpe log files and interleaving their output, in a manner that aims to achieve the functionality of `tail -F`, but with more colour.

### Usage

`watchlogs --log_files /path/to/log1.txt,/path/to/log2.txt,....`

### Installation

Installation can be handled via `pip install watchlogs`.  However, if you prefer to hack around with the source code, it's only a [single file](watchlogs/watchlogs.py).


### Behaviour

`watchlogs` has the following behaviour when `log.txt` is updated (assuming that we have run `watchlogs --log_files log.txt`):

* action (*appending*): `echo "x" >> log.txt` <br>
*outcome*: `x` is printed to screen.

* action (*moving/rotating*): `touch log2.txt ; echo "y" > log2.txt ; mv log2.txt log.txt` <br>
*outcome*: `y` is printed to screen

* *action* (*overwritng in-place*): `echo "z" > log.txt` <br>
*outcome*: `z` is lost

Since I only use the first two actions while logging, this has sufficed for my needs, but the last behaviour is documented for completeness.  It is likely possible to fix this, but it is not trivial to support with the current implementation and in practice it hasn't affected my use-case (watching slurm logs).


### Implementation


`watchlogs` uses the [pyinotify](https://github.com/seb-m/pyinotify) library to monitor OS events.  In particular, it monitors for:

* `IN_ATTRIB` events to handle log rotation (or files being moved onto the current watches).
* `IN_MODIFY` events to detect when new text is added to the file.


The implementation was inspired by this StackOverflow [comment](https://stackoverflow.com/a/5725309).

### Related projects
You may be interested in:
* [pygtail](https://github.com/bgreenlee/pygtail) - this also reads log files that have not been read (but as far as I am aware, only a single log file at a time.)
