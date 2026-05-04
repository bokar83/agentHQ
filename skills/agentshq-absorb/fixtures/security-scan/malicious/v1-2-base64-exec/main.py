# FIXTURE: triggers v1-2 base64/decode-exec pattern
import base64, subprocess
cmd = base64.b64decode("bHMgLWxh").decode()
subprocess.run(cmd, shell=True)
