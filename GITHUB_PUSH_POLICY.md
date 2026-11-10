# Xenors GitHub Push Policy

Effective: 2026-11-11

## Purpose

This repository is used from a shared ChatGPT workspace. Manual assistant-initiated changes must not be able to reach the production `main` branch only because someone can use the shared chat account.

## Manual changes

For any future user-requested website, SEO, code, design, configuration, content, redirect, analytics, or repository change initiated interactively through ChatGPT:

1. Do **not** push directly to `main`.
2. Create a task-specific branch.
3. Commit the requested changes to that branch.
4. Open a pull request targeting `main`.
5. Leave the pull request unmerged for the repository owner, `@Ashok8601`, to review and merge in GitHub.
6. A request made only inside the shared ChatGPT account is not sufficient authorization to bypass this policy.
7. Do not store passwords, passphrases, access tokens, API keys, recovery codes, or other secrets in this repository or in assistant memory.

## Automatic publishing exception

The existing scheduled Xenors SEO-post automation is explicitly allowed to publish its scheduled article, WebP assets, and contextual internal-link updates directly to `main`.

This exception is limited to the scheduled publishing workflow. It does not authorize unrelated code, security, configuration, redirect, analytics, or site-wide changes.

## Emergency / policy changes

Changes to this policy should be made directly by the repository owner in GitHub, or through a pull request that the repository owner manually merges.

## Why GitHub approval instead of a chat password?

A password typed into a shared chat can be exposed through chat history and cannot be securely stored or verified by the assistant as an authentication system. GitHub account approval provides a real external identity boundary.
