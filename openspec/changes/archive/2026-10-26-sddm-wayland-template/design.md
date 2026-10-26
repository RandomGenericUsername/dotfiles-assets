# Design

## Context

The SDDM config body is a `templates/` asset; the consumer's `display_manager` role renders it with
values, installs packages and enables the service. A role-side `blockinfile` would put body content
back in the consumer and violate the AD-9 seam. SDDM's implicit Wayland compositor default is
`weston --shell=kiosk`; implying it in a template that sets `DisplayServer=wayland` makes the
dependency invisible until the greeter fails at boot.

## Goals / Non-Goals

**Goals:**

- Make the rendered config name its Wayland greeter compositor explicitly.
- Keep the override optional and the schema additive (`schema_major` stays 1).
- Make the contract executable in `make validate-templates`.

**Non-Goals:**

- Installing `weston`, passing the role variable, or bumping the consumer pin (Wave 2).
- Naming a package list, service name or destination in this repository.
- Rendering or committing an SDDM config file.

## Decisions

### D1 — Default lives in the template, not the schema

The template uses `{{ display_manager_sddm_compositor_command | default('weston --shell=kiosk') }}`
and the schema marks the variable optional without a `default` keyword. The rendered body must
always carry a command; a schema default would still make an absent value a consumer concern, while
the validator's body-equality rules treat the template as the source of the fallback.

**Alternative rejected:** make the variable required. That is a schema break for every consumer and
forces a role variable before the template can render.

### D2 — A targeted validator assertion, not a new engine

`validate-templates.py` stays stdlib-only. It statically asserts the `[Wayland]` section, the
`CompositorCommand` line, the exact `weston --shell=kiosk` fallback and the optional schema entry.
When `jinja2` happens to be importable, it additionally renders the template with the required
variable only and with an override, proving the default is real render behavior. The deep mode is
reported as a NOTE when skipped, like the existing `jsonschema` mode.

**Alternative rejected:** a general Jinja renderer in this repository. The renderer belongs to the
consumer; the gate only needs this one deploy-critical contract.

### D3 — `schema_major` stays 1

The change adds an optional property and keeps every required name, type and path. Consumers that
parse the schema continue to work; a MAJOR bump would be a false break.

## Risks / Trade-offs

- **Default drift:** the template default and the package the consumer installs must stay in sync.
  The plan names `weston --shell=kiosk`; the consumer's unit test asserts the rendered line.
- **Optional empty value:** an empty string can override the default. The schema sets `minLength: 1`
  so a consumer-supplied value cannot be empty.
- **Targeted coupling:** the validator names one template path. That path is already
  consumer-addressed and a rename is a MAJOR change, so the coupling is explicit rather than hidden.

## Verification plan

| Decision | Command | Expected |
| --- | --- | --- |
| Red proof | `make validate-templates` with the assertion and old template | non-zero, names the missing `[Wayland]` |
| D1 default | `uv run --with jinja2` render with only `display_manager_sddm_display_server` | `CompositorCommand=weston --shell=kiosk` |
| D1 override | same render with the optional variable | `CompositorCommand=<override>` |
| D2 assertion | `make validate-templates` | exit 0, sddm assertion line |
| D3 additive | `make validate` | exit 0, `schema_major: 1` both sides |
| Release | `make gates`, `make gates-ci`, `make hermetic` | exit 0 |
