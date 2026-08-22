# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This repository currently has **no application code**. The original project — a CLI that checks unread mail on Gmail and Naver over IMAP (`mail_checker/`, `main.py`, `tests/`) — was deliberately deleted (PR #3, commit `29928ec`). The implementation is still fully readable via `git show <commit>:<path>` on commits before `29928ec`, or `git log --diff-filter=D --summary` to find exactly what was removed.

What's actually in the tree now:
- `README.md` — one-line status note pointing back to git history
- `notes/git-basics.md` — a running Git/GitHub workflow log, built up while practicing branch/commit/push/PR/merge/revert/Issues in this repo
- `.claude/` — Claude Code on the web session tooling, described below

There is currently nothing to build, lint, or test. Don't assume the old `mail_checker` structure is still present — verify against the working tree first.

## Claude Code on the web session setup

`.claude/settings.json` registers `.claude/hooks/session-start.sh` as a `SessionStart` hook. The hook only runs in remote sessions (`CLAUDE_CODE_REMOTE=true`; no-ops locally) and installs `requirements.txt` if one exists. It's guarded to no-op when `requirements.txt` is absent (as it is now) so it stays safe to keep in place for whenever application code — and its `requirements.txt` — comes back.

## Branch/PR convention

This repo's default branch is `claude/google-naver-mail-checker-kcfix9`, not `main`. PRs target that branch. Work happens on short-lived feature/practice branches created off it and merged back in.
