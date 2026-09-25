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
