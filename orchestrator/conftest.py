import sys, pathlib

_orch = pathlib.Path(__file__).parent          # orchestrator/
_root = _orch.parent                           # agentsHQ/

for p in (_root, _orch):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)
