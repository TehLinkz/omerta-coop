# Omerta Co-op v1.5 - HUD scaling and shared map pings

New controls under **Patches and options**:

- **In-game HUD size:** Default, 150%, 200% or 300% of the native size. Each player can choose independently.
- **Shared map ping:** Middle mouse click, Alt + left click, or Off.
- Five-second fixed-location markers in co-op combat, one per player, with a 0.75-second cooldown. Pings do not issue orders or move the camera.
- Clicks over HUD buttons/chat do not send pings. Steam and LAN/VPN use the same helper message.
- **Disable optional patches** also resets HUD size to Default and turns pings Off.

Download **Omerta-Coop-v1.5.zip** and extract the entire ZIP. No separate Python installation is needed.

**Upgrade:** close Omerta and stop the old launcher/helper on both PCs. Extract to a new folder, copying the old host's `support/state` if retaining saved gangs, with a backup. Install/update on both PCs and use the updated host helper. Never share one player's INI with another PC.

**Validation:** the larger HUD was confirmed in-game. 17 protocol tests, 6 setup tests and Lua HUD/ping/input regression checks pass. Native ping appearance on both PCs and a complete synchronized Steam co-op mission remain unconfirmed. Larger HUD sizes may overlap on smaller screens. This is an experimental community release.

All v1.4 Steam, fallback, unlock, timer, difficulty and camera features remain available. Disabling unlocks does not undo saved progression. Steam lobbies/invites and HD textures are not included.
