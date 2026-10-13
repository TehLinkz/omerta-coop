# Omerta Co-op v1.5

A community co-op restoration launcher for **Omerta: City of Gangsters** on Windows. Connect through Steam, with LAN, Radmin and ZeroTier as fallbacks. No separate Python installation is needed.

**[Download the latest release](https://github.com/TehLinkz/omerta-coop/releases/latest)** | [Release notes](RELEASE-NOTES.md) | [Changelog](CHANGELOG.md) | [Build and tests](support/DEVELOPMENT.md)

**Experimental community release:** two-PC Steam relay connectivity has been tested and a Steam game connection was reported working. A complete synchronized co-op mission has not yet been confirmed. This project is not affiliated with Kalypso, Haemimont or Valve.

## Features

- Steam direct connections or relay fallback using Omerta's own app ID.
- One launcher with Steam, Patches and options, and LAN / Radmin fallback tabs.
- Detection across multiple Steam libraries, manual folder selection and player names.
- Independent character/level 12/default-perk and weapon unlock options.
- In-game HUD size: Default, 150%, 200% or 300% of the native size.
- Shared five-second map pings using middle-click or Alt + left-click.
- Optional WASD alongside arrows, Kalypso launcher skip, and 1920x1080 windowed launch.
- Adjustable round timer, including unlimited time, and host-controlled bot difficulty.
- Apply settings, disable optional patches, or restore the original game Lua archive.

Steam IDs are exchanged manually. Steam friend invites/lobbies, HD textures and translation packs are not included.

## Requirements

- Windows 10/11 64-bit with .NET Framework 4.x.
- An installed Steam copy of Omerta on each PC, with separate Steam accounts/game ownership.
- Steam running online for Steam mode.
- Both players on v1.5 with matching timer settings and compatible installed DLC.

The patcher supports the verified Steam Lua archive used during development and refuses unknown archives. No original game archives or Steam DLL are distributed; the launcher loads the installed game's Steam library.

## Steam setup: both players

1. Download **Omerta-Coop-v1.5.zip** from Releases and extract the entire ZIP into a permanent writable folder. Keep `support` and `steam_appid.txt` beside `OmertaSteamCoop.exe`.
2. Close Omerta and any old launcher/helper. Start Steam and open **OmertaSteamCoop.exe**.
3. Check the detected game folder and enter your player name. One player selects **Host**, the other **Join**.
4. In **Patches and options**, choose unlocks, camera controls, timer and launcher behavior. The host chooses difficulty.
5. On the **Steam** tab, click **Initialize Steam**, exchange the displayed IDs and enter the other player's ID into **Friend's Steam ID**.
6. Click **Install / update** with the game closed. Both players then click **Connect**.
7. Wait for **Steam connection ready** on both PCs. Initial relay setup can take 20-60 seconds; the initial timeout is 120 seconds.
8. Click **Play** in this launcher, then open Multiplayer. For a first test, both select Quick Match and the same mission, such as Bank Heist.

**Keep the launcher open throughout the game.** Closing it or stopping the connection ends the bridge. Use its Play button: Steam's Play button can report that Omerta is already running because the bridge uses the same app ID.

Steam mode needs no inbound LAN firewall rule or router forwarding. `Relay=1` means Steam relay; `Relay=0` means a direct Steam-managed connection. Both are valid. A lightweight helper still runs on the host PC; no separate dedicated server is required.

## Patches and options

Close the game and stop the Steam connection before changing patches. Changing a checkbox alone does not apply it: use **Apply selected patches**, **Install / update**, or the appropriate connection setup action.

| Control | Behavior |
|---|---|
| Characters + level 12 / default perks | Unlocks available multiplayer characters and rebuilds character-specific default perks. Custom perk choices are replaced on login while enabled. |
| All available weapons | Independent weapon unlocks. Installed DLC availability applies. |
| WASD + arrows | Adds WASD movement; arrows remain available. Alt+W retains Defensive Behavior. Chat focus and camera locks suspend movement. |
| Skip Kalypso launcher | Skips the launcher during Play; disable to use its normal Start button. |
| In-game HUD size | Default, 150%, 200% or 300% of native size. Local setting; large sizes may overlap on smaller screens. |
| Shared map ping | Middle mouse click, Alt + left click, or Off. Five-second fixed-location markers in co-op combat. |
| Round timer | 0 = unlimited; 60 = original; 300 = five minutes; maximum 3600. Both players must match. |
| Bot difficulty | Easy, Normal, Hard or Insane; the host's rules apply to both players for new matches. |
| Disable optional patches | Turns off unlocks, WASD, launcher skip and pings; restores HUD Default, timer 60 and difficulty Normal. Co-op stays installed. |
| Restore original game | Restores verified original Lua.hpk, removing the co-op Lua patch. Profiles and host saves remain. |

**Turning unlocks off does not erase saved levels, weapons or perks.** It stops future grants and perk rebuilding. To recover previous progression, restore your own pre-unlock host backup. Campaign saves are not edited by the multiplayer unlock patch.

Difficulty changes enemy levels/stats, not AI decision-making: Easy targets three levels below normal (minimum 1); Normal uses original scaling; Hard adds 1 Toughness/Guts; Insane adds 2 Toughness/Guts and 1 Muscle/Finesse/Cunning/Smarts. Stat bonuses cap at 10.

## Shared map pings

With both PCs and the helper updated to v1.5, middle-click the ground during a co-op combat mission to draw a marker on both screens. Choose Alt + left-click or Off under Patches and options if preferred.

Each marker lasts five seconds. Each player has one marker; a new ping replaces it, with a 0.75-second cooldown. It marks a fixed location, not a tracked enemy, and does not issue orders or move the camera. Off disables sending and displaying pings locally. HUD clicks, chat focus and camera locks do not send pings. Single-player and city maps do not send shared pings.

Steam and LAN/VPN use the same message. Automated relay tests pass; a two-PC visual marker test is still pending.

## LAN / Radmin fallback

1. Close the game, stop the Steam connection and select **LAN / Radmin fallback**.
2. Host: select Host, choose Home LAN or Radmin / ZeroTier, and select the correct interface. Join: select Join and enter the host IP.
3. Both click **Apply LAN / VPN setup**. Host setup starts the helper and requests administrator approval for its Windows firewall rule if necessary.
4. The joining player clicks **Test displayed IP**. Success on the host's own PC does not prove remote reachability.
5. Use **Play** with the fallback tab selected. Keep the host helper running; **Stop fallback host** stops it.

Both players must already belong to the same reachable LAN or VPN. The patch does not create VPN memberships or configure router forwarding. The firewall rule is scoped to the bundled helper, TCP 50669 and selected network. Client isolation or other firewall rules can still block access.

## Co-op missions

| Mission | Requirement |
|---|---|
| Bank Heist | Base game |
| Jailbreak | Base game |
| Aggressive Negotiations | Base game |
| Escape the Flames | The Japanese Incentive on both PCs |

Quick Match Random Map selects among missions available to both players. This restores existing co-op missions; it does not add campaign co-op or new maps.

## Upgrade from v1.0-v1.4 and preserve saves

1. Close the game and stop/close old launchers and helpers on both PCs.
2. Extract v1.5 to a **new folder**. Keep the old folder as a backup.
3. To keep existing gangs, copy the old host's `support/state` folder into the new host's `support/state` while both helpers are stopped. Saves are not automatically imported from another kit folder.
4. Open OmertaSteamCoop.exe, review options and follow Steam or fallback setup. Install on both PCs.

The player ID lives in the game's `OmertaCoop.ini`. Renaming or changing networks preserves it. **Never copy one player's INI to the other PC.** Host saves are keyed by profile ID; another host has separate saves unless you transfer the state folder. Both modes in the same kit share that folder.

The original Lua backup is `Packs/Lua.hpk.omerta-coop-original`; first Steam setup also preserves `OmertaCoop.ini.before-steam`. Share the clean ZIP, not your configured working folder.

## Troubleshooting

- **Game not detected:** Browse to the folder containing OmertaSteam.exe.
- **Connection not ready:** check the IDs, opposite roles and both Steam clients. Close the old probe and allow relay setup time.
- **Disconnected/restarted bridge:** close Omerta, then Stop/Connect on both launchers and wait until both are ready.
- **Already running:** use this launcher's Play button, not Steam's.
- **Port in use:** stop the old helper or duplicate launcher. Unrelated processes are left alone.
- **Unknown game build:** installation stops without overwriting an unrecognized archive. Report the error and game version.
- **Bug reports:** include both PCs' results and where it stopped: login, matching, loading or taking turns. Logs are `support/steam-bridge.log` and `support/steam-server.log`. Review private information before sharing; do not upload saves or profile INIs.

## Validation and credits

Automated checks cover the local tunnel, co-op protocol and setup. The tunnel test transfers 1,048,577 bytes each way through real loopback TCP with simulated Steam transport. These checks do not prove completed native combat. Camera direction/speed was manually checked in sandbox city view. The larger HUD was confirmed in-game by the tester. Ping routing, validation and expiry pass automated checks; native marker appearance on both PCs remains unconfirmed.

- Source is under `support`; detailed offline instructions are in README.txt.
- [HPK v0.3.12](https://github.com/nickelc/hpk), GPLv3: `support/tools/LICENSE`.
- Bundled Python: `support/runtime/LICENSE.txt`.
- Steam integration uses the older SteamNetworking005 interface from the installed game.

Omerta and its assets belong to their respective owners.
