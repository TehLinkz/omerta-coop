# Omerta Co-op

A community-made co-op restoration kit and Windows launcher for **Omerta: City of Gangsters** (Steam).

Host on your own PC and invite a friend over LAN, Radmin, or ZeroTier. The C# launcher handles setup, player names, game options and launching, with a bundled runtime so players do not need to install Python separately.

> **Experimental build:** multiplayer login, connection checks and automated protocol tests pass. A complete two-player combat session, turn-timer changes and WASD camera movement still need confirmation in the actual game. This is not an official Kalypso or Haemimont release.

## Features

- Host or join by IP, with no account or token setup.
- Automatic Steam library scanning, including libraries on other drives.
- Select between multiple detected Omerta installations, or browse manually.
- C# graphical launcher with settings and connection checks.
- Launch through Steam with the Kalypso launcher skip.
- Optional 1920x1080 windowed launch.
- Editable player names without changing profile IDs.
- Available multiplayer characters unlocked with character-specific default perk progression toward level 12.
- Available weapons unlocked, including unique variants. Installed DLC availability still applies.
- Host-controlled co-op bot difficulty, synchronized before each match.
- Adjustable turn timer, including unlimited time.
- WASD camera controls alongside the original arrow keys.
- Host save backup and restore.

## Requirements

- Windows 10/11, 64-bit.
- An installed Steam copy of Omerta on each PC.
- Both PCs on the same reachable LAN, or the same Radmin/ZeroTier network.
- Administrator approval when Windows requests it for the host firewall rule.

The patcher supports the verified Steam Lua archive used during development and refuses unknown builds. No original game archives are included.

## Download and start

Download `Omerta-Coop-Kit.zip` from this repository's **Releases**, once available. Extract the entire ZIP to a permanent folder and open **OmertaCoop.exe**. Keep the `support` folder beside it.

If downloading the repository through **Code > Download ZIP**, extract it before launching.

```text
OmertaCoop.exe
README.txt
support/
```

The runtime, patch source, settings, logs and host saves are under `support`. Optional console shortcuts are under `support/shortcuts`.

## Host a game

1. Close Omerta and open the launcher.
2. Confirm the detected game folder and enter your player name.
3. Set **Play as** to **Host**.
4. Select **Home LAN** or **Radmin / ZeroTier**, then the appropriate **Host interface**.
5. Check the displayed **Host IP** and your game options.
6. Click **Install / update**. Accept the Windows administrator prompt for the host firewall rule if shown.
7. Give your friend the displayed IP address.
8. Click **Play** or **Play windowed**, then open Multiplayer.

Keep the host helper running while playing. A lightweight relay runs on the hosting player's PC; no separate dedicated machine is required. The current restoration relays gameplay messages and is not pure peer-to-peer. Direct public internet hosting and router port forwarding are not configured by this kit.

## Join a game

1. Close Omerta and open the launcher on the joining PC.
2. Confirm the game folder and choose your own player name.
3. Set **Play as** to **Join** and enter the host's LAN or VPN address.
4. Use the same turn-timer setting as the host.
5. Click **Install / update**, then **Test connection**.
6. Click **Play** or **Play windowed**, then open Multiplayer.

For an initial test, both players can select Quick Match with the same original co-op mission, such as Bank Heist. A successful connection check confirms reachability, not a completed or synchronized match.

## Co-op maps

| Mission | Requirement |
|---|---|
| Bank Heist | Base game |
| Jailbreak | Base game |
| Aggressive Negotiations | Base game |
| Escape the Flames | The Japanese Incentive expansion on both PCs |

Version 1.3 includes relay support for the existing expansion mission, **Escape the Flames**. Unavailable expansion missions are disabled in the chooser. Quick Match's **Random Map** now selects from maps available to both players, instead of always selecting Bank Heist. Random invitations choose from the sender's available missions and verify that the recipient has the selected mission.

**Upgrade:** close Omerta on both PCs. Click **Stop host** before extracting the new ZIP over the existing kit folder, preserve existing settings/saves under `support`, and click **Install / update** on each PC. This restarts the host with the updated helper. Existing player IDs and saved gangs are retained.

The updated helper accepts older difficulty-enabled clients for the three base missions. Both clients and the helper must be updated for Escape the Flames. Automated matching, expansion checks and message-relay tests pass; a complete two-PC expansion combat session still needs in-game confirmation. HD textures are separate and are not included in this release.

## Launcher buttons

| Button | Action |
|---|---|
| Install / update | Apply the patch and selected Host/Join settings; hosting also starts the helper. |
| Save settings | Save the selected name, connection and options for the next game launch. |
| Play | Launch through Steam with the launcher skip; start the configured host helper if needed. |
| Play windowed | Launch in a 1920x1080 window. |
| Test connection | Test the displayed IP. Host checks flag an unsaved network and distinguish local success from remote reachability. |
| Start host / Stop host | Start host saves the displayed Host settings and starts the helper on that interface. Stop host disconnects players. |
| Back up saves | Create a host backup ZIP under `support`; stop the helper first. |
| Restore saves | Restore a host backup ZIP; stop the helper first. |
| Refresh | Rescan game/network information and reload saved settings, replacing unsaved edits. |
| Browse | Select the game folder manually. |

Close the game before installation or saving client settings. Changing fields alone does not save them: click **Save settings**, **Install / update**, or **Start host**. Saving a changed host network restarts an already-running helper and updates its firewall rule. Play uses saved settings. A successful host-side connection test does not establish that a friend can connect; test from the joining PC too.

## Game options

### Bot difficulty

**Both PCs must install the difficulty-enabled patch. Older clients are rejected at login.**

The host selects a preset and clicks **Save settings** (or **Install / update** when upgrading). The helper sends the selected rules to both players before each new match. Guests cannot override them, and changes do not affect an active match.

| Preset | Enemy changes |
|---|---|
| Easy | Target level three below original scaling, minimum level 1. |
| Normal | Original multiplayer scaling. |
| Hard | Original scaling, plus 1 base Toughness and Guts. |
| Insane | Original scaling, plus 2 Toughness/Guts and 1 Muscle/Finesse/Cunning/Smarts. |

Stat bonuses cap at 10. These custom co-op presets adjust enemy levels/stats, not AI decision-making. Player characters and allies are not modified. Native perk progression caps at level 12, so harder presets use stat bonuses rather than relying on higher levels alone. In-game balance and synchronization still need a complete two-player combat test.

### Other options

**Turn seconds:** `0` disables the timer, `60` selects the original duration, and `300` gives five minutes. Both players should use the same value.

**Unlocks + level 12:** unlocks available multiplayer characters and weapons, and rebuilds each character's default perk progression. This does not grant every possible perk. Custom perk choices are replaced by character defaults on login while this option is enabled. Fresh profiles receive the unlocks too. Disabling it does not undo progression already saved.

**WASD + arrows:** adds camera movement while retaining the arrow keys. **Alt+W** retains Defensive Behavior. The original in-game options label still shows W. Camera locks and chat focus suspend WASD movement.

Campaign saves are not edited by the multiplayer unlock patch.

## Profiles and saves

Player names and profile IDs are separate. Renaming a player, switching LAN/VPN, or joining another host preserves that PC's existing ID.

- The player's ID is stored in the game's `OmertaCoop.ini`.
- Saved multiplayer gangs and equipment are stored in the host's `support/state` folder, keyed by profile ID.
- A different host has separate saves unless host backups are transferred.
- When moving hosts, stop the helper, back up the old host, restore on the new PC, and configure the new network address.
- Do not give both players the same `OmertaCoop.ini`.

Share a clean release ZIP, not your configured working folder.

## Troubleshooting

**Game not detected:** click Refresh, inspect the game dropdown, or use Browse to select the folder containing `OmertaSteam.exe`.

**Connection fails or login times out:** keep the host helper running, confirm the IP and selected interface, and check that both PCs can reach each other. LAN client isolation or blocking firewall rules can prevent connections even on the same subnet. Radmin/ZeroTier requires both players to join the same VPN network.

**Unknown game build:** the patcher intentionally stops without overwriting the archive. Report the game version and error.

**Need to restore the original patch archive?** With the game closed, run this from the kit folder in PowerShell:

```powershell
& .\support\runtime\OmertaCoopServer.exe .\support\patch_client.py "YOUR GAME FOLDER" --restore
```

The original archive backup is `Packs/Lua.hpk.omerta-coop-original`.

## Development

The C# WinForms source is `support/Launcher.cs`. The GUI calls `gui_bridge.py`, which uses the shared setup logic in `manage.py`. The host protocol implementation is in `server.py` and `wire.py`; the game-side patch is `client/zzOmertaCoop.lua`.

Run protocol tests from the kit folder:

```powershell
& .\support\runtime\OmertaCoopServer.exe .\support\test_server.py
```

Build the launcher on Windows with the .NET Framework compiler:

```powershell
$csc = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
& $csc /nologo /target:winexe /out:OmertaCoop.exe /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll .\support\Launcher.cs
```

## Third-party components

- [HPK v0.3.12](https://github.com/nickelc/hpk): archive tool; GPLv3 license included at `support/tools/LICENSE`. Upstream source is available from the linked repository.
- [Python 3.13.15](https://www.python.org/downloads/release/python-31315/): official Windows embeddable runtime; license included at `support/runtime/LICENSE.txt`.

Omerta and its game assets belong to their respective owners. This project requires an existing game installation and does not distribute the original game archives.
