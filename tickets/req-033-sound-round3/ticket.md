---
id: req-033
title: "Sound panel round three: shared labels, no footer copy"
kind: requirement
status: done
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-033/
branch: ticket/req-033-sound-round3
---

# Sound panel round three

Owner feedback:

- Remove the panel footer copy and the settings popover footer copy; the
  template must not leave dead footer selectors.
- Output and Input use exactly one type style: `.audio-section-label`
  (title size/ink, start-aligned, same casing).
- The settings switch stays the compact 42x24 / 20px knob; the bar fixes the
  bounds so the skin pill paint cannot inflate it.

The mock/ticket and hash are updated by the bar; this assets tag supplies the
shared label and removes the footer selectors. No skin retune.
