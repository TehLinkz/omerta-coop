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
