# Omerta Co-op v1.4 - Steam and unified launcher

Connect through Steam without requiring Radmin, using **OmertaSteamCoop.exe**. LAN/Radmin/ZeroTier remain in a fallback tab.

- Steam direct/relay transport under Omerta's app ID; manually exchange Steam IDs.
- Separate toggles for characters/level 12/default perks, weapons, WASD and launcher skip.
- Round timer from unlimited to 3600 seconds, plus host bot difficulty.
- Apply patches, disable optional patches, or restore the original Lua archive.
- Direct Play and optional 1920x1080 windowed launch.
- Fallback setup/tests use the selected IP, with scoped host firewall setup.
- Includes previous camera fixes and co-op mission support.

Download **Omerta-Coop-v1.4.zip** and extract the whole ZIP. No separate Python installation is needed. Follow the repository README for both-player setup.

**Upgrading:** stop the old helper and close the game/launcher. Extract into a new folder. Copy the old host's support/state folder if retaining gangs, keeping a backup. Install on both PCs. Never share player INIs.

**Limitations:** disabling unlocks does not undo saved progression. Steam lobbies/invites are not implemented. Steam relay connectivity and a game connection have been reported working, but a full synchronized mission remains unconfirmed. This is an experimental community release. HD textures are not included.
