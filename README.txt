OMERTA CO-OP v1.5 - STEAM WITH LAN / VPN FALLBACK

This integrates the existing co-op helper with SteamNetworking under Omerta's
real app ID (208520). The earlier two-PC probe confirmed Steam relay delivery.
Steam connection has been reported working by the tester. A full completed
mission is still not confirmed. LAN/Radmin is available in the fallback tab.

HUD AND MAP PINGS
- Patches and options: HUD size Default, 150%, 200%, or 300% of the native size.
  This changes in-game UI only. Larger sizes may overlap on smaller screens.
- Shared map ping: Middle mouse click (default), Alt + left click, or Off.
- In a co-op combat map, click the ground to show a marker for five seconds.
  Pings mark a fixed location, not a tracked enemy. They do not issue orders.
  One marker per player; new pings replace the old one. Cooldown: 0.75 seconds.
- Off disables sending/display locally. HUD size can differ between players.
- Both PCs and the host helper should use v1.5. Use Steam or LAN/VPN.
- HUD buttons, chat, camera locks and single-player/city maps do not send pings.
- Larger HUD confirmed in-game. Native marker appearance on two PCs is unconfirmed.
- Close the game and connection, change options, then Apply selected patches.
- Disable optional patches resets HUD size to Default and turns pings Off.

SETUP ON BOTH PCs
1. Extract the entire ZIP to a new, permanent folder. Keep support and
   steam_appid.txt beside OmertaSteamCoop.exe.
2. Close Omerta and the old Steam connection prototype. Run Steam online on
   separate accounts that each own Omerta.
3. Open OmertaSteamCoop.exe. Check the detected game folder and player name.
4. One player chooses Host; the other chooses Join. The host selects difficulty.
5. Click Initialize Steam. Exchange the displayed IDs and paste the other
   player's ID into Friend's Steam ID. These are IDs, not IP addresses.
6. Click Install / update with Omerta closed.
7. Both click Connect. This applies the selected role/settings again and starts
   the host's helper automatically. Wait for "Steam connection ready" on BOTH
   PCs. Initial relay setup may take 20-60 seconds; the initial timeout is 120.
8. Click Play on each PC, then open Multiplayer. Start with Quick Match and the
   same mission, such as Bank Heist. Keep this launcher open for the whole game.

Radmin/ZeroTier is not required for this transport. To verify independence,
disconnect it on both PCs while leaving Steam and the internet connected.
Relay=1 means Steam reports relay use; Relay=0 means a direct Steam-managed
connection. Both are valid. Relay fallback is enabled, not forced.


PATCHES AND OPTIONS TAB
- Characters: unlock available characters, level 12 and their default perks.
- Weapons: independently unlock all available weapons. Installed DLC applies.
- Camera: turn WASD movement on/off; arrow keys remain available. Alt+W retains
  Defensive Behavior while WASD is enabled.
- Game launch: enable/disable the Kalypso launcher skip.
- Round timer: 0 = unlimited, 60 = original, 300 = five minutes, up to 3600.
  Both players must use the same timer setting.
- Host bot difficulty: Easy, Normal, Hard or Insane; applied to both players.
- Apply selected patches: install the selected on/off settings with game closed.
- Disable optional patches: turn off characters, weapons, WASD and launcher
  skip, restore the 60-second timer and select Normal. Co-op remains installed.
- Restore original game: restore the verified original Lua archive, removing
  the co-op Lua patch. Profiles and host saves remain. HD textures are separate.

Turning unlocks OFF stops future grants and perk rebuilding; it does not remove
levels, weapons or other progress already saved. There is no automatic downgrade
of existing characters. Restore a private pre-unlock host backup if you have one
and need that exact older progress. Campaign saves are not edited.

LAN / RADMIN FALLBACK TAB
Choose Host or Join above the tabs. Host selects Home LAN or Radmin / ZeroTier
and its interface. Join enters the host IP. Click Apply LAN / VPN setup; it
installs the same game options with the fallback connection and starts the host
helper, with Windows administrator approval for its firewall rule when needed.
Test displayed IP checks that selected address, not a stale saved address.
A successful test on the host PC is only local; the guest must test from theirs.
Use Play while the fallback tab is selected. Stop fallback host stops this kit's
owned helper. Steam Connect stops this kit's fallback host before switching.
Both players must already belong to the same LAN or VPN. Router port forwarding
is not configured. Steam remains the default tab; fallback does not require
initializing the Steam connection API. All modes share this build's host saves.

Stop the active Steam connection and close Omerta before changing patches or
switching connection modes. Select settings, then apply them; changing a checkbox
alone does not change the running game.

WHAT CHANGES
Install updates Lua.hpk with the current co-op patch. It preserves the original
archive backup and existing player identity, unlocks, timer and WASD options.
Both players should still use matching turn-timer settings.
The game connects locally: Host uses 127.0.0.1:50670; Join uses 127.0.0.1:50671.
In Steam mode, only the selected peer's packets are accepted and the host
helper binds loopback. No inbound LAN/VPN rule or router forward is needed
for Steam mode. Fallback host setup configures its selected interface firewall.
No original game archives or Steam DLL are included. The installed game's DLL
is loaded. HD texture archives are not changed.

SAVES AND RETURNING TO THE LAN/RADMIN KIT
The game's pre-Steam INI is backed up once as OmertaCoop.ini.before-steam.
Host saves live in THIS build's support/state folder. A separate extracted
build starts with separate host saves; unlocks still apply if enabled.
To transfer existing gangs, stop both helpers and copy the old kit's support/
state folder into this build's support/state before playing. Keep a backup.
Only the host needs these saves. Never give both players the same profile INI.
To return to LAN/Radmin: close Omerta, click Stop and close this launcher; open
the old OmertaCoop.exe, choose the desired Host/Join network, and use Install /
update. That restores the old connection port and settings while retaining ID.

IF IT FAILS
- Wait for both launchers to say ready before opening Multiplayer.
- Use opposite roles and the correct Steam IDs, and close the old probe.
- If a bridge restarts or times out, close Omerta and Stop/Connect on both PCs.
- Stop or closing this window ends the bridge; on Host it also ends this
  launcher's own helper. Other helpers and game processes are not terminated.
- A port-in-use error leaves the existing process alone. Stop the other Steam
  gameplay-test window first; do not run two copies of this build.
- Logs: support/steam-bridge.log and support/steam-server.log. Report both PCs'
  results and where play stopped: login, matching, loading or taking turns.
- Play starts the installed Omerta executable directly while Steam is running.
  Using Steam's own Play button can report "already running" because the bridge
  uses the same app ID. Direct launch has been verified on the development PC.

VALIDATION
The local transport test passed byte-for-byte transfer of 1,048,577 bytes in
each direction through real loopback TCP sockets with a simulated Steam
transport, including reconnect, stale-session rejection and role validation.
The 17 co-op protocol regression tests pass. Setup tests verify role ports,
profile/options preservation and the pre-Steam INI backup.
These tests do not prove native Steam gameplay or combat synchronization.

DEVELOPMENT
Source is in support. Build SteamMain.cs, SteamWindow.cs, SteamTunnel.cs and
SteamProbe.cs together with the .NET Framework C# compiler, /platform:x86
/target:winexe and references System.Windows.Forms, System.Drawing,
System.Web.Extensions. --self-test runs the local tunnel regression test.
Python is bundled. Steam API interface reference:
https://partner.steamgames.com/doc/api/isteamnetworking
This uses the older SteamNetworking005 API and is an unofficial test build.
