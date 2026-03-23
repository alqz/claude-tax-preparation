# Tax Preparation Skill for Claude

If you don't want to install this manually, just tell Claude:

```text
Install and use https://github.com/alqz/claude-tax-preparation
```

This Skill helps Claude prepare your tax return: read the source docs, compute the return, fill the official PDF forms, and hand back a clear summary of what to review before you file.

Works in both **Claude Code** and **Claude.ai**.

## What It Does

- Reads W-2s, 1099s, brokerage statements, and prior-year returns
- Asks the questions Claude needs to finish the return
- Computes federal and state tax results, including capital gains and carryovers
- Downloads official blank PDF forms and fills them programmatically
- Verifies outputs and returns a human-friendly summary of refunds, forms, and next steps

## Installation

### Claude.ai

1. Download `tax-preparation-cloud.skill` from the [latest release](https://github.com/alqz/claude-tax-preparation/releases).
2. Go to **Settings > Skills** and upload the `.skill` file.

Then start a new conversation and say something like:

```text
Help me do my taxes.
```

Claude will ask you to upload your tax documents (W-2s, 1099s, etc.) directly in the chat. It will also ask you to download and upload the blank IRS/state forms it needs to fill — it gives you the exact URLs.

### Claude Code

```
/plugin marketplace add alqz/claude-tax-preparation
/plugin install tax-preparation
```

### Differences Between Versions

The tax computation logic is identical. The differences are purely about how Claude interacts with the environment:

| | Claude.ai (`/tax-preparation-cloud`) | Claude Code (`/tax-preparation`) |
|---|---|---|
| **Tax documents** | You upload them in the chat | Reads from your local filesystem |
| **Blank IRS forms** | You download and upload them (Claude gives you the URLs) | Claude downloads them directly |
| **Filled forms** | Downloadable from the chat | Saved to `output/` in your project |
| **Web lookups** | Uses built-in web search tools | CLI-based |

## What It Looks Like

Start with a simple prompt:

![Starting prompt in Claude](docs/images/start-prompt.png)

Claude asks the follow-up questions needed to finish the return:

![Filing questions UI](docs/images/filing-questions.png)

It works through the preparation steps and keeps track of progress:

![Workflow progress](docs/images/workflow-progress.png)

At the end, it gives you a clean summary of refunds, carryovers, and filled forms:

![Results summary](docs/images/results-summary.png)

## What You Get

- Filled PDF forms ready for you to review and file
- A summary of federal and state results
- Any carryover values to save for next year
- A checklist of what to sign, review, and file

## Contributing

This is a fork of [robbalian/claude-tax-filing](https://github.com/robbalian/claude-tax-filing). Contributions are welcome via PR.
