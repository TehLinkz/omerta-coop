# Omerta Co-op v1.3 - LAN / Radmin selection fix

Selecting Radmin in the launcher could leave the helper using its saved LAN address. Test connection also used saved settings, so a successful LAN test could appear underneath a selected Radmin IP. This release fixes that mismatch.

- **Test connection** now checks the IP shown in the launcher, instead of silently testing the previously saved address.
- An unsaved Host network produces a clear instruction to apply it with **Start host**.
- **Start host** now saves the displayed settings before starting the helper.
- Saving a changed host network restarts an already-running helper and updates its firewall rule.
- A host-side test is labelled as a local check; your friend must test from their PC to confirm reachability.

## WASD camera correction

- Changed WASD movement to use the same world-coordinate camera function as the game's own movement code, addressing reports of jumping to the map boundary.
- Corrected reversed A/D movement and calibrated zoom-based speed scaling against measured city-view arrow-key movement.
- Added checks for movement distance, Shift speed, diagonal movement, zoom scaling and frame-delay limits.
- This correction requires **Install / update** with Omerta closed. Direction and teleport fixes were confirmed in-game. Final speed calibration matches the measured city zoom; other zoom levels and combat still need comparison.

## Firewall setup

The launcher already includes automatic host firewall setup. **Install / update** and **Start host** configure it when starting the helper; accept the Windows administrator prompt if shown. The rule permits inbound TCP port **50669** for the bundled helper on the selected interface and network range. Changing the saved host network updates the rule when the helper starts. Joining players normally do not need an inbound rule.

Both players must join the same Radmin/ZeroTier network themselves. Firewall setup does not configure the VPN or router port forwarding.

## Updating

Close Omerta and the launcher. Stop the host helper before extracting this ZIP over your existing kit folder; retain existing settings and saves under `support`. Open **OmertaCoop.exe**, select Host and the intended LAN/VPN interface, then click **Install / update** on both PCs. For subsequent network changes, use **Start host** to apply the selected Host settings.

Joining players choose **Join**, enter the host's VPN address, save settings and test the connection. Both players must belong to the same Radmin/ZeroTier network.

Six launcher regression tests pass. The helper's Radmin listener and local connection were verified; remote connectivity and a full multiplayer match still require a second PC.

Includes Escape the Flames support and the Random Map fixes. HD texture work remains paused.
