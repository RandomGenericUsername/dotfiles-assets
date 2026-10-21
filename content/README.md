# content — large/binary content: wallpapers and authored themes

```text
wallpapers/wallpapers.tar.gz   the wallpaper set, as one unmodified archive
btop-themes/                   authored btop themes (*.theme), currently none
```

## The tarball is a byte contract

`wallpapers/wallpapers.tar.gz` is imported byte-for-byte and is **never re-packed**.
The runtime derives a hash from the archive, so re-packing changes the hash for no
user-visible gain. The deploy unpacks the archive's **contents** into the consumer's
wallpaper directory, which is why the archive must hold a **top-level `default.png`**
(not `wallpapers/default.png`). The installer asserts that at deploy time; this
repository asserts it at release time, so a bad archive cannot be tagged:

```bash
make validate-content
```

The gate also fails a zero-byte `*.theme` (an empty theme renders as "no theme" on a
host) and any archive member whose path escapes the archive root. It prints the
authored-theme count, and says "vacuous" out loud when the count is zero — a silent
skip and a pass must not be indistinguishable in a green log.

## Authored themes only

`btop-themes/` holds repo-authored `*.theme` files. The btop **active theme** is a
mutable host preference written by the theme studio, not content: it is never an
asset (spine AD-11), so it must not appear here.
