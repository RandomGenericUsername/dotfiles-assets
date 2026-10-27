---
id: REQ-007
title: "Rename the clipboard launcher/autostart/keybind from hypr-pano to clipboard"
kind: requirement
status: proposed
lane: 2
links:
  openspec: none
  bmad: none
worktree: none
branch: none
---

# Rename the clipboard launcher/autostart/keybind from hypr-pano to clipboard

## Requirement

Update the static config corpus for the full clipboard rename owned by
`ags-apps` REQ-009:

- `configs/hypr/autostart.lua` starts `~/.config/ags-clipboard` with the
  `clipboard` instance/log name, not `ags-hypr-pano`;
- `configs/hypr/keybindings.lua` invokes `clipboard-ui`, not `hypr-pano-ui`;
- any desktop entry, comment or config reference to the app's old name is
  updated or removed;
- the provisioned launcher template itself belongs to
  `dotfiles-provision` REQ-008, not this repo.

The runtime clipboard daemon keeps `dotfiles-runtime clipboard`; its data-path
migration is in the runtime ticket.

## Acceptance

- [ ] `rg -n 'hypr-pano|ags-hypr-pano' configs desktop` returns no live app
      reference (historical archive paths excluded and listed).
- [ ] Autostart launches `ags-clipboard` with the `clipboard` instance/log.
- [ ] The keybind invokes `clipboard-ui` with the “Open clipboard history”
      description.
- [ ] `make validate-configs`/`make gates` is green; the asset schema/catalog
      remains valid.
- [ ] The cutover leaves no duplicate autostart/keybind entry.

## Dependencies

- `ags-apps` REQ-009 clipboard pilot.
- `dotfiles-provision` REQ-008 launcher template and install topology.
- `dotfiles-runtime` REQ-002 clipboard data-path migration.

## Evidence

- `configs/hypr/autostart.lua` current `~/.config/ags-hypr-pano` line.
- `configs/hypr/keybindings.lua` current `hypr-pano-ui` line.
- `ags-apps/_bmad-output/initiative-ags-standalone-apps/architecture-standalone-app-contract/architecture-standalone-app-contract.md`
  AD-35.
