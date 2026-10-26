# Proposal

## Why

The assembled host has `DisplayServer=wayland` and
`GreeterEnvironment=QT_QPA_PLATFORM=wayland`, but the rendered SDDM config has no `[Wayland]`
section. SDDM then relies on its implicit `Wayland.CompositorCommand=weston --shell=kiosk`
(sddm.conf(5)); when `weston` is not installed the greeter display server fails every boot and SDDM
falls back to `DisplayServer=x11-user`, which tears the login down 30/60 seconds later.

The config body is an assets template; the consumer's role supplies values but must not patch the
body with `blockinfile` (spine AD-9). The template therefore has to express the compositor command
explicitly before the consumer can install `weston` and pass the override.

Evidence: host `cat /etc/sddm.conf.d/10-dotfiles.conf` (no `[Wayland]`), `command -v weston` → exit
1, `journalctl -b -u sddm | grep -c "falling back to DisplayServer=x11-user"` → 4. Verify:
`cat /etc/sddm.conf.d/10-dotfiles.conf | grep -n '\[Wayland\]'` → no line.

## What Changes

- `templates/display-manager/sddm.conf.j2` gains an explicit `[Wayland]` section:
  `CompositorCommand={{ display_manager_sddm_compositor_command | default('weston --shell=kiosk') }}`.
- `templates/display-manager/sddm.conf.vars.schema.json` adds
  `display_manager_sddm_compositor_command` as an **optional** string (no schema `default`), keeping
  `schema_major: 1` and `additionalProperties: false`.
- `scripts/validate-templates.py` asserts the sddm body carries `[Wayland]` + `CompositorCommand`,
  its default, and an override; when Jinja2 is importable it renders with the required variable
  only and with the optional override.
- `catalog.yaml`, `README.md`, `templates/README.md` and `CHANGELOG.md` record the new optional
  variable, the counts and the `v0.6.0` release.
- Release `v0.6.0`; the consumer pin bump and the `weston` package stay out of this repository.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `assets-catalog`: the templates contract gains the requirement that the SDDM template names its
  Wayland greeter compositor explicitly, with an optional consumer override.

## Impact

- Template body + one vars schema; validator assertion; catalog/docs counts; tag `v0.6.0`.
- No class, path, required variable or schema major changes. No rendered output, package list,
  service name or consumer destination enters this repository.
- Out of scope: `dotfiles-provision` package installation, role var, pin bump to `v0.6.0`, verify
  assertions and the host reboot (Wave 2).
