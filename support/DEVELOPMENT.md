# Build and tests

The WinForms launcher targets x86 to load the installed game's Steam DLL. The bundled Python helper runs as a separate 64-bit process.

From the repository root in PowerShell:

```powershell
& .\support\Build.ps1
& .\support\runtime\OmertaCoopServer.exe .\support\test_server.py
$test = Start-Process .\OmertaSteamCoop.exe -ArgumentList '--self-test' -Wait -PassThru
Get-Content .\support\tunnel-test.txt
if ($test.ExitCode -ne 0) { throw 'Tunnel test failed' }
```

The tunnel self-test does not initialize Steam or install the game patch. It exercises byte transfer, reconnect, session rejection and role validation with simulated peer transport. Neither it nor the Python protocol tests replaces a two-PC mission test.

## Source

- SteamWindow.cs: UI and helper lifecycle.
- SteamProbe.cs: installed Steam API bindings.
- SteamTunnel.cs: Steam-to-loopback bridge.
- SteamMain.cs: entry point and transport test.
- steam_setup.py: patch options and connection setup.
- manage.py and gui_bridge.py: configuration and LAN/VPN setup.
- server.py and wire.py: host helper and protocol.
- client/zzOmertaCoop.lua: game-side patch.
- patch_client.py: verified original archive backup/install/restore.

Steam host uses loopback port 50670; the joining bridge uses 50671. Fallback uses TCP 50669. Steam packets are accepted only from the selected peer. Lobby/invitation APIs are not implemented.

Never distribute a configured working folder. Exclude saves, INIs, logs, local settings JSON, PID files, test outputs, game archives and Steam DLLs. Retain bundled third-party licenses.
