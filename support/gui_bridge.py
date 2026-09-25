"""JSON bridge for the desktop launcher. No interactive console prompts."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import manage as m

class HiddenProcess(subprocess.Popen):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)
        kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
        super().__init__(*args, **kwargs)
subprocess.Popen = HiddenProcess

def adapters():
    raw=m.powershell("Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,PrefixLength | ConvertTo-Json -Compress")
    rows=json.loads(raw or '[]')
    if isinstance(rows,dict): rows=[rows]
    return [r for r in rows if not m.ipaddress.ip_address(r['IPAddress']).is_loopback
            and not m.ipaddress.ip_address(r['IPAddress']).is_link_local
            and (m.ipaddress.ip_address(r['IPAddress']).is_private or r['IPAddress'].startswith('26.'))]

def status():
    games=m.discover_games()
    saved=m.read_json(m.LOCAL).get('game','')
    if saved and (Path(saved)/'OmertaSteam.exe').exists():
        if Path(saved) not in games: games.insert(0,Path(saved))
    game=Path(saved) if saved and Path(saved) in games else (games[0] if games else None)
    data=m.read_ini(game/'OmertaCoop.ini') if game else {}
    return {'games':[str(g) for g in games], 'game':str(game) if game else '',
            'settings':data,'host':m.read_json(m.ROOT/'host-settings.json'),
            'adapters':adapters(),'running':bool(m.own_server())}

def dispatch(q):
    action=q['action']
    if action=='status': return status()
    if action=='check':
        address=m.validate_connection({'host':q['address'].strip()})
        print(f'Testing selected address: {address}:50669')
        if q.get('role')=='Host':
            saved=m.read_json(m.ROOT/'host-settings.json').get('host')
            if saved!=address:
                raise ValueError(f'Selected host IP is {address}, but saved host IP is {saved or "not configured"}. Close the game and click Start host to apply the selected network.')
        try:
            with m.socket.create_connection((address,50669),timeout=5): pass
        except OSError as e:
            raise ValueError(f'Cannot reach {address}:50669. Check that the host helper is running on this address and both players have joined the same LAN or VPN network. ({e})') from e
        print(f'TCP connection successful: {address}:50669')
        return {'message':('Local host check passed. Your friend must test this IP from their PC.' if q.get('role')=='Host' else 'Host reachable from this PC. TCP check passed; gameplay is not yet verified.')}
    if action in ('setup','save','start'):
        if action=='start' and q.get('role')!='Host':
            raise ValueError('Choose Host to start a helper. Joining players use Test connection.')
        m.game_closed()
        game=Path(q['game']).resolve()
        if not (game/'OmertaSteam.exe').is_file(): raise ValueError('Choose the folder containing OmertaSteam.exe.')
        name=m.validate_name(q['name'].strip())
        options=q['options']
        if not 0<=int(options['turn_seconds'])<=3600: raise ValueError('Timer must be 0-3600 seconds.')
        if any(str(options[k]) not in ('0','1') for k in ('wasd','maxed')): raise ValueError('Invalid option')
        if options.get('difficulty','normal') not in ('easy','normal','hard','insane'): raise ValueError('Invalid difficulty')
        hosting=q['role']=='Host'
        host=None
        restart=False
        if hosting:
            row=next((r for r in adapters() if r['IPAddress']==q['address'] and r['InterfaceAlias']==q['interface']),None)
            if not row: raise ValueError('Selected network address is no longer available. Refresh networks.')
            host={'host':row['IPAddress'],'interface':row['InterfaceAlias'],
                  'subnet':str(m.ipaddress.ip_interface(str(row['IPAddress'])+'/'+str(row['PrefixLength'])).network),
                  'mode':q['mode']}
            old=m.read_json(m.ROOT/'host-settings.json')
            if old!=host and m.own_server():
                m.stop_server()
                restart=True
            address='127.0.0.1'
        else:
            address=m.validate_connection({'host':q['address'].strip()})
            if m.own_server(): m.stop_server()
        local=m.read_json(m.LOCAL);local['game']=str(game);m.write_json(m.LOCAL,local)
        m.configure_client(game,address,'',name,options)
        if hosting:
            m.write_json(m.ROOT/'host-settings.json',host)
            m.write_json(m.ROOT/'server-settings.json',{'token':'','difficulty':options.get('difficulty','normal')})
            m.export_invite()
        if action=='setup':
            m.install()
        if hosting and (action in ('setup','start') or restart): m.start_server()
        if hosting:
            print(f'Saved host address: {host["host"]}:50669 ({host["interface"]})')
        return {'message':('Host ready at '+host['host']+':50669.' if action=='start' else 'Setup complete.' if action=='setup' else 'Settings saved. Restart the game to apply them.')}
    if action=='restore':
        import unittest.mock
        with unittest.mock.patch('builtins.input',return_value=q['path']): m.restore_host()
    elif action in ('play','windowed','start','stop','backup','check','install'):
        m.ACTIONS[action]()
    else: raise ValueError('Unknown launcher action')
    return {'message':'Completed.'}

if __name__=='__main__':
    log=io.StringIO()
    try:
        q=json.load(sys.stdin)
        with contextlib.redirect_stdout(log): data=dispatch(q)
        result={'ok':True,'data':data,'log':log.getvalue()}
    except Exception as e:
        detail = str(e)
        if isinstance(e, subprocess.CalledProcessError):
            for part in (e.stdout, e.stderr):
                if part: detail += '\n' + (part.decode('utf-8', errors='replace') if isinstance(part,bytes) else part)
        result={'ok':False,'error':detail,'log':log.getvalue()}
    print(json.dumps(result))
