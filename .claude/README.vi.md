# Shopify theme

Theme Shopify với pipeline port HTML design → Liquid, được vận hành bởi hệ agent `.claude/` chạy trên Claude Code.

> English version: [README.md](./README.md)

## Tổng quan

Dự án có 3 lớp chính:

- `design/` — nguồn HTML thiết kế (xo-include + xo-component convention) — đầu vào.
- `src/` — Liquid theme source (`sections/`, `snippets/`, `blocks/`, `groups/`, `layout/`, `pages/`, `config/`, `styles/`) — đầu ra do agent viết.
- `shopify/` — output compile (tạo bởi build pipeline, không tự edit).

Agent `.claude/` đứng giữa: đọc design, viết Liquid, validate schema, commit theo scope. State của dự án được lưu trong `.agent-state/` (markdown commit vào git) nên nhiều phiên làm việc có thể nối tiếp nhau mà không mất context.

## Hệ thống `.claude/`

### 3 lớp

| Lớp | Vị trí | Vai trò |
|-----|--------|---------|
| **Bộ nhớ dự án** | `.agent-state/` | 3 file markdown: `PLAN.md` (hàng đợi ưu tiên ⚪🔵✅⏸❓), `PROGRESS.md` (nhật ký append-only, mỗi phiên 1 entry), `INVENTORY.md` (coverage map auto-generate). |
| **Skill catalog** | `.claude/skills/<name>/` | 19 skill chuyên môn — mỗi skill là 1 thư mục có `SKILL.md` + `references/*.md` + `scripts/` nếu cần. |
| **Tích hợp ngoài** | `.mcp.json` | 3 MCP server (`xo-components`, `playwright`, `xo-design`) + `context7` cho docs lookup. |
| **Guardrails** | `.claude/hooks/` + `settings.json` | `skill-reminder.cjs` — hook `PreToolUse` nhắc đúng skill theo file path ở mỗi lần Edit/Write; `settings.json` ghim model, plugin skill, và đăng ký hook. |

### 19 skill

| Skill | Trả lời | Khi nào kích hoạt |
|-------|---------|---------------------|
| `planner` | **WHAT + STATUS** — việc gì tiếp theo, đang ở đâu | Đầu mỗi phiên hoặc khi hỏi "what's next" |
| `design-to-liquid` | **HOW** — port 1 section cụ thể (Step 0 tokens → Step 6 restyle) | User pick section trên xo-design hoặc gọi `/design-to-liquid` |
| `figma-to-liquid` | **HOW (Figma)** — port section/snippet từ frame Figma qua Dev Mode MCP | Chọn frame trong Figma desktop rồi `/figma-to-liquid` |
| `design-sync` | Worklist re-port khi `design/` được pull lên bản mới | `/design-sync`, "design có bản mới", sau `git -C design pull` |
| `polish` | Finishing-pass QA — a11y · `xo-animate` reveal · `xo-hover` | `/polish <target>`, hoặc handoff khi design-to-liquid xong |
| `editor-qa` | QA trên Theme Editor thật — add section/blocks, set field, desktop↔mobile, screenshot | `/editor-qa <target>`, "test trên editor" |
| `lighthouse-audit` | Điểm Lighthouse (Perf/A11y/BP/SEO) + Core Web Vitals trên storefront URL | `/lighthouse-audit <url>` — chạy tay lúc theme đã xong |
| `liquid` | Liquid language reference — tags, filters, objects, idioms, gotchas | Author/debug bất kỳ file `.liquid` nào |
| `snippet` | Cách viết thân `.liquid` của snippet | Tạo/sửa snippet |
| `schema` | Cách viết `schema.js` (section / block / global) | Tạo/sửa schema |
| `scss` | Framework SCSS: `color()` / `fz()` / `media()` / BEM | Viết `.global.scss` |
| `xo-css` | Atomic class syntax: `p:1rem c:primary|h d:none@md` | Class trên liquid |
| `liquid-doc` | `{% comment %} @param … %}` doc block | Header file snippet |
| `motion` | Authority wiring motion: `xo-animate` / `xo-parallax-scroll` / `xo-parallax-hover` (+ gotcha `xo-start/xo-end`) | `/motion`, "thêm animation/parallax" |
| `web-components` | Viết MỚI web component `xo-*` (TS, `XoComponent`) vào `src/scripts/` | `/web-components`, "tạo web component" |
| `git` | Commit theo scope; sau commit hỏi Push / Commit tiếp / Dừng (Step 11); push chỉ khi bạn chọn, không `--force`, không amend | User gõ `/git` |
| `extract-icon` | Sync SVG Lucide vào `src/snippets/icons/icon-*.liquid` | "update icons", "sync icons", "lucide → snippet" |
| `system-upgrade` | Check, đánh giá + **nâng cấp** hệ `.claude/` (việc động tới skill delegate cho `skill-creator`) | `/system-upgrade`, `/system-audit`, "kiểm tra hệ thống", "nâng cấp hệ thống" |
| `shopify-watch` | Radar tin Shopify liên quan theme, hand-off cho `/system-upgrade` | `/shopify-watch`, "Shopify có gì mới" |

### Script tooling

| Script | Mục đích |
|--------|----------|
| `.claude/skills/design-to-liquid/scripts/validate-schema.py` | Validate `schema.js`: compile, duplicate IDs, range, select, inline_richtext tags, block resolve. Cộng thêm Theme Store label audit (AmE, banned phrases, ampersand, `?`). Cờ `--strict` để escalate warnings → errors. |
| `.claude/skills/planner/scripts/scan-inventory.py` | Quét `design/` + `src/sections/`, sinh `INVENTORY.md`. |

### Entry point

```
CLAUDE.md  →  .claude/AGENT.md
                    │
                    └─→ ràng buộc: đọc .agent-state/PROGRESS rồi PLAN trước khi làm bất cứ điều gì khác
```

## Khởi đầu một dự án design mới

### Day 0 — Setup (~30 phút, làm tay)

1. Copy `.claude/` + `CLAUDE.md` từ project mẫu sang repo mới.
2. Tạo `.agent-state/` rỗng — kickoff-protocol sẽ tự seed PLAN/PROGRESS/INVENTORY.
3. Bỏ thiết kế vào `design/` (cấu trúc `design/src/pages/*.html` + `design/src/sections/<name>/<name>.html`).
4. Nếu design có xo-design: `cd design && npm run xo-design` → mở browser thấy toolbar `◎ Pick section`.
5. Cập nhật `.mcp.json` nếu URL xo-design khác port đặt trong `design/xo-design/.env`.
6. (Optional) Wire thêm MCP server design pipeline cần dùng (vd: `context7` cho docs lookup) vào `.mcp.json`.

### Day 1 — Phiên đầu tiên với Claude

Mở Claude Code, gõ `bắt đầu nào` hoặc `port design này`. Agent sẽ tự:

1. Đọc `CLAUDE.md` → `AGENT.md` → tìm state docs.
2. State không tồn tại → kích hoạt `planner` kickoff-protocol.
3. Quét `design/` + `src/sections/`, sinh `PLAN.md` v0 (pages + sections + Step 0 tokens) và `INVENTORY.md` v0.
4. Hỏi thứ tự ưu tiên các page → user chốt.
5. Append entry phiên 1 vào `PROGRESS.md`.

### Day 2 — Step 0 (1 lần / dự án)

User: `làm Step 0`. Agent sẽ:

1. Đọc brand guide / global SCSS / palette của design.
2. Sửa `src/config/presets/preset-1.js` (KHÔNG tạo `preset-<brandname>.js`).
3. Set `color_schemes` (≥ 4 màu, mỗi background pair với foreground), 4 font slots, 6 heading presets, radius, page width, spacing.
4. `src/config/settings_data.js`: `current = JSON.parse(JSON.stringify(preset1))` (object clone — KHÔNG string).
5. Italic-em rule vào `src/styles/base/content.scss` nếu design có.
6. Build + reload Theme Editor → verify `:root` emit đúng `--color-…` / `--font-…`.
7. Flip "Theme tokens" trong PLAN.md → ✅.

## Một ngày làm việc bình thường

```
09:00  Mở Claude Code, gõ "hôm nay làm gì?"
        → Agent đọc PROGRESS top + PLAN, đề xuất section tiếp theo.

09:05  Browser: click ◎ Pick trên section cần port.
        Claude: /design-to-liquid

09:06  Agent tự động:
        - mcp__xo-design__get_selection() lấy htmlPath / scssPath
        - Confirm "Convert {page}.{sectionName} → src/sections/{name}/ ?"
        - Đọc design HTML + SCSS
        - Variant audit: chạy thang A→B→C cho từng snippet sẽ render
        - Viết 3 file: <name>.liquid + <name>.global.scss + schema.js
        - Run validate-schema.py → fix warnings nếu có
        - mcp__xo-design__clear_selection()
        - Update PLAN.md → ✅

09:45  (optional) Visual check qua playwright MCP — screenshot Theme Editor preview.

10:00  /git
        → git skill: scan → preview → confirm → commit 1 scope.

10:30  Lặp lại từ 09:05 cho section tiếp theo.

17:00  Cuối phiên: agent append PROGRESS.md với Goal/Done/Decisions/Open.
        /git agent-state để commit state file.
        git push (làm tay khi muốn).
```

### Picker MCP

User trỏ chuột (`◎ Pick section`) thay vì gõ tên — agent nhận selection qua MCP. Lệnh tiếng Việt tự nhiên hoạt động: "làm section này", "port cái đang select", `/design-to-liquid` không tham số.

### Variant audit ladder

Trước khi `{% render 'X' %}` trong section mới, agent **bắt buộc** chạy thang:

| Bước | Hành động | Khi nào |
|------|-----------|---------|
| A | Set giá trị trong `preset-N.js` | Variant đã đọc setting đó, chỉ cần value đúng |
| B | Modify variant gần nhất | Thay đổi có lợi chung; không phá preset khác |
| C | Tạo variant mới (`<snippet>-N`) | **HỎI USER TRƯỚC** — ripple vào dispatcher + global-schema |

## Validator workflow

```bash
# Validate 1 section
python .claude/skills/design-to-liquid/scripts/validate-schema.py src/sections/<name>/

# Sweep toàn bộ
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all

# CI mode — warning escalate thành error
python .claude/skills/design-to-liquid/scripts/validate-schema.py --all --strict

# Theme settings sanity (settings_data.json vs settings_schema.json)
python .claude/skills/design-to-liquid/scripts/validate-schema.py --theme

# Cross-validate 1 preset với sibling schema
python .claude/skills/design-to-liquid/scripts/validate-schema.py --preset src/sections/<name>/preset-1.js
```

Bắt được: disallowed `inline_richtext` tags, missing range bounds, undefined select options, unresolved block types, theme-settings `current` as string, orphan color schemes, missing labels, British spelling, banned phrases (`CTA` / `X position` / `homepage` / `slider` / …), `&` hoặc `?` trong label.

## Commit workflow (`/git`)

Quy ước cứng:

- 1 commit = 1 scope. Không straddle scope (`.claude` + `root` phải 2 commit riêng).
- Conventional Commit format: `<type>(<scope>): <summary>` ≤ 70 chars, lowercase.
- Stage path cụ thể, không bao giờ `git add -A` / `.`.
- Không push, không amend, không bypass hook, không AI co-author trailer.

Skill `git` tự scan dirty, gợi ý scope, draft message, hỏi confirm, run pre-commit gates (secret-file block, schema mismatch, scope leak, settings JSON sync), rồi commit. User phải xác nhận trước mỗi commit.

## Vòng đời dự án (tham khảo)

| Tuần | Phase | Hoạt động |
|------|-------|-----------|
| 1 | Kickoff + Step 0 | PLAN seeded; preset-1.js đầy tokens; 1-2 section thử nghiệm pipeline |
| 2-3 | Home page sprint | 12-15 section home; 1-2 snippet variant mới (audit step C đã duyệt) |
| 4 | Product + Collection | PDP + PLP; blocks (price/vendor/add-to-cart); facet filters |
| 5 | Cart + Article + Pages còn lại | Section nhỏ, nhiều |
| 6 | Polish + Theme Store prep | Clear pre-existing validator errors; chạy `--strict`; Lighthouse; demo store; docs |

Định nghĩa "done" tham khảo `.claude/skills/design-to-liquid/references/theme-store-requirements.md`.

## Tham khảo sâu hơn

| Cần biết | File |
|---------|------|
| Working philosophy + skill catalog đầy đủ | `.claude/AGENT.md` |
| Format từng state doc | `.claude/skills/planner/references/*.md` |
| Cách port section step-by-step | `.claude/skills/design-to-liquid/SKILL.md` |
| Map tokens design → preset | `.claude/skills/design-to-liquid/references/tokens-mapping.md` |
| Theme Store requirements + label audit | `.claude/skills/design-to-liquid/references/theme-store-requirements.md` |
| Variant audit + escalation ladder | `.claude/skills/design-to-liquid/references/sections-to-liquid.md` |
| Picker MCP protocol | `.claude/skills/design-to-liquid/references/picker-protocol.md` |
| BaseHTML SCSS framework | `.claude/skills/scss/SKILL.md` |
| Atomic class syntax (XO-CSS) | `.claude/skills/xo-css/SKILL.md` |
| Commit workflow chi tiết | `.claude/skills/git/SKILL.md` |

## Tech stack

- Shopify Liquid theme (source `src/`, compile `shopify/`)
- Vite + scss-glob plugin
- BaseHTML SCSS framework + XO-CSS atomic utilities
- xo-webcomponents runtime (`<xo-container>`, `<xo-carousel>`, `<xo-magnetic>`, …)
- Claude Code + MCP (xo-components, playwright, xo-design)
- `context7` MCP để fetch docs cập nhật (Liquid, Shopify APIs, …)
