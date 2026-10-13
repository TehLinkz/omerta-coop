"""Steam test build setup. Keeps the game identity and original co-op options."""
import contextlib,io,json,sys,subprocess
from pathlib import Path
import manage as m

def options(q):
    opts=q.get('options',{})
    for k in ('maxed','items','wasd'):
        if k in opts and opts[k] not in ('0','1'):raise ValueError('Invalid '+k)
    if 'turn_seconds' in opts and not 0<=int(opts['turn_seconds'])<=3600:raise ValueError('Timer must be 0-3600 seconds')
    return {k:str(v) for k,v in opts.items() if k in ('maxed','items','wasd','turn_seconds')}

def dispatch(q):
    if q['action']=='status':
        games=m.discover_games()
        saved=m.read_json(m.ROOT/'steam-local.json')
        game=Path(saved.get('game',''))
        if not (game/'OmertaSteam.exe').is_file(): game=games[0] if games else None
        cfg=m.read_ini(game/'OmertaCoop.ini') if game else {}
        try:
            import gui_bridge
            adapters=gui_bridge.adapters()
        except Exception: adapters=[]
        return {'games':[str(p) for p in games], 'game':str(game) if game else '',
                'name':cfg.get('name','Player'),'difficulty':cfg.get('difficulty','normal'),
                'role':saved.get('role','Host'),'peer':saved.get('peer',''),
                'options':{k:cfg.get(k,default) for k,default in [('maxed','1'),('items',cfg.get('maxed','1')),('wasd','1'),('turn_seconds','0')]},
                'skip_launcher':saved.get('skip_launcher',True),'adapters':adapters,
                'host':m.read_json(m.ROOT/'host-settings.json'),'client_host':cfg.get('host',''),
                'transport':saved.get('transport','Steam')}
    game=Path(q['game']).resolve()
    if not (game/'OmertaSteam.exe').is_file(): raise ValueError('Choose the Omerta game folder.')
    if q['action'].startswith('fallback_'):
        import gui_bridge
        action=q['action'][9:]
        if action not in ('setup','check','stop','backup','restore'):raise ValueError('Invalid fallback action')
        if action=='stop':m.stop_server();return {'message':'Fallback host stopped.'}
        if action=='backup':m.backup_host();return {'message':'Host saves backed up under support.'}
        if action=='restore':return gui_bridge.dispatch({'action':'restore','path':q['path']})
        request=dict(q,action=action,options=dict(options(q),difficulty=q['difficulty']))
        result=gui_bridge.dispatch(request)
        if action=='setup':
            m.write_json(m.ROOT/'steam-local.json',{**m.read_json(m.ROOT/'steam-local.json'),**{k:q[k] for k in ('game','role','peer')},'transport':'Fallback','skip_launcher':q.get('skip_launcher',True)})
        return result
    if q['action']=='restore_game':
        m.game_closed()
        if m.own_server():m.stop_server()
        subprocess.run([str(m.EXE),str(m.ROOT/'patch_client.py'),str(game),'--restore'],check=True,capture_output=True,text=True)
        m.write_json(m.ROOT/'steam-local.json',{**m.read_json(m.ROOT/'steam-local.json'),'transport':'None'})
        return {'message':'Original Lua archive restored. Co-op patch disabled; profiles and saves retained. Already saved unlocks are not reversed.'}
    if q['action']=='options':
        m.game_closed();opts=options(q)
        data=m.read_ini(game/'OmertaCoop.ini')
        if not data.get('profile'):raise ValueError('Install the co-op patch first.')
        data.update(opts);data['name']=m.validate_name(q['name'])
        if q['difficulty'] not in ('easy','normal','hard','insane'):raise ValueError('Invalid difficulty')
        data['difficulty']=q['difficulty']
        m.write_ini(m.ROOT/'OmertaCoop.ini',data)
        subprocess.run([str(m.EXE),str(m.ROOT/'patch_client.py'),str(game),'--install'],check=True,capture_output=True,text=True)
        if q['role']=='Host':m.write_json(m.ROOT/'server-settings.json',{'token':'','difficulty':q['difficulty']})
        m.write_json(m.ROOT/'steam-local.json',{**m.read_json(m.ROOT/'steam-local.json'),'skip_launcher':q.get('skip_launcher',True)})
        return {'message':'Selected options applied. Disabled unlock options stop future grants; saved progression is retained.'}
    if q['action']=='prepare':
        m.game_closed()
        role=q['role']; difficulty=q['difficulty']
        if role not in ('Host','Join') or difficulty not in ('easy','normal','hard','insane'):raise ValueError('Invalid settings')
        opts=options(q)
        if m.own_server():m.stop_server()
        data=m.player_settings(game)
        data.update(opts)
        backup=game/'OmertaCoop.ini.before-steam'
        if not backup.exists() and (game/'OmertaCoop.ini').exists(): backup.write_bytes((game/'OmertaCoop.ini').read_bytes())
        data.update(host='127.0.0.1',port='50670' if role=='Host' else '50671',token='',name=m.validate_name(q['name']),difficulty=difficulty)
        m.write_ini(m.ROOT/'OmertaCoop.ini',data)
        # Patcher copies this exact INI; manage.install would reset the port.
        subprocess.run([str(m.EXE),str(m.ROOT/'patch_client.py'),str(game),'--install'],check=True,capture_output=True,text=True)
        m.write_json(m.ROOT/'server-settings.json',{'token':'','difficulty':difficulty})
        m.write_json(m.ROOT/'steam-local.json',{**{k:q[k] for k in ('game','role','peer')},'skip_launcher':q.get('skip_launcher',True),'transport':'Steam'})
        return {'message':'Steam game patch installed. Profile, unlock, timer and camera settings preserved.'}
    if q['action']=='play':
        m.game_closed()
        saved=m.read_json(m.ROOT/'steam-local.json')
        if saved.get('transport')=='Fallback' and saved.get('role')=='Host':m.start_server()
        subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(m.ROOT/'Start-Omerta.ps1'),'-GameDirectory',str(game)]+(['-Windowed'] if q.get('windowed') else [])+(['-KeepKalypso'] if not q.get('skip_launcher',True) else []),check=True,capture_output=True,text=True)
        return {'message':'Launch requested.'}
    raise ValueError('Unknown Steam setup action')

if __name__=='__main__':
    log=io.StringIO()
    try:
        with contextlib.redirect_stdout(log): result=dispatch(json.load(sys.stdin))
        answer={'ok':True,'data':result,'log':log.getvalue()}
    except Exception as e:
        answer={'ok':False,'error':str(e),'log':log.getvalue()}
        if isinstance(e,subprocess.CalledProcessError):answer['error']+='\n'+str(e.stdout or '')+str(e.stderr or '')
    print(json.dumps(answer))
