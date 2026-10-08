import os, hashlib, sys

def sig(root):
    h = hashlib.md5()
    for base, _, files in os.walk(root):
        for f in sorted(f for f in files if not f.endswith('.pyc')):
            p = os.path.join(base, f)
            h.update(os.path.relpath(p, root).encode('utf-8'))
            with open(p, 'rb') as fh:
                h.update(fh.read())
    return h.hexdigest()

base = r'C:\Users\yanqi\Desktop\超临界\GitHub1\ten-question-paper-reader'
paths = [
    r'.agents\skills\ten-question-paper-reader',
    r'.claude\skills\ten-question-paper-reader',
    r'.codex\skills\ten-question-paper-reader',
]
sigs = {}
for p in paths:
    full = os.path.join(base, p)
    n = sum(len(fs) for _, _, fs in os.walk(full))
    sigs[p] = (sig(full), n)
    print(p, '-> files:', n, 'sig:', sigs[p][0])
print('all match:', len({v[0] for v in sigs.values()}) == 1)
