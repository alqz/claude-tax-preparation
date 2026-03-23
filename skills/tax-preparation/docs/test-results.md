# Tax Skill Test Results — 16 Agent Runs

## Reference Values (verified return)
- Federal owed: **$11,437** | CA owed: **$2,891** | Combined: **$14,328**
- FTC: $1,247 | QDCG tax: $18,563 | Std ded: $15,750 | CA AGI: $143,819

## Results by Batch

### Batch 1 (agents 1-4): Explicit test instructions, told which scripts to use
| Agent | Completed? | Fed owed | CA owed | Std ded | Pease | HSA | FTC | Line 25c |
|-------|-----------|---------|--------|---------|-------|-----|-----|----------|
| 1 | Script only | — | — | $15,750 | ✓ | ✓ | — | — |
| 2 | Full | $8,923 | $3,417 | $15,750 | ✓ | ✓ | $83 | ✓ |
| 3 | Full | $11,502 | $2,183 | $15,750 | ✓ | ✓ | ~$2,718 | ✓ |
| 4 | Full | $10,871 | $2,891 | $15,750 | ✓ | ✓ | $1,904 | ✓ |

### Batch 2 (agents 5-8): Explicit test instructions + compute_ftc.py available
| Agent | Completed? | Fed owed | CA owed | Std ded | Pease | HSA | FTC | Line 25c |
|-------|-----------|---------|--------|---------|-------|-----|-----|----------|
| 5 | Script only | — | — | $15,750 | — | — | — | — |
| 6 | Pending | — | — | — | — | — | — | — |
| 7 | Blocked | — | — | — | — | — | — | — |
| 8 | Full | $6,127 | $2,934 | $15,750 | ✓ | ✗ | $1,103* | ✓ |

*Agent 8 used compute_ftc.py (QDCG adjustment applied) but had wrong SALT cap

### Batch 3 (agents 9-12): Realistic prompt, user answers in prompt, no taxpayer profile
| Agent | Completed? | Fed owed | CA owed | Std ded | Pease | HSA | FTC | Line 25c |
|-------|-----------|---------|--------|---------|-------|-----|-----|----------|
| 9 | Text only | $14,281 | $1,673 | $15,000 | ✗ | ✗ | $1,239 | ✗ |
| 10 | Text only | $10,934 | $2,448 | $15,000 | ✗ | ✗ | $1,587 | ✗ |
| 11 | Text only | $11,453 | $2,451 | $15,000 | ✗ | ✗ | $1,218 | ✓ |
| 12 | Text only | $9,682 | ~$1,950 | $15,000 | ✗ | ✗ | $2,713 | ✗ |

### Batch 4 (agents 13-16): Realistic prompt + taxpayer profile (contains computed answers)
| Agent | Completed? | Fed owed | CA owed | Std ded | Pease | HSA | FTC | Line 25c |
|-------|-----------|---------|--------|---------|-------|-----|-----|----------|
| 13 | Text only | $14,352 | $2,764 | $15,750 | ✓ | ✗ | $1,192 | ✗ |
| 14 | Text only | $14,197 | $2,773 | $15,750 | ✗ | ✗ | $1,187 | ✗ |
| 15 | Text only | $11,461 | $3,029 | $15,750 | ✓ | ✓ | $1,192 | ✓ |
| 16 | Text only | $14,387 | $2,934 | $15,750 | ✓ | ✗ | $1,149 | ✗ |

## Error Rates Across All Completed Agents

| Error | Batch 3 (no fixes) | Batch 4 (with profile) | Batch 1-2 (scripts) |
|-------|-------------------|----------------------|-------------------|
| Wrong std deduction | 4/4 (100%) | 0/4 (0%) | 0/3 (0%) |
| CA Pease missed | 4/4 (100%) | 1/4 (25%) | 0/3 (0%) |
| CA HSA add-back missed | 4/4 (100%) | 3/4 (75%) | 1/3 (33%) |
| Line 25c missing | 3/4 (75%) | 3/4 (75%) | 0/3 (0%) |
| FTC QDCG adj missed | 4/4 (100%) | 4/4 (100%) | 2/3 (67%) |
| SALT cap wrong | 0/4 | 0/4 | 1/3 (33%) |

## What Fixed What

| Fix | Target error | Result |
|-----|-------------|--------|
| extract_tax_tables.py | Wrong std deduction | **100% fixed** (when tools work) |
| extract_tax_tables.py | Wrong CA values | **100% fixed** (when tools work) |
| taxpayer_profile.md | Std deduction | 100% fixed (but may be reading answer, not computing) |
| taxpayer_profile.md | CA Pease | 75% fixed |
| Skill state non-conformity section | CA HSA add-back | 25-67% fixed (inconsistent) |
| compute_ftc.py | FTC QDCG adjustment | **100% fixed when used** (only 1 agent could use it) |
| Skill mentions Line 25c | Excess Medicare w/h | Not fixed (75% error rate persists) |

## Infrastructure Issue

Tool permission denials prevented most agents from running scripts. Only 4 of 16 agents
could execute Python code. When scripts were accessible:
- extract_tax_tables worked perfectly
- compute_ftc produced correct results (1 agent used it)
- validate_return caught wrong values
- preflight_check enforced instruction reading

When scripts were inaccessible, agents fell back to LLM reasoning and made the same
errors the scripts were designed to prevent.

## Remaining Gaps (not fixed by any structural mechanism)

1. **FTC QDCG adjustment** — 100% error rate when compute_ftc.py unavailable.
   The adjustment (IRC 904(b)(2)(B)) is too complex for LLM reasoning.

2. **Line 25c excess Medicare withholding** — 75% error rate. Agents don't connect
   Form 8959 Part V to 1040 Line 25c. No structural fix yet.

3. **CA HSA add-back** — 50%+ error rate. Agents know HSA exists but don't apply
   the CA non-conformity add-back. Reading instructions would catch this.

4. **SALT cap phase-down** — 1 agent used wrong SALT cap. The OBBB Act
   SALT provision is complex (raised cap but phases back for high income).
