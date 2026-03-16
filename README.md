# Tax Filing Skill for Claude Code

This Skill helps Claude turn a folder of tax documents into a mostly-complete filing workflow: read the source docs, compute the return, fill the forms, and hand back a clear summary of what to review before filing.

## What It Does

- Reads W-2s, 1099s, brokerage statements, and prior-year returns
- Asks the missing filing questions Claude needs to finish the return
- Computes federal and state tax results, including capital gains and carryovers
- Downloads official blank PDF forms and fills them programmatically
- Verifies outputs and returns a human-friendly summary of refunds, forms, and next steps

## Installation

In Claude Code:

```
/plugin marketplace add alqz/claude-tax-filing
/plugin install tax-filing
```

## What It Looks Like

Start with a simple prompt:

![Starting prompt in Claude](docs/images/start-prompt.png)

Claude asks the follow-up questions needed to finish the return:

![Filing questions UI](docs/images/filing-questions.png)

It works through the filing steps and keeps track of progress:

![Workflow progress](docs/images/workflow-progress.png)

At the end, it gives you a clean summary of refunds, carryovers, and filled forms:

![Results summary](docs/images/results-summary.png)

## What You Get

- Filled PDF forms in `output/`
- A summary of federal and state results
- Any carryover values to save for next year
- A checklist of what to sign, review, and file

## What We've Learned

Skills are not just a single `.md` file anymore. They can also include scripts, code snippets, and example files, which makes them much more powerful.

## Contributing

This is a fork of [robbalian/claude-tax-filing](https://github.com/robbalian/claude-tax-filing). Contributions are welcome via PR.
