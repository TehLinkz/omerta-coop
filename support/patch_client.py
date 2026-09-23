"""Rebuild an owned Omerta Lua archive; install only with explicit --install."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

EXPECTED = '8e9984b182a6a58fb03d7d7c3ecd4c8f3a9c3481901332590243ac882203f982'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    game = args.game.resolve(strict=True)
    target = game / 'Packs' / 'Lua.hpk'
    backup = game / 'Packs' / 'Lua.hpk.omerta-coop-original'
    if args.install or args.restore:
        listing = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq OmertaSteam.exe', '/FO', 'CSV', '/NH'],
                                 check=True, capture_output=True, text=True)
        if any(row and row[0].lower() == 'omertasteam.exe' for row in csv.reader(listing.stdout.splitlines())):
            raise SystemExit('Exit Omerta before installing or restoring. No game files were changed.')
    if args.restore:
        if not backup.exists() or sha(backup) != EXPECTED:
            raise SystemExit('Verified original backup not found; refusing restore.')
        shutil.copy2(backup, target)
        print('Restored original Lua.hpk. Private settings file was retained.')
        return
    source = backup if backup.exists() else target
    if sha(source) != EXPECTED:
        raise SystemExit('Unknown Lua.hpk build. No changes made; inspect this build before patching.')
    ini = root / 'OmertaCoop.ini'
    if args.install and not ini.exists():
        raise SystemExit('Run Host Setup.cmd or Join Setup.cmd before installation.')
    with tempfile.TemporaryDirectory(prefix='omerta-build-', dir=root) as work:
        work = Path(work)
        tool = str(root / 'tools' / 'hpk.exe')
        subprocess.run([tool, 'extract', str(source), str(work / 'lua')], check=True)
        client_source = (root / 'client' / 'zzOmertaCoop.lua').read_text(encoding='utf-8')
        game_path = game.as_posix() + '/'
        # Forward slashes are accepted by Windows and avoid Lua escape ambiguity.
        client_source = client_source.replace('local install_dir = "" -- OMERTA_INSTALL_DIR',
            'local install_dir = ' + json.dumps(game_path, ensure_ascii=False))
        (work / 'lua' / 'Lua' / 'zzOmertaCoop.lua').write_text(client_source, encoding='utf-8')
        output = root / 'Lua.coop-built.hpk'
        subprocess.run([tool, 'create', str(work / 'lua'), str(output)], check=True)
    if args.install:
        if not backup.exists():
            shutil.copy2(target, backup)
        shutil.copy2(output, target)
        shutil.copy2(ini, game / 'OmertaCoop.ini')
        print('Installed experimental client with verified original backup. Close the game before installation.')
    else:
        print('Built Lua.coop-built.hpk. Game installation unchanged.')
    print('Built SHA-256:', sha(output))


if __name__ == '__main__':
    main()
