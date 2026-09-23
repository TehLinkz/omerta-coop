"""Portable Omerta co-op setup and host management. Uses only the bundled runtime."""
import ctypes
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parent
EXE = ROOT / 'runtime' / 'OmertaCoopServer.exe'
LOCAL = ROOT / 'local-settings.json'
DEFAULTS = {'maxed': '1', 'turn_seconds': '0', 'wasd': '1'}

def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else (default or {})

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def read_ini(path):
    if not path.exists():
        return {}
    return dict(line.split('=', 1) for line in path.read_text(encoding='utf-8-sig').splitlines() if '=' in line)

def write_ini(path, data):
    for k, v in data.items():
        if '\n' in str(v) or '\r' in str(v):
            raise ValueError('Settings must be single lines')
    path.write_text(''.join(f'{k}={v}\n' for k, v in data.items()), encoding='utf-8')

def validate_name(name):
    if not 1 <= len(name.encode('utf-8')) <= 40 or any(c in name for c in '\r\n'):
        raise ValueError('Use a player name of 1-40 UTF-8 bytes on one line.')
    return name

def validate_connection(data):
    address = ipaddress.IPv4Address(data['host'])
    if address.is_unspecified or address.is_multicast:
        raise ValueError('Use the host PC address, not a wildcard or multicast address.')
    return str(address)

def powershell(code):
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', code],
                            check=True, capture_output=True, text=True)
    return result.stdout.strip()

def game_closed():
    listing = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq OmertaSteam.exe', '/FO', 'CSV', '/NH'], text=True)
    if 'omertasteam.exe' in listing.lower():
        raise RuntimeError('Close Omerta before changing settings or installing.')

def discover_games(steam_roots=None):
    roots = list(steam_roots or [])
    if steam_roots is None:
        import winreg
        for hive, key, field in [(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                                 (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath'),
                                 (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Valve\Steam', 'InstallPath')]:
            try:
                with winreg.OpenKey(hive, key) as handle:
                    roots.append(Path(winreg.QueryValueEx(handle, field)[0]))
            except OSError: pass
        for env in ('ProgramFiles(x86)', 'ProgramFiles'):
            if os.environ.get(env): roots.append(Path(os.environ[env]) / 'Steam')
    libraries = list(roots)
    for root in roots:
        vdf = Path(root) / 'steamapps/libraryfolders.vdf'
        if vdf.exists():
            paths = re.findall(r'"path"\s+"([^\"]+)"', vdf.read_text(encoding='utf-8', errors='replace'))
            libraries.extend(Path(p.replace('\\\\', '\\')) for p in paths)
    games = []
    for library in libraries:
        apps = Path(library) / 'steamapps'
        folder = 'Omerta'
        manifest = apps / 'appmanifest_208520.acf'
        if manifest.exists():
            match = re.search(r'"installdir"\s+"([^\"]+)"', manifest.read_text(encoding='utf-8', errors='replace'))
            if match: folder = match[1]
        game = (apps / 'common' / folder).resolve()
        if (game / 'OmertaSteam.exe').is_file() and game not in games: games.append(game)
    return games

def game_path():
    local = read_json(LOCAL)
    saved = local.get('game')
    if saved and (Path(saved) / 'OmertaSteam.exe').exists():
        return Path(saved)
    candidates = discover_games()
    path = candidates[0] if len(candidates) == 1 else Path(input('Omerta game folder: ').strip().strip('"'))
    path = path.resolve()
    if not (path / 'OmertaSteam.exe').exists():
        raise ValueError('OmertaSteam.exe not found in that folder.')
    local['game'] = str(path)
    write_json(LOCAL, local)
    return path

def player_settings(game):
    data = read_ini(game / 'OmertaCoop.ini') or read_ini(ROOT / 'OmertaCoop.ini')
    data.setdefault('profile', secrets.token_hex(16))
    data.setdefault('name', 'Player')
    for key, value in DEFAULTS.items():
        data.setdefault(key, value)
    data['smoke'] = '0'
    data['port'] = '50669'
    return data

def configure_client(game, host, token, name, options=None):
    validate_connection({'host': host, 'token': token})
    data = player_settings(game)
    data.update(host=host, token=token, name=validate_name(name))
    for key, value in (options or {}).items():
        if key in DEFAULTS:
            if key == 'turn_seconds' and not 0 <= int(value) <= 3600:
                raise ValueError('Timer must be 0-3600 seconds')
            if key != 'turn_seconds' and str(value) not in ('0', '1'):
                raise ValueError('Invalid game option')
            data[key] = str(value)
    write_ini(ROOT / 'OmertaCoop.ini', data)
    write_ini(game / 'OmertaCoop.ini', data)
    return data

def install():
    game_closed()
    game = game_path()
    data = player_settings(game)
    if not data.get('host'):
        raise ValueError('Run Host or Join setup first.')
    write_ini(ROOT / 'OmertaCoop.ini', data)
    subprocess.run([str(EXE), str(ROOT / 'patch_client.py'), str(game), '--install'], check=True)
    print('Patch installed. Play Windowed.cmd skips Kalypso and opens a 1920x1080 window.')

def choose_adapter():
    mode = input('Connection: 1 = home LAN, 2 = Radmin / ZeroTier [1]: ').strip() or '1'
    if mode not in ('1', '2'):
        raise ValueError('Choose 1 or 2')
    raw = powershell("Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,PrefixLength | ConvertTo-Json -Compress")
    rows = json.loads(raw)
    if isinstance(rows, dict): rows = [rows]
    rows = [r for r in rows if not ipaddress.ip_address(r['IPAddress']).is_loopback
            and not ipaddress.ip_address(r['IPAddress']).is_link_local
            and (ipaddress.ip_address(r['IPAddress']).is_private or r['IPAddress'].startswith('26.'))]
    if mode == '2':
        preferred = [r for r in rows if re.search('radmin|zerotier|tailscale', r['InterfaceAlias'], re.I)]
    else:
        preferred = [r for r in rows if not re.search('radmin|zerotier|tailscale|vmware|virtual|wsl|vethernet', r['InterfaceAlias'], re.I)]
    rows = preferred or rows
    if not rows: raise RuntimeError('No suitable active IPv4 address found.')
    for i, r in enumerate(rows, 1): print(f"{i}. {r['InterfaceAlias']}: {r['IPAddress']}/{r['PrefixLength']}")
    index = int(input('Host interface number [1]: ') or '1') - 1
    if not 0 <= index < len(rows): raise ValueError('Invalid interface number')
    row = rows[index]
    return {'host': row['IPAddress'], 'interface': row['InterfaceAlias'],
            'subnet': str(ipaddress.ip_interface(f"{row['IPAddress']}/{row['PrefixLength']}").network),
            'mode': 'LAN' if mode == '1' else 'VPN'}

def export_invite():
    host = read_json(ROOT / 'host-settings.json')
    client = player_settings(game_path())
    invite = {'host': host['host'], 'mode': host['mode'],
              'options': {k: client[k] for k in DEFAULTS}}
    path = ROOT / f"Connection-{host['mode']}.json"
    write_json(path, invite)
    print(f"Join address: {host['host']}. Optional settings file: {path.name} (no player identity).")

def host_setup():
    game_closed()
    if own_server(): raise RuntimeError('Stop this kit server before changing its network.')
    game = game_path()
    host = choose_adapter()
    current = player_settings(game)
    name = input(f"Player name [{current['name']}]: ").strip() or current['name']
    server = {'token': ''}
    write_json(ROOT / 'server-settings.json', server)
    write_json(ROOT / 'host-settings.json', host)
    configure_client(game, '127.0.0.1', server['token'], name)
    install()
    export_invite()
    start_server()

def join_setup():
    game_closed()
    game = game_path()
    entry = input('Host IP address (or optional Connection-LAN/VPN.json path): ').strip().strip('"')
    invite = read_json(Path(entry)) if entry.lower().endswith('.json') else {'host': entry}
    host = validate_connection(invite)
    name = input(f"Player name [{player_settings(game)['name']}]: ").strip() or player_settings(game)['name']
    configure_client(game, host, '', name, invite.get('options'))
    install()
    print(f'Configured for {host}:50669. Your existing profile ID was retained.')

def change_name():
    game_closed()
    game = game_path()
    data = player_settings(game)
    name = validate_name(input(f"New player name [{data['name']}]: ").strip() or data['name'])
    configure_client(game, data['host'], data['token'], name)
    print('Name changed. Profile ID and saved gang are unchanged.')

def options():
    game_closed()
    game = game_path()
    data = player_settings(game)
    changes = {}
    for key, label in [('turn_seconds', 'Turn seconds (0 = off, 60 = original, 300 = five minutes)'),
                       ('wasd', 'WASD + arrows (1 = on, 0 = original controls)'),
                       ('maxed', 'All unlocked / default level-12 builds (1 = on, 0 = off)')]:
        changes[key] = input(f'{label} [{data[key]}]: ').strip() or data[key]
    configure_client(game, data['host'], data['token'], data['name'], changes)
    if (ROOT / 'host-settings.json').exists(): export_invite()
    print('Settings saved. Both clients must use the same timer. Disabling unlocks does not erase saved progress.')

def own_server():
    path = ROOT / 'server.pid'
    if not path.exists(): return None
    pid = int(path.read_text().strip())
    raw = powershell(f"Get-CimInstance Win32_Process -Filter 'ProcessId={pid}' | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress")
    if not raw: return None
    p = json.loads(raw)
    if (p.get('ExecutablePath') or '').lower() != str(EXE).lower() or 'server.py' not in (p.get('CommandLine') or ''):
        return None
    return pid

def firewall():
    result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                             str(ROOT / 'Host-Firewall.ps1'), '-Elevate'], check=False)
    if result.returncode: raise RuntimeError('Firewall setup did not complete. Server was not started.')

def start_server():
    if own_server(): print('This kit server is already running.'); return
    host = read_json(ROOT / 'host-settings.json')
    if not host: raise ValueError('Run Host setup first.')
    for address in ('127.0.0.1', host['host']):
        with socket.socket() as probe:
            probe.settimeout(0.4)
            if probe.connect_ex((address, 50669)) == 0:
                raise RuntimeError('Port 50669 is already in use. Stop the existing server first; no process was stopped.')
    firewall()
    with (ROOT / 'server.stdout.log').open('ab') as out, (ROOT / 'server.stderr.log').open('ab') as err:
        proc = subprocess.Popen([str(EXE), '-u', str(ROOT / 'server.py'), '--bind', '127.0.0.1', '--bind', host['host']],
                                cwd=ROOT, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW)
    (ROOT / 'server.pid').write_text(str(proc.pid))
    for _ in range(30):
        if proc.poll() is not None: raise RuntimeError('Server exited; see server.stderr.log.')
        with socket.socket() as probe:
            probe.settimeout(0.2)
            if probe.connect_ex((host['host'], 50669)) == 0:
                print(f"Server ready: {host['host']}:50669"); return
        time.sleep(0.1)
    raise RuntimeError('Server startup timed out; see server.stderr.log.')

def stop_server():
    pid = own_server()
    if not pid: print('No server owned by this kit is running.'); return
    subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True, capture_output=True)
    print('Server stopped. Saved state is retained.')

def backup_host():
    if own_server(): raise RuntimeError('Stop the server before backing up its saves.')
    if not (ROOT / 'server-settings.json').exists(): raise ValueError('No host configured.')
    path = ROOT / ('Host-Backup-' + time.strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(3) + '.zip')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
        out.write(ROOT / 'server-settings.json', 'server-settings.json')
        for save in (ROOT / 'state').glob('*.bin'):
            if re.fullmatch('[a-f0-9]{64}\\.bin', save.name): out.write(save, 'state/' + save.name)
    print(f'Host backup: {path.name}. Player IDs remain on each player PC. Keep this backup private.')

def restore_host():
    if own_server(): raise RuntimeError('Stop the server before restoring saves.')
    path = Path(input('Host backup ZIP path: ').strip().strip('"'))
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or 'server-settings.json' not in names:
            raise ValueError('Invalid backup')
        if any(n != 'server-settings.json' and not re.fullmatch(r'state/[a-f0-9]{64}\.bin', n) for n in names):
            raise ValueError('Backup contains unexpected paths')
        if any(info.file_size > 3 * 1024 * 1024 for info in archive.infolist()):
            raise ValueError('Oversize backup entry')
        settings = json.loads(archive.read('server-settings.json'))
        if not isinstance(settings, dict): raise ValueError('Invalid server settings')
        if (ROOT / 'server-settings.json').exists(): backup_host()
        for name in names:
            target = ROOT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    write_json(ROOT / 'server-settings.json', {'token': ''})
    print('Saved gangs restored. Run Host setup to choose this PC network. No token is needed.')

def play(windowed=False):
    game_closed()
    game = game_path()
    if player_settings(game).get('host') == '127.0.0.1' and (ROOT / 'host-settings.json').exists():
        start_server()
    args = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'Start-Omerta.ps1'), '-GameDirectory', str(game)]
    if windowed: args.append('-Windowed')
    subprocess.run(args, check=True)

def check():
    data = player_settings(game_path())
    with socket.create_connection((data['host'], 50669), timeout=5): pass
    print(f"TCP connection successful: {data['host']}:50669")

ACTIONS = {'host': host_setup, 'join': join_setup, 'name': change_name, 'options': options,
           'install': install, 'start': start_server, 'stop': stop_server,
           'backup': backup_host, 'restore': restore_host, 'play': play,
           'windowed': lambda: play(True), 'check': check, 'invite': export_invite}

def main():
    if len(sys.argv) > 1:
        ACTIONS[sys.argv[1]](); return
    keys = list(ACTIONS)
    while True:
        print('\nOmerta private co-op kit - development build')
        labels = ['Host: LAN or Radmin/ZeroTier', 'Join by host IP address', 'Change player name',
                  'Timer / controls / unlock settings', 'Install or update patch', 'Start server', 'Stop server',
                  'Back up host saves', 'Restore host saves', 'Play', 'Play windowed', 'Test connection', 'Export connection settings']
        for i, label in enumerate(labels, 1): print(f'{i}. {label}')
        choice = input('Choose a number, or Q to quit: ').strip()
        if choice.lower() == 'q': return
        try:
            index = int(choice) - 1
            if not 0 <= index < len(keys): raise ValueError('Invalid menu selection')
            ACTIONS[keys[index]]()
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as error:
            print('Could not complete:', error)

if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError) as error:
        print('Could not complete:', error); sys.exit(1)
