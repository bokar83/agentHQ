"""Shell entry point for the coordination layer.

Usage:
    python -m skills.coordination.cli with-lock <resource> --ttl <s> -- <cmd> [args...]

Exits 0 on child success, child's exit code on child failure, or 75
(EX_TEMPFAIL) if the lock could not be acquired (something else holds it).
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys

from . import claim, complete

EX_TEMPFAIL = 75


def main() -> int:
    argv = sys.argv[1:]
    if "--" not in argv:
        sys.stderr.write("usage: with-lock <resource> [--ttl N] [--holder S] -- <cmd>...\n")
        return 2
    sep = argv.index("--")
    own_args, child = argv[:sep], argv[sep + 1 :]

    parser = argparse.ArgumentParser(prog="skills.coordination.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("with-lock", help="Run a command while holding a lock")
    p.add_argument("resource")
    p.add_argument("--ttl", type=int, default=1800, help="Seconds (default 1800)")
    p.add_argument("--holder", default=None)

    args = parser.parse_args(own_args)
    if args.cmd != "with-lock":
        parser.error("only with-lock is implemented")
    if not child:
        parser.error("no child command after --")

    holder = args.holder or f"{socket.gethostname()}/pid={os.getpid()}/{child[0]}"
    task = claim(resource=args.resource, holder=holder, ttl_seconds=args.ttl)
    if task is None:
        sys.stderr.write(
            f"coordination.cli: resource '{args.resource}' is held; not running.\n"
        )
        return EX_TEMPFAIL

    try:
        rc = subprocess.call(child)
    finally:
        complete(task["id"])
    return rc


if __name__ == "__main__":
    sys.exit(main())
