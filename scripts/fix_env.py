import re
with open('/root/agentsHQ/.env', 'r') as f:
    lines = f.readlines()
fixed = []
count = 0
for line in lines:
    line = line.replace('\r\n', '\n').replace('\r', '\n')
    m = re.match(r'^([A-Z][A-Z0-9_]*)=(.+)$', line.rstrip())
    if m:
        key, val = m.group(1), m.group(2)
        if ' ' in val and not (val.startswith('"') or val.startswith("'")):
            line = f'{key}="{val}"\n'
            count += 1
    fixed.append(line)
with open('/root/agentsHQ/.env', 'w') as f:
    f.writelines(fixed)
print(f'Fixed {count} lines')
