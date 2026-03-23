# Testing the Tax Preparation Skill

## Overview

The skill is tested by running independent Claude Code CLI sessions against a
prepared test directory containing real tax documents. Each agent receives a
minimal prompt and must produce a complete return. Results are compared against
a verified reference return.

## Test Setup

### Directory Structure

```
/tmp/tax-test-2025/
├── run-tests.sh          # launches 4 agents in parallel
├── logs/                 # agent output logs
│   ├── agent-{a,b,c,d}.log
│   └── status.txt        # completion timestamps
├── taxpayer_profile.md   # cleaned profile (no computed results)
├── test-prompt.md        # documents the prompt and setup
└── agent-{a,b,c,d}/     # one directory per agent
    ├── source/           # symlink → real source documents
    ├── forms/            # symlink → blank PDF forms
    ├── taxpayer_profile.md  # copy of cleaned profile
    ├── work/             # agent writes intermediate files here
    └── output/           # agent writes filled PDFs here
```

### Taxpayer Profile

The `taxpayer_profile.md` is a cleaned version of the real taxpayer's data
that contains only raw input facts — no computed results, no filing decisions,
no depreciation schedules, no USD conversions. The agent must derive everything.

Items deliberately excluded (agent must compute):
- Standard vs. itemized deduction decision
- CA Pease limitation analysis
- Depreciation schedules and MACRS classifications
- USD conversions of Canadian amounts
- Allocation percentages for shared expenses
- Exchange rates

### Prompt

All agents receive the same prompt:

```
Before starting, read the instructions at ~/.claude/skills/tax-preparation/SKILL.md
and follow them.

Do my taxes. All of my source documents and information are in this folder.
Please prepare and file my 2025 federal and California tax returns. All
necessary information is in the provided documents; proceed through all
phases without waiting for additional input.
```

Key design decisions:
- Agents are told to read the skill file (since CLI `-p` mode doesn't
  auto-load skills)
- "All necessary information is in the provided documents" prevents the
  agent from blocking on the Phase 1c questionnaire
- No hints about expected results, known pitfalls, or which scripts to use
- The agent doesn't know it's being tested

### Launch Script

`run-tests.sh` launches 4 parallel agents via:

```bash
npx -y @anthropic-ai/claude-code -p "$PROMPT" \
  --dangerously-skip-permissions \
  --output-format json \
  --max-turns 150
```

- `--dangerously-skip-permissions`: agents need Bash/Write for Python scripts
- `--max-turns 150`: enough for the full workflow
- `--output-format json`: output captured at end (not streamed)

### Why CLI, Not Subagents

Earlier testing used the Agent tool to spawn subagents. This had two problems:
1. **Permission issues**: 75% of subagents couldn't use Bash/Write tools,
   even with `bypassPermissions` mode, falling back to LLM reasoning
2. **Skill loading**: subagents don't inherit the parent's skill configuration

Running independent CLI sessions with `--dangerously-skip-permissions`
resolves both issues.

## Evaluating Results

### Extracting Key Values

After agents complete, extract values from their workbooks:

```bash
cd /tmp/tax-test-2025/agent-X
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('work/tax_computations.xlsx', data_only=True)
for sheet in wb.sheetnames:
    ws = wb[sheet]
    for row in ws.iter_rows(values_only=False):
        vals = [str(c.value) if c.value is not None else '' for c in row]
        print(f'{sheet}: {chr(9).join(vals)}')
"
```

### Key Metrics

| Metric | Source |
|--------|--------|
| Federal owed | Federal Return sheet, line 37 |
| CA owed | CA Return sheet, amount owed |
| AGI | Federal Return sheet, line 11 |
| Taxable income | Federal Return sheet, line 15 |
| Deduction type/amount | Federal Return sheet, line 12-14 |
| FTC | FTC sheet or Federal Return line 20 |
| Line 25c | Federal Return sheet, line 25c |
| CA AGI | CA Return sheet, line 16-17 |
| CA deduction | CA Return sheet, line 18 |
| CA Pease applied | CA Deductions section |
| HSA add-back | CA Return sheet, additions |

### Error Classification

Common error types and their structural fixes:

| Error | Structural fix | Status |
|-------|---------------|--------|
| Wrong standard deduction | `extract_tax_tables.py` | Fixed |
| CA Pease limitation missed | `extract_tax_tables.py` + skill instructions | Fixed |
| FTC QDCG adjustment wrong | `compute_ftc.py` | Fixed |
| Wrong federal brackets | Tax Tables sheet (written, auditable) | Detectable |
| Missing 1099-B category | Source reconciliation in `validate_return.py` | New |
| Line 25c missing | Skill mentions Form 8959 → 1040 25c | Partially fixed |
| CA HSA add-back missed | Skill state non-conformity section | Partially fixed |
| CA exemption phase-out | Form instructions (agent must read) | Not structural |

### Running Validation

```bash
cd /tmp/tax-test-2025/agent-X
python3 path/to/scripts/validate_return.py work/tax_computations.xlsx --forms-dir forms/
```

## Monitoring

Check progress while agents are running:

```bash
# File counts
for agent in a b c d; do
  echo "agent-$agent: $(find /tmp/tax-test-2025/agent-$agent/work \
    /tmp/tax-test-2025/agent-$agent/output -type f | wc -l) files"
done

# Completion status
cat /tmp/tax-test-2025/logs/status.txt

# Cross-directory access (agents should stay in their own folder)
for pid in $(pgrep -f "claude.*max-turns"); do
  lsof -p $pid 2>/dev/null | grep -v "agent-" | grep "tax-test"
done
```
