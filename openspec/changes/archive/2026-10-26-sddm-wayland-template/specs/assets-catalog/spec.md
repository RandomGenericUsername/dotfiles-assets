# Spec Delta

## ADDED Requirements

### Requirement: The SDDM template names its Wayland greeter compositor

`templates/display-manager/sddm.conf.j2` SHALL render a `[Wayland]` section whose
`CompositorCommand` defaults to `weston --shell=kiosk` via
`display_manager_sddm_compositor_command`. The schema SHALL declare that variable optional, with no
schema-level default, and `make validate-templates` SHALL fail when the section or fallback is
missing. The package and the consumer pin stay outside this repository.

Evidence: plan 03 §2; `make validate-templates`; host fallback count 4.

#### Scenario: The Wayland compositor is implicit

- **WHEN** the sddm template omits `[Wayland]`, omits `CompositorCommand`, or loses the
  `weston --shell=kiosk` fallback
- **THEN** `make validate-templates` fails naming the template and the missing contract, because
  the rendered config would silently depend on SDDM's implicit default and a missing `weston`

#### Scenario: The consumer overrides the compositor

- **WHEN** the consumer supplies `display_manager_sddm_compositor_command`
- **THEN** the rendered config carries the supplied command instead of the template default, and
  rendering with only the required display-server variable still produces a `[Wayland]` section
  with `CompositorCommand=weston --shell=kiosk`
