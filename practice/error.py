# ---- PATH DEBUG BLOCK ----
import sys, os, unicodedata
from pathlib import Path

TARGET = './audio/싼기타_비싼기타.mp3'

print('[PY]', sys.version)
print('[PLATFORM]', sys.platform)
print('[CWD]', Path.cwd())
try:
    script_path = Path(__file__).resolve()
    print('[__file__]', script_path)
    base_dir = script_path.parent
except NameError:
    print('[__file__] not defined (notebook/REPL)')
    base_dir = Path.cwd()

p_rel = Path(TARGET)
p_abs = (base_dir / p_rel).resolve()
p_nfc = Path(unicodedata.normalize('NFC', str(p_abs)))
p_nfd = Path(unicodedata.normalize('NFD', str(p_abs)))

print('[REL EXISTS]', p_rel.exists())
print('[ABS]', p_abs)
print('[ABS EXISTS]', p_abs.exists())
print('[NFC EXISTS]', p_nfc.exists())
print('[NFD EXISTS]', p_nfd.exists())

audio_dir = p_abs.parent
print('[AUDIO DIR]', audio_dir, 'exists=', audio_dir.exists())
if audio_dir.exists():
    print('[AUDIO DIR LIST]')
    for q in audio_dir.iterdir():
        if q.is_file():
            print('-', repr(q.name))
print('---- END PATH DEBUG ----\n')