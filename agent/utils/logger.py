import json, sys
class _Log:
    def info(self, obj):
        print(json.dumps(obj), file=sys.stdout, flush=True)
    def error(self, obj):
        print(json.dumps({"level":"error", **obj}), file=sys.stderr, flush=True)
log = _Log()
