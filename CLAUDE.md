# Development Notes

## Skill Sync

There are two versions of the tax-preparation skill that must be kept in sync:

1. `skills/tax-preparation/SKILL.md` — Claude Code version
2. `skills/tax-preparation-cloud/SKILL.md` — Claude.ai version

The two versions differ in environment-specific details (tool names, file access patterns) but share the same tax logic. When editing the skill, apply changes to both.
