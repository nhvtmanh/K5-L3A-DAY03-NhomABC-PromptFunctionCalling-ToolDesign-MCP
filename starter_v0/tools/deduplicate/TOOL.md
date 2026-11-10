---
name: deduplicate
track: core
kind: local_formatter
requires_env: []
inputs: [items]
outputs: [items, removed_count]
side_effect: false
---
# deduplicate

Removes repeated items with the same URL while preserving the first occurrence
and input order. URL scheme and host are case-insensitive, trailing slashes and
fragments are ignored, and query strings are preserved. Items without a URL are
kept because they cannot be reliably matched.
