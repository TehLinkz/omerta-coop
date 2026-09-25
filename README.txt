OMERTA CO-OP

Open OmertaCoop.exe. Keep the support folder beside it.
No separate Python installation is needed.

SETUP
The launcher scans Steam and every library listed by Steam for Omerta.
If multiple installations are found, choose one from Game folder.
Browse is available if automatic detection cannot locate the game.

Close Omerta. Choose Host or Join, enter your player name and configure:
- Host: Home LAN or Radmin / ZeroTier, then your network interface.
- Join: enter the host player's IP address.
Click Install / update. Host setup starts the helper and may show a Windows
administrator prompt to configure its firewall rule. No tokens are needed.
Both VPN players must already be in the same Radmin / ZeroTier network.

PLAY AND OPTIONS
Play or Play windowed launches through Steam and skips the Kalypso launcher.
Play windowed defaults to 1920x1080. The host helper starts when needed.
Save settings applies names, unlocks, timer and WASD settings for the next launch.
Timer 0 means off; both players should use the same number of seconds.
Unlocks + level 12 includes available characters, their default perk builds,
and available weapons. This replaces custom perk choices while enabled.
WASD works alongside arrows; Alt+W retains Defensive Behavior.
Changing the player name or network retains the existing profile ID.
Fresh profiles receive the unlocks when the option is enabled.

HOST SAVES
Stop host before Back up saves or Restore saves. Backups are saved in support.
Choose the backup ZIP when restoring. Configure the new host's network afterward.
Host saves are separate from player IDs, which remain in each game's OmertaCoop.ini.
Do not copy one player's INI to the other player's PC.

SHARING
Give other players the clean ZIP, not your configured working folder.
Extract the entire ZIP. Each player needs their own installed Steam game.
Runtime, settings, logs and saves remain in support. Optional console shortcuts
are in support/shortcuts. Technical details and licenses: support/README.txt.

Development build: login and connection tests passed; a full two-player match,
turn timer and camera controls still need real-game confirmation.

BOT DIFFICULTY (HOST CONTROLLED)
Both PCs need at least the difficulty-enabled patch; earlier clients cannot join.
The host chooses Easy, Normal, Hard or Insane and clicks Save settings.
The choice is synchronized to both players before each new match; changing it
never changes an already-started match. The guest's dropdown is disabled.
- Easy: enemy target level is three below the original scaling, minimum 1.
- Normal: original multiplayer enemy scaling.
- Hard: original level scaling, +1 base Toughness and Guts.
- Insane: original levels, +2 Toughness/Guts, +1 Muscle/Finesse/Cunning/Smarts.
Base stat bonuses cap at 10. These are custom co-op presets, not the campaign
selector or changes to AI decision-making. Player characters and allies are unchanged.
Real-game combat balance and synchronization still need a two-PC match test.

CO-OP MAPS (v1.3)
The original maps are Bank Heist, Jailbreak and Aggressive Negotiations.
Escape the Flames is also supported when both players have the expansion.
Unavailable expansion missions are disabled. Random Map now chooses from
the maps available to both players in Quick Match; invitations use the sender's
available maps and check the recipient before accepting the match.

To upgrade, close the game on both PCs. On the host, click Stop host before
extracting the new ZIP over the existing kit, then open OmertaCoop.exe and click
Install / update on both PCs. Keep existing settings and saves in support.
The updated helper accepts older difficulty-enabled clients for base maps only;
both clients and the host helper need this update for Escape the Flames.
Automated matching and relay tests pass; an actual two-PC Escape the Flames
combat session still needs confirmation. This update contains no HD textures.

NETWORK SELECTION FIX (v1.3)
Test connection checks the IP displayed in the launcher. If the selected host
network is not saved, it tells you to close the game and click Start host.
Start host applies the displayed settings before starting the helper.
Saving a changed host network restarts an already-running helper and updates
its firewall rule. Play still uses saved settings: save changes before playing.
A successful test on the host PC is only a local check. The joining player must
test the host IP from their PC; both players must be on the same VPN network.
