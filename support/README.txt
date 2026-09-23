OMERTA PRIVATE CO-OP KIT - DEVELOPMENT BUILD

One package supports hosting and joining over home LAN, Radmin, or ZeroTier.
A lightweight relay runs on the hosting player PC; no separate machine is needed.
This restoration currently relays gameplay messages and is not pure peer-to-peer.
It includes a portable Python 3.13.15 runtime; no Python installation is needed.
Game login and LAN TCP connectivity have been verified. A completed two-player
combat, timer changes, and WASD movement still need real-game validation.

GET STARTED
Extract the entire ZIP to a permanent folder. Each PC needs its own copy of the
tested Steam game. Close Omerta before installation or changing client settings.
Open OmertaCoop.exe in the main folder for setup, names, options, play and backups.
Optional console shortcuts are in support/shortcuts. Supporting files remain in support/.

HOST
Choose Host in OmertaCoop.exe and click Install / update. Choose home LAN or a VPN, then your actual network adapter.
Enter a player name. The setup backs up and patches your game, configures a
restricted firewall rule (Windows administrator prompt), and starts the server.
Send the other player the clean kit ZIP and the host IP shown by setup.
No tokens or accounts are required. support/Connection-LAN/VPN.json is optional and
copies the host address and game options; it contains no player identity.
Keep the host PC and helper running. Play and Play windowed start the
host helper when needed; the Start server menu option can also start it separately.
Play windowed launches the game at 1920x1080 and skips the Kalypso launcher.

JOIN
Choose Join in OmertaCoop.exe, enter the host IP address, and choose your own name.
You can also supply the optional connection settings file instead of an IP. Existing player identity is retained when upgrading an already patched game.
Then launch the game and choose Multiplayer. Both players should try Quick Match
with the same original co-op mission, such as Bank Heist.

LAN / RADMIN / ZEROTIER
The game patch is identical. The host chooses the appropriate address/interface;
the joining PC enters that address. For VPN play, both players must
already belong to the same Radmin/ZeroTier network. Stop the server before rerunning
Host Setup to change networks, then share the new address. Guests
rerun Join Setup with that address. No router port forwarding is configured.

NAMES, IDENTITIES, AND SAVES
The Change player name menu option changes your displayed name without changing your profile ID.
Changing LAN/VPN addresses or joining a different host also preserves your profile ID.
Each PC must have a distinct ID; setup generates one only if none exists.
The ID lives in the game's OmertaCoop.ini. Back up that file privately if moving your
own player to another PC; do not give it to someone else or use it on both players.
Saved gangs/equipment are stored in the host's support/state folder, keyed by that ID.
Your name is not the save key. A different host has separate saved gangs unless
you transfer the host saves using Back up host saves and Restore host saves in the menu.
Stop the server first. Restore keeps a backup of existing host saves and
leaves network configuration for Host Setup on the new PC.

UNLOCKS AND CONTROLS
The Timer / controls / unlock settings menu option changes these options without a new game build:
- maxed=1: unlock available multiplayer characters, rebuild each character's own
  default perk progression toward level 12, and unlock all available weapons.
  Includes unique variants; installed/available DLC rules still apply.
  These are default builds, not every possible perk. Custom perk choices are
  replaced by the character's defaults on login while this option is enabled.
- turn_seconds=0 disables the turn timer. Use 60 for original timing or 300 for
  five minutes. Both PCs must use the same value. A host options change regenerates
  its connection file; the guest can use that file to copy the settings,
  or set the same timer through the menu.
- wasd=1 adds WASD camera movement alongside arrows in combat and district view.
  Alt+W retains Defensive Behavior. Original Options still shows its W label.
  Chat focus and camera locks suspend WASD movement. wasd=0 restores plain W.
- Unlocks apply to a fresh profile too when maxed=1. Disabling the option does not
  undo saved progression. Campaign saves are not edited.

UPDATES / RESTORE
Keep the kit folder in place. Install or update patch in the menu rebuilds from your verified original
game archive. It preserves the original at Packs/Lua.hpk.omerta-coop-original.
The patcher refuses unknown game builds and refuses installation while Omerta runs.
Use the menu to update settings; changing a setting requires restarting the game.
To restore the original game archive, with the game closed run:
support\runtime\OmertaCoopServer.exe support\patch_client.py "YOUR GAME FOLDER" --restore

SHARING
Share the clean Omerta-Coop-Kit.zip, not your configured working folder. Your working
folder gains a player ID, local settings, and host saves. The release ZIP contains
none of those and contains no original Omerta game files. Host backups are private.

DEPENDENCIES
HPK v0.3.12: https://github.com/nickelc/hpk (license: tools/LICENSE).
Official Python embeddable runtime: https://www.python.org/downloads/release/python-31315/
Original download SHA256:
d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf
Python license: runtime/LICENSE.txt. Runtime interpreter is copied as
OmertaCoopServer.exe and its _pth file includes this kit's source directory.

All runtime files, settings, logs, saves and generated backups stay in support/.
