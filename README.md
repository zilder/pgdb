[WIP]

# pgdb

`pgdb` is gdb-like wrapper for `pldebugger`

## Installation

Install pldebugger first

```
git clone http://git.postgresql.org/git/pldebugger.git
cd pldebugger
make install USE_PGXS=1
```

Add following line to `postgresql.conf` file

```
shared_preload_libraries = '$libdir/plugin_debugger'
```

and restart postgres server.

# Using

Run

```
python pgdb.py [-h] [--user <username>] [--database <database_name>] [--func <function_name>]
```

Commands:

* `breakpoint <func_name>` or `b <func_name>` sets breakpoint on function
* `run` or `r` starts waiting until function executes
* `next` or `n` moves to the next line of source code
* `continue` or `c` runs code until next breakpoint or end of function
* `print <var>` or `p <var>` prints variable name
* `list` or `l` prints current function's source code
