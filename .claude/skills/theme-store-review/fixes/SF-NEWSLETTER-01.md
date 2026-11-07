# SF-NEWSLETTER-01 — Newsletter email input validates

Requirement and how to verify: `../references/feedback-ledger.md` → `SF-NEWSLETTER-01`.
Check type: static + runtime

## Recipe (any theme)

Every newsletter email input: `type="email"`, `required`, an email `pattern` requiring a dot in the domain, and a translated `title` message. No `novalidate` unless JS shows its own error.

## History

Each entry is one theme where this was fixed. On a theme built on the same base the files
are usually the same paths, so start from the newest entry; if the root cause differs, fix it
from the recipe above and add a new entry.

### Folio — R1 (2026-11-05)

- **Root cause:** The email input was `type="email"` only, which accepts `abc@abc`; reviewers expect an incomplete address to be rejected with a visible message.
- **Fix:** Add `pattern='[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'` and `title="{{ 'customer.subscribe.error_text' | t }}"` to the email input of every newsletter form. Check the field snippet's param name before passing attributes (`field-text`/`field-input` read `attrs`, not `attr`). Keep `required`; no `novalidate` unless JS shows the error itself.
- **Files:** `src/snippets/email-signup/email-signup.liquid`, `src/snippets/email-signup-footer/email-signup-footer.liquid`, sign-up popup
- **Verify:** Runtime: submit `abc@` and `abc@abc` in footer, section and popup forms; each shows a message.
