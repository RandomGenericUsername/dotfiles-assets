---
id: REQ-002
title: "S1 assets cut: icons + content, one group map, v0.2.0"
kind: requirement
status: in-progress
size: L
lane: bmad-advisory
links:
  openspec: assets-catalog
  bmad: none
worktree: .worktrees/s1/
branch: ticket/s1-assets-icons-content
children: []
---

# S1 assets cut: icons + content, one group map, `v0.2.0`

## Requirement

Land the first real corpus slice in `dotfiles-assets`: the 117-SVG icon template tree, the icon
color-mapping manifest and vocabulary, the 82.6 MB wallpaper archive (unmodified bytes) and the
authored btop-theme class. Give the icons and content classes their release-time validators, cut
`v0.2.0`, and let `dotfiles-v3` pin it (the consumer cut-over is a separate commit in that repo).

## Acceptance

- [ ] `icons/templates/` and `content/` imported with `cp -a`; tarball sha256 identical on both
      sides and `diff -r` exit 0 for each imported tree (run before any consumer deletion).
- [ ] `icons/mappings/` holds exactly `icons.yaml` (one group map) and `defaults.yaml`
      (vocabulary); the six stale per-concern duplicates are retired with evidence.
- [ ] `make validate-icons` fails a stale mapping template, an undeclared `{{COLOR_*}}`, a
      malformed SVG, a non-bare `output`, and a second group-map file.
- [ ] `make validate-content` fails a tarball without a top-level `default.png` and a zero-byte
      `*.theme`.
- [ ] `GATES` = `validate validate-icons validate-content lint hermetic`; `make gates-ci`,
      `make hermetic`, `make ci-gates-parity` exit 0; CI green on `master` and on the tag.
- [ ] Annotated `v0.2.0` pushed and anonymously fetchable (tag object + peeled commit recorded
      below); GitHub Release published with notes and no assets.
- [ ] `catalog.yaml`, `icons/schema.json`, `icons/README.md`, the openspec spec and the CHANGELOG
      state what the classes hold and why the split is one manifest.

## Blocker found in the first pass (and its resolution)

The verbatim import made `make validate-icons` fail with **15 violations, all in
`icons/mappings/network.yaml`**:

- 12 `variants[].template` entries named SVGs deleted in `dotfiles-v3@37fd3958` ("icons: rework
  network group templates"): `ethernet/{default,rounded,sharp}`,
  `ethernet-no-internet/{rounded,sharp}`, `wifi-{low,medium,high}/sharp`,
  `wifi-disabled/{default,rounded,sharp}`, `wifi-no-internet/sharp`;
- `COLOR_CROSS` / `COLOR_WARNING` used by templates the stale group references but not declared in
  that group's `color_mappings` (they are declared in `icons.yaml`'s live `network` group).

`network.yaml` was never updated after that rework. This is the class of bug the new gate exists to
catch, so the first pass stopped **before tagging** rather than patching paths by guesswork.

### Resolution: retire the duplicate per-concern files

Orchestrator decision, re-verified here before acting:

| Claim | Evidence (executed) |
| --- | --- |
| No consumer loads the per-concern files | `rg -l --fixed-strings '<file>'` over `icon-templates-renderer/`, `dotfiles-v3/src`, `dotfiles-v3/scripts`, assets → only `verify/vars/main.yml` (required-member list), the assets docs, and one provisioning test *fixture string*; no loader reference |
| ITR takes one YAML path | `src/icon_templates_renderer/cli/{render,validate,list_cmd,mapping}.py` all build a request with a single `yaml_path=Path(yaml_file)`; `YamlIconConfigLoader.load()` parses one file |
| Runtime reads `icons.yaml` only | `src/runtime/src/runtime/application/derive.py` candidates name `icon-mappings/icons.yaml` / the directory; `scripts/sync-icons-manifest.py:45` is `SPINE/"icon-mappings"/"icons.yaml"` |
| The duplicates are stale/partial or byte-equal | `battery.yaml` 11 variants vs `icons.yaml` 16; `power-menu.yaml` same names, different `color_mappings`; `network.yaml` 12 non-existent templates; `email-client`/`wallpaper-selector`/`wlogout` byte-equal |
| `icons.yaml` is the declared single manifest owner | `dotfiles-v3@d00c3932` ("uniform icon contract + single manifest owner"); the authoring doc says new groups/variants go only to `icons.yaml` |

Six files were `git rm`-ed: `battery.yaml`, `email-client.yaml`, `network.yaml`, `power-menu.yaml`,
`wallpaper-selector.yaml`, `wlogout.yaml`. `icons.yaml` and `defaults.yaml` are byte-identical to
the source. `make validate-icons` now rejects any second `*.yaml` under `icons/mappings/`, so the
split cannot recur.

**Deviation from the slice text:** S1 said "copy the 8 mapping YAMLs verbatim". The import is
verbatim **minus six unread duplicate group maps**; that is the only content deviation, and it is
recorded here and in `CHANGELOG.md`.

## Evidence

- Byte identity (before any consumer deletion):
  `sha256sum` of `wallpapers.tar.gz` → `8c027906733c142ecfed2b5a34342208831859f5829108d6ec82de33b3ba7838`
  on both sides; `diff -r` over `icon-templates/`, the mappings dir and `btop-themes/` → 0.
- Validators: `make validate-icons` → PASS (1 manifest, 22 groups, 136 variants, 117 SVGs, 4
  defaults); `make validate-content` → PASS (55 members, top-level `default.png`; 0 themes,
  vacuous). Negative runs: an injected missing template fails with the file/group/variant named; a
  synthetic empty tarball + zero-byte theme fails with two named violations.
- Gates: `make gates-ci`, `make hermetic`, `make ci-gates-parity`, `openspec validate --specs` → 0.
- Tag: recorded below after the release.
