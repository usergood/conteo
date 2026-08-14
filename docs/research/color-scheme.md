# Conteo — Color Scheme & Design Guideline

**Scope:** govern all future UI in this repo. Stack: FastAPI + Next.js, plain CSS with custom properties in `frontend/src/app/globals.css`. Tool-agnostic (works with any coding agent / human).
**Status:** research proposal — no source code changed.

---

## 0. How to use this doc

1. **Pick a palette.** Start from §1. The three palettes are drop-in replacements for the `:root[data-theme='light']` and `:root[data-theme='dark']` blocks in `globals.css`. Each is complete (all existing custom properties + appbar).
2. **Keep the token names.** Do not invent new semantic tokens; reuse `--bg`, `--panel`, `--ink`, `--muted`, `--line`, `--accent`, `--accent-ink`, `--accent-soft`, `--warn`, `--warn-soft`, `--ok`, `--ok-soft`, `--appbar`, `--appbar-ink`. New screens should consume these tokens, never hardcode hex.
3. **Apply the design principles** in §2 to any new screen — color, hierarchy, spacing, typography, motion, backgrounds.
4. **Write your prompts** per §3 when asking an agent to build UI, so the output follows this guideline instead of "AI slop" defaults.
5. **Verify before shipping** — run the contrast check in §1.3 on any palette change.

---

## 1. Candidate palettes

The current light theme is jarring because `--panel: #ffffff` sits as a stark, blue-tinted "pure white" slab against the lavender `--bg` — the cookbook's exact anti-pattern ("clichéd color schemes, particularly purple gradients on white backgrounds"). The fix, per the guidance, is to commit to a **cohesive warm-neutral surface** and let the purple accent carry the identity rather than spreading purple everywhere. Each palette keeps a purple accent (the product identity) but varies its hue temperature and weight.

The core insight from the source: **"Dominant colors with sharp accents outperform timid, evenly-distributed palettes."** We make the surface (warm neutral) the *dominant* color and the purple accent *sharp* — a strong single accent on a calm field, instead of the current lavender-wash-everywhere.

### 1.1 Contrast method & assumptions

- WCAG 2.1 relative-luminance ratio = `(L1+0.05)/(L2+0.05)`, computed on sRGB linearized channels. WCAG AA requires **≥ 4.5:1 for normal text**, **≥ 3:1 for large text (≥18.66px bold / ≥24px) and UI component boundaries** (WCAG 1.4.3, 1.4.11).
- We verify the four pairs the task calls out: `--ink` on `--bg`, `--ink` on `--panel`, `--muted` on `--bg`, `--accent-ink` on `--accent`. All pass AA.
- Ratios below are exact, computed from the given hex via the standard WCAG algorithm. They assume no transparency, no blend, and default font rendering (no font smoothing that changes luminance).

---

### PALETTE A — "Linen & Dusk" (recommended)

Warm neutral light surfaces (linen) + a violet-purple accent; dark side shifts to a soft plum-navy. Least saturated background of the three — the most "natural, smooth" reading, most distinct from the current harsh white.

**Light `:root[data-theme='light']`**
```css
--bg: #f6f2ec;          /* warm paper / linen, no more lavender */
--panel: #fffdfa;       /* warm white — softly off-white, not #fff */
--ink: #24202c;         /* near-black plum */
--muted: #6b6576;       /* greyed plum */
--line: #e8e2d8;        /* warm taupe hairline */
--accent: #5b3fd6;      /* violet-purple */
--accent-ink: #ffffff;
--accent-soft: #efebfb; /* lilac tint over warm base */
--warn: #a15c07;        /* amber-ochre */
--warn-soft: #fbf2e0;
--ok: #137a41;          /* leaf green */
--ok-soft: #edf6ef;
--appbar: linear-gradient(135deg, #d8cbf8, #b9a5e8); /* violet wash, warm underglow */
--appbar-ink: #332a5e;
```

**Dark `:root[data-theme='dark']`**
```css
--bg: #15101d;          /* soft plum-black, not blue */
--panel: #1c1626;
--ink: #ece8f5;
--muted: #a29bb0;
--line: #2c2436;
--accent: #a08cff;      /* luminous violet */
--accent-ink: #15101d;
--accent-soft: #2a2240;
--warn: #f5b14e;
--warn-soft: #2e2410;
--ok: #63d28a;
--ok-soft: #12311d;
--appbar: linear-gradient(135deg, #2b1f45, #1d162e);
--appbar-ink: #e6e0f5;
```

**Contrast (AA verified)**
| Pair | Ratio | Meets AA |
|---|---|---|
| `--ink #24202c` on `--bg #f6f2ec` | **14.3** | ✓ (needs ≥4.5) |
| `--ink #24202c` on `--panel #fffdfa` | **15.7** | ✓ |
| `--muted #6b6576` on `--bg #f6f2ec` | **5.0** | ✓ |
| `--accent-ink #ffffff` on `--accent #5b3fd6` | **6.7** | ✓ |
| dark `--ink` on `--bg` | **15.5** | ✓ |
| dark `--ink` on `--panel` | **14.6** | ✓ |
| dark `--muted` on `--bg` | **7.0** | ✓ |
| dark `--accent-ink #15101d` on `--accent #a08cff` | **6.8** | ✓ |

**Why it reads smooth/natural:** warm neutrals (R>G>B) avoid the cold clinical cast of pure white; the violet accent stays the identity while the background stops being purple-washed. Surface tint is subtle — off-white, not cream-colored panels that risk looking dated.

---

### PALETTE B — "Stone & Plum" (more saturated)

Same warm-neutral direction but deeper, warmer panels and a slightly warmer, deeper purple. Reads richer / more "crafted" than A; panel is a touch less white, which lowers glare most aggressively.

**Light `:root[data-theme='light']`**
```css
--bg: #f4f1ea;
--panel: #fdfbf6;
--ink: #2a2533;
--muted: #6f6877;
--line: #e6dfd2;
--accent: #6a3fd1;
--accent-ink: #ffffff;
--accent-soft: #ede8fb;
--warn: #a15c07;
--warn-soft: #fbf2e0;
--ok: #12743f;
--ok-soft: #edf6ef;
--appbar: linear-gradient(135deg, #dccdf6, #b99fe6);
--appbar-ink: #332a5e;
```

**Dark `:root[data-theme='dark']`**
```css
--bg: #141017;
--panel: #1b171d;
--ink: #eeeaec;
--muted: #a49ca6;
--line: #2d272e;
--accent: #a489ff;
--accent-ink: #141017;
--accent-soft: #2c2441;
--warn: #f5b14e;
--warn-soft: #2e2410;
--ok: #5fcf86;
--ok-soft: #12311d;
--appbar: linear-gradient(135deg, #2c2046, #1e162f);
--appbar-ink: #e7e1f6;
```

**Contrast (AA verified)**
| Pair | Ratio | Meets AA |
|---|---|---|
| `--ink` on `--bg` | **13.2** | ✓ |
| `--ink` on `--panel` | **14.4** | ✓ |
| `--muted` on `--bg` | **4.8** | ✓ |
| `--accent-ink` on `--accent` | **6.5** | ✓ |
| dark `--ink` on `--bg` | **15.8** | ✓ |
| dark `--ink` on `--panel` | **14.8** | ✓ |
| dark `--muted` on `--bg` | **7.1** | ✓ |
| dark `--accent-ink` on `--accent` | **6.8** | ✓ |

**Why choose B over A:** if you want the UI to feel warmer and more "material" (a tactile, paper-and-ink quality) than A's airy neutral. The darker purple `#6a3fd1` is the most conventional "brand purple."

---

### PALETTE C — "Dawn & Midnight" (closest to current, softened)

Closest to today's scheme: keeps a faint cool-rose tint in the light surface (less "white-shock") while staying in the current purple family. Smallest visual delta from the existing theme — easiest to adopt, but least distinct from what you have.

**Light `:root[data-theme='light']`**
```css
--bg: #f4f1fa;
--panel: #fbf9ff;      /* soft near-white, rose/lavender tint, not pure #fff */
--ink: #241f2e;
--muted: #6a6276;
--line: #e7e1f2;
--accent: #5d45d4;
--accent-ink: #ffffff;
--accent-soft: #efeafb;
--warn: #a15c07;
--warn-soft: #fbf2e0;
--ok: #12743f;
--ok-soft: #edf6ef;
--appbar: linear-gradient(135deg, #ddd2ff, #c0adff);
--appbar-ink: #332a5e;
```

**Dark `:root[data-theme='dark']`**
```css
--bg: #0e0b16;
--panel: #161222;
--ink: #e9e6f4;
--muted: #9f97b2;
--line: #262034;
--accent: #9c89ff;
--accent-ink: #0e0b16;
--accent-soft: #262038;
--warn: #f5b14e;
--warn-soft: #2e2410;
--ok: #5fcf86;
--ok-soft: #12311d;
--appbar: linear-gradient(135deg, #1e2f5c, #151f3f);
--appbar-ink: #dbe4f7;
```

**Contrast (AA verified)**
| Pair | Ratio | Meets AA |
|---|---|---|
| `--ink` on `--bg` | **14.4** | ✓ |
| `--ink` on `--panel` | **15.3** | ✓ |
| `--muted` on `--bg` | **5.2** | ✓ |
| `--accent-ink` on `--accent` | **6.4** | ✓ |
| dark `--ink` on `--bg` | **15.9** | ✓ |
| dark `--ink` on `--panel` | **14.9** | ✓ |
| dark `--muted` on `--bg` | **7.0** | ✓ |
| dark `--accent-ink` on `--accent` | **6.9** | ✓ |

**Why choose C:** minimal-change upgrade. The light surface is still lavender-tinted (smoother than today's stark `#fff` against lavender `#f5f3fb`) and the appbar stays in the current purple family. If you want the least disruptive change that still removes the "harsh white" complaint.

---

### 1.2 Comparison & recommendation

| Criterion | A Linen & Dusk | B Stone & Plum | C Dawn & Midnight |
|---|---|---|---|
| Distance from current | large | large | small |
| "Natural / smooth" | ★★★ | ★★★ | ★★ |
| Purple identity preserved | ✓ (violet) | ✓ (deep plum) | ✓ (classic purple) |
| Reduces pure-white glare | strongest | strongest | moderate |
| Distinctive (not generic) | ★★★ | ★★★ | ★★ |

**Recommendation: Palette A ("Linen & Dusk").** It best answers "smoother, more natural but still colorful": a genuinely warm neutral canvas (not purple or pure white), with a single sharp violet accent carrying the brand. Its dark theme drops the blue for plum so both themes share the same warm-violet DNA, reinforcing the purple identity across light and dark.

---

## 2. Design guideline (distilled from the cookbook + linked posts)

The following principles are distilled from the primary source — the Claude Cookbook *Prompting for frontend aesthetics* — and its companion Anthropic guidance *Improving frontend design through Skills* (which restates the same playbook at the skill level). They are stated **stack-agnostically**; nothing below assumes Claude, only that the writer is a capable frontend agent/human. The source itself is a general-purpose aesthetic prompt that Anthropic ships as a reusable skill — the guidance is tool-independent by construction.

### 2.1 Core mindset — escape the generic

> The model/agent "tends to converge toward generic, 'on distribution' outputs. In frontend design, this creates what users call the 'AI slop' aesthetic."

- Treat "safe, generic, cookie-cutter" as the enemy. Aim for output that is **distinctive, context-specific, and feels genuinely designed for this app** (a personal-finance tool, not a generic SaaS).
- Three strategies consistently improve results (from the cookbook's intro): **(1) guide specific design dimensions one at a time; (2) reference concrete inspirations (IDE themes, cultural aesthetics) without over-specifying; (3) explicitly call out the defaults to avoid.**
- **Known defaults to avoid** (explicitly named in the cookbook): overused font families (Inter, Roboto, Arial, system fonts); clichéd color schemes (especially purple gradients on white); predictable layouts/component patterns; cookie-cutter design.
- **Don't fall into a *different* local maximum:** the source warns the model "still tends to converge on common choices (Space Grotesk, for example)." When you pick a distinctive option, verify it isn't merely the *second* most common default. The companion blog adds the same warning and says to finish by telling yourself to "think outside the box."

### 2.2 Color & mood

- **Commit to a cohesive aesthetic.** Use CSS variables (custom properties) for consistency — this repo already does via `globals.css`; keep extending that, never hardcode hex in a component.
- **"Dominant colors with sharp accents outperform timid, evenly-distributed palettes."** Decide which color is dominant (in our redesign: the warm neutral surface) and which is the sharp accent (purple). Do not smear the accent color over everything — restraint in the field is what makes the accent read as intentional.
- **Color communicates mood before words.** A warm-neutral canvas reads calm, trustworthy, "natural" (right for money/finance); cold pure white reads clinical/harsh; saturated backgrounds read energetic/brand-forward. Choose deliberately for what the screen must convey.
- **Draw from IDE themes and cultural aesthetics for inspiration** — but always land back on a token-driven palette so the result stays consistent repo-wide.
- **Purple identity:** keep it, but *vary* it (see §1: violet, plum, classic purple are all valid). The current problem is not the purple — it's the purple *everywhere* on a stark white field.

### 2.3 Hierarchy

- **Seasoned visual hierarchy beats decoration.** Use size, weight, and contrast (muted vs. ink) to establish what matters first. On a finance screen, the headline number should be the largest, darkest, most emphasized element; supporting metadata should drop to `--muted`.
- **One dominant accent at a time.** Reserve full-saturation `--accent` for the primary action / active nav state. Secondary emphasis uses `--accent-soft` or borders (`--line`), not another loud color.
- **Structure is information** (from the companion skill guidance): dividers, labels, "eyebrows," numbering should encode something true about the content — don't add decorative numbering/labels that say nothing. This matters in a data-dense money app: only add structure that helps a user parse a month, a settlement, or a table.

### 2.4 Spacing & layout

- **Predictable spacing is a quality floor.** Use a consistent rhythm (the repo's existing `12px/16px/20px` padding cadence) rather than arbitrary per-component values. Consistency reads as polished; randomness reads as slop.
- **Let whitespace carry the calm.** "Smoother, more natural" largely comes from *space*, not just color. Generous padding around panels and breathing room between rows lowers the perceived harshness of any color scheme.
- **Less is more — cut decoration that doesn't serve the brief.** The companion skill's rule: "Before leaving the house, take a look in the mirror and remove one accessory." If a border, gradient, or shadow isn't earning its place, remove it.
- **Responsive to mobile and visible keyboard focus are non-negotiable quality floors** (per the companion skill). A polished scheme fails if it breaks at small widths or loses focus indication.

### 2.5 Typography

- **Typography instantly signals quality.** Avoid generic system fonts — but in a *self-hosted tool* respect that loading fonts has a cost. Prefer distinctive families that are self-hosted or already-available, and apply the pairing principles below.
- **Pairing principle: high contrast = interesting** — "Display + monospace, serif + geometric sans, variable font across weights." For a finance app, a strong pairing is a distinctive sans for headers/labels and a clean tabular-friendly sans or mono for numbers and tables (tables benefit from monospaced/tabular figures so columns align).
- **Use extremes, not middle weights:** "100/200 weight vs 800/900, not 400 vs 600. Size jumps of 3x+, not 1.5x." A headline should be dramatically larger and heavier than body text; timid 400↔600 weight steps are a tell of generic design. Applies to numbers especially — the big money figure should *look* big.
- **Pick one distinctive font and use it decisively; state your choice before coding.** Don't sprinkle several novelty fonts; one characterful face + a complementary utility face is the pattern.
- For the money/table surfaces, ensure **tabular figures** (even digit widths) so columns and figures align — a functional-quality aspect of typography for finance UIs, distinct from pure aesthetics.

### 2.6 Motion & backgrounds

- **Motion is a polish signal — use it deliberately, not everywhere.** "One well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions." Prefer a single high-impact orchestrated moment over a dozen tiny animations. **Respect `prefers-reduced-motion`** (companion skill: quality floor).
- **Backgrounds: create atmosphere and depth rather than defaulting to solid colors.** "Layer CSS gradients, use geometric patterns, or add contextual effects." The existing appbar gradient is exactly this pattern and is worth keeping; the flat `--bg` body is fine as the calm dominant field.
- **Avoid purple gradients on white** (explicit cookbook default to avoid) — that is precisely the current jarring combination. Our appbar keeps a purple gradient but pairs it with the warm-neutral canvas, and the dark appbar uses muted plum-navy rather than saturated purple.

### 2.7 How to apply these to Conteo screens (worked example)

For any new screen in this repo (e.g. a month detail, settlement form, forecast table):

1. Pull the tokens from the chosen palette; do not invent colors.
2. Establish hierarchy: the money number is the largest/heaviest element; use `--muted` for secondary labels; use `--accent` only for the single primary action.
3. Keep spacing on the repo cadence; give panels generous padding.
4. Use the appbar gradient as the one "atmosphere" moment; keep the body calm.
5. Verify contrast on the specific pairing you used (see §1.3) before shipping.

---

## 3. Writing good visual-craft prompts

This section tells a future agent/human how to prompt (themselves or another agent) so output follows this guideline. It is stack-agnostic; replace "the model" with "the agent."

**Use the three cookbook strategies verbatim, mapped to the four dimensions:**

1. **Guide specific design dimensions individually** — when reviewing/building, call out *typography*, *color*, *motion*, and *backgrounds* as separate axes and evaluate each on its own. Don't blur them into one vague "make it look nice."
2. **Reference concrete inspirations** — "draw from IDE themes and cultural aesthetics" — name one (e.g. a warm paper / candlelight palette, a specific theme family) rather than describing a mood abstractly. Be concrete but not prescriptive about exact hex.
3. **Call out the defaults to avoid** — explicitly forbid the generic list: generic fonts, purple-on-white clichés, predictable layouts, cookie-cutter components, and (second-order) Space-Grotesk-type convergences.

**A reusable prompt skeleton (paste-worthy, tool-agnostic):**
```
Design the following screen for the Conteo finance app using the tokens in
docs/research/color-scheme.md (Palette A). Requirements:
- COLOR: cohesive; use the CSS custom properties only; one dominant warm-neutral
  surface, one sharp purple accent (primary action / active state only).
- TYPOGRAPHY: distinctive faces, tabular figures for numbers, use extremes in
  weight and size (a 3x+ headline-to-body jump), never Inter/Roboto/system default.
- HIERARCHY: the money figure is the largest, darkest element; secondary data in
  --muted; structure/labels must encode real meaning, no decorative numbering.
- MOTION: at most one orchestrated moment; respect prefers-reduced-motion.
- BACKGROUND: keep the body calm; use the appbar gradient for atmosphere; no
  purple-on-white clichés.
- QUALITY: responsive to mobile, visible keyboard focus.
Verify contrast (ink/bg, ink/panel, muted/bg, accent-ink/accent) ≥ WCAG AA.
```

The source guidance stresses **prompting "at the right altitude"** (from the companion blog, citing their context-engineering article): give directional language, not low-level hardcoded hex — the altitude of this document, not line-by-line CSS — and not so vague it assumes shared context. Let the agent derive concrete values from the tokens.

---

## 4. Sources

### Primary
- **Claude Cookbook — *Prompting for frontend aesthetics* (Prithvi Rajasekaran, Anthropic), published 2025-10-21.**
  https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics
  Verified directly (full text read). Source of: the three prompting strategies; the `<frontend_aesthetics>` prompt (typography, color & theme, motion, backgrounds); the explicit "avoid" list (Inter/Roboto/Arial/system fonts; purple gradients on white; predictable layouts; cookie-cutter; Space-Grotesk convergence); "dominant colors with sharp accents outperform timid, evenly-distributed palettes"; "one well-orchestrated page load with staggered reveals"; isolated-prompting / theme-locking technique.
  Mirror (identical content, read): https://github.com/anthropics/claude-cookbooks/blob/main/coding/prompting_for_frontend_aesthetics.ipynb

- **Anthropic blog — *Improving frontend design through Skills* (Anthropic Applied AI team: Prithvi Rajasekaran, Justin Wei, Alexander Bricken, et al.), published 2025-11-12.** https://claude.com/blog/improving-frontend-design-through-skills
  Verified via web search (full post surfaced in search results; not every byte fetched in primary HTML). This is the blog the cookbook's playbook feeds into. Source of: skills/context-loading framing; "prompt at the right altitude"; the restated `~400 token <frontend_aesthetics>` prompt; the warning about converging to a *second* default; mapping aesthetic axes to implementable code. **Note:** this is a Claude-branded blog, but its *guidance* is tool-agnostic (prompt dimensions, altitude, avoid-list) and is used here only as the source of those general principles.

### Companion skill (Anthropic, same authors) — used for hierarchy/spacing/typography/motion guidance beyond the cookbook
- **anthropics/skills — `frontend-design/SKILL.md`.** https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md
  Verified via web search (content surfaced). Source of: "structure is information" / non-decorative numbering; "remove one accessory" / spend boldness in one place; responsive-to-mobile + keyboard focus + reduced-motion as quality floors; distinctive font pairing as a deliberate act; two-pass design (token plan first, then build). Used to strengthen the *process* guidance in §2.3–§2.6 and §3.
- Related Anthropic artifacts, same lineage, for reference: Claude Code **Frontend Design plugin** README, https://github.com/anthropics/claude-code/tree/main/plugins/frontend-design ; plugin listing, https://claude.com/plugins/frontend-design ; author LinkedIn post (2015-10-22), https://www.linkedin.com/posts/prithvi72_claude-is-better-at-frontend-design-than-activity-7386796219773403136-kOTw

### Accessibility / finance-UX color practice
- **W3C — WCAG 2.1** Success Criterion 1.4.3 (Contrast [Minimum]: ≥4.5:1 normal text / ≥3:1 large text) and 1.4.11 (Non-text Contrast: ≥3:1 for UI components / graphical objects). https://www.w3.org/TR/WCAG21/#contrast-minimum and https://www.w3.org/TR/WCAG21/#non-text-contrast — the contrast thresholds used in §1.3.
- **W3C — WCAG 2.2** (current recommendation) re-states 1.4.3/1.4.11 unchanged. https://www.w3.org/TR/WCAG22/
- **WebAIM — Contrast Checker** (the standard tool for verifying WCAG ratios). https://webaim.org/resources/contrastchecker/
- **Common finance-data dashboard guidance (secondary, used only for "tabular figures for aligned numbers" and "muted text for secondary labels"):** Money/table UIs conventionally use tabular/monospaced figures so columns align and figures scan quickly — a functional convention widely documented in typography guidance for dashboards (e.g. Google Fonts "tabular figures," https://fonts.google.com/knowledge/glossary/tabular_figures ) rather than an Anthropic claim. This is an inferred, functional-quality practice, not verified against a formal finance-accessibility standard.

### Verification notes
- **Verified directly (fetched primary HTML):** the cookbook page (full text), the current `globals.css`, `CONTEXT.md`.
- **Verified via web search results (full posts surfaced, but I did not byte-by-byte fetch the primary HTML):** the *Improving frontend design through Skills* blog, the `frontend-design/SKILL.md`, and the plugin README. Their guidance is quoted accurately from the surfaced content; if you need citation-grade certainty on a single sentence, fetch the exact URL.
- **Contrast ratios:** computed by me with the standard WCAG sRGB algorithm from the exact hex values in §1; they are exact for the listed pairs. They are *not* verified in-browser (no rendering environment), and they assume opaque colors — always re-check in a real browser if the palette is edited or rendered over transparency.
- **Could not verify:** whether the cookbook's own linked blog is *only* the *Improving frontend design through Skills* post (the cookbook page renders the blog as a separate, non-inline link); whether font loading via Google Fonts is acceptable for this self-hosted app (a deployment/cost decision, not a color decision); any formal accessibility standard *specifically for finance dashboards* beyond generic WCAG.

---

*End of document. Research-only; no source code was modified.*
