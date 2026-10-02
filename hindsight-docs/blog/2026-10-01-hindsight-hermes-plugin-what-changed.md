---
title: "What Changes Now That Hindsight Is a Hermes Plugin"
authors: [benfrank241]
slug: "2026/10/01/hindsight-hermes-plugin-what-changed"
date: 2026-10-01T12:00
tags: [hindsight, hermes, nous-research, plugins, memory-provider, migration]
description: "Hindsight used to ship inside Hermes. It now installs from the plugin catalog. Your settings and memory are untouched, but one thing genuinely changed: where updates come from."
image: /img/blog/migrate-hindsight-hermes.png
hide_table_of_contents: true
---

![Hindsight now installs from the Hermes plugin catalog rather than shipping inside Hermes](/img/blog/migrate-hindsight-hermes.png)

Until late September, Hindsight shipped inside [Hermes Agent](https://github.com/NousResearch/hermes-agent) as a bundled memory provider at `plugins/memory/hindsight/`. It does not any more. Nous Research moved every memory provider out of the Hermes core tree, and Hindsight was the first one out.

Most of what you read about this will tell you how to migrate. That part is short, because Hermes does it for you. The more useful question is what is actually different now, and there is exactly one answer that matters.

<!-- truncate -->

## TL;DR

- **Your setup did not change.** Settings, memory bank, API key, config file and the three tools are all untouched.
- **The code moved.** The plugin lives in the Hindsight repository and is maintained by us.
- **The one real change: updates.** `hermes update` no longer moves the plugin. Memory improvements used to ride along with Hermes releases, and they do not any more.
- **You now choose your version:** follow the catalog pin, freeze a commit, or track our `main`.
- **Bugs now go to us**, and fixes ship on a pin bump rather than an unrelated release cycle.

## Start with what did not change

Worth getting out of the way, because "we moved your integration" usually comes with a weekend attached.

Nothing about your memory moved. The plugin is the code that talks to Hindsight, not the place your memories live, so whether your bank is on Hindsight Cloud, a local embedded daemon or an instance you run yourself, it sits exactly where it sat.

| Thing | Still where it was |
|---|---|
| Provider setting | `memory.provider: hindsight` in `config.yaml` |
| Plugin config | `~/.hermes/hindsight/config.json` |
| API key | `~/.hermes/.env` |
| Memory bank | Cloud, local daemon, or your own instance |
| Tools | `hindsight_retain`, `hindsight_recall`, `hindsight_reflect` |

The migration itself is a plugin install, not a data operation. Run `hermes update`, or just start an agent, and Hermes resolves the provider name against the catalog and installs it. You get one line:

```
✓ Memory provider 'hindsight' moved out of core — installed its plugin from the
  catalog (your memory.hindsight settings and data are unchanged).
```

Afterwards the plugin sits in `~/.hermes/plugins/hindsight/` and your `config.yaml` picks up `plugins.enabled: [hindsight]`. If you have turned off `security.allow_lazy_installs`, Hermes will not install anything for you and logs a one-line instruction to run `hermes plugins install hindsight` yourself.

## What the plugin actually is

It is worth being concrete about the split, because it is what makes "your memory did not move" more than a reassuring phrase.

The plugin is a **memory provider**: a small piece of Python that Hermes loads and calls at defined moments. Before each turn it can call `recall` and put what comes back into the model's context. After a turn it can call `retain`. It exposes three tools the model can invoke directly. That is the whole job, and it is a few hundred lines of client code plus a config schema.

Everything underneath is Hindsight: the extraction that turns a conversation into facts, the entity resolution that recognises the same person across sessions, the consolidation that folds repeated facts into observations, the retrieval that decides what comes back. None of that is in the plugin, and none of it ever shipped inside Hermes. It runs on Hindsight Cloud, in a local daemon the plugin starts for you, or on an instance you host.

So the thing that moved repositories is the connector. The memory system was always somewhere else, which is why a change of this size can leave your bank untouched.

It also explains the shape of the three modes you can run in. `cloud` points the connector at Hindsight Cloud. `local_embedded` has the plugin start and supervise a local daemon with its own PostgreSQL, idling it after five minutes of inactivity. `local_external` points at an instance you already run.

Same connector, three places for the memory to live. Which is also why the mode you are in determines how much the move could possibly affect you: a cloud user's memory was never on their machine to begin with, and an embedded user's daemon is started by the plugin but is not part of it.

## Where the code lives now

The bundled directory is gone from `hermes-agent`. The plugin lives in [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight/tree/main/hindsight-integrations/hermes), maintained by the Hindsight team, and Hermes installs it from its plugin catalog.

The catalog entry is the part worth understanding, because it is doing more work than it appears to. It does not point at our repository and track it. It pins a **specific commit** that Nous has reviewed. Your installed copy is that commit until the pin moves.

You can see exactly what you got:

```bash
cat ~/.hermes/plugins/.install-metadata.json
```

which records the catalog entry, the source repository and the resolved commit.

## The one thing that genuinely changed

Here is the part to internalise, and it is a habit rather than a command.

**`hermes update` does not update the plugin.** It reinstalls the plugin's Python dependencies and leaves the checkout exactly where it is. Nothing updates the plugin on its own.

When the provider shipped inside Hermes, its release cycle was Hermes' release cycle. Updating Hermes updated your memory layer, whether you thought about it or not. That is no longer true, and if you came from the bundled provider it is the assumption to drop.

What replaces it is a choice you did not have before.

### Follow the catalog pin

The default, and the right answer for almost everyone. This is what `hermes plugins install hindsight` gives you: the commit Nous reviewed.

```bash
hermes plugins update hindsight
```

`hermes plugins list` flags the plugin `update_available` once your installed commit differs from the catalog's. Note that re-running `plugins install` does **not** update it — it refuses with "already exists". `plugins update` is the command that re-pins.

### Freeze a specific commit

For a version you choose and hold:

```bash
hermes plugins install vectorize-io/hindsight/hindsight-integrations/hermes \
  --force --ref <40-character-commit-sha>
```

Replace the whole placeholder, angle brackets included. `--ref` takes a full 40-character SHA and rejects tag names, so take the SHA from the [release notes](https://github.com/vectorize-io/hindsight/releases) rather than typing a version number. A `--ref` install is marked pinned, and `plugins update` will deliberately refuse to move it.

### Track our development branch

For a fix before it reaches the catalog:

```bash
hermes plugins install vectorize-io/hindsight/hindsight-integrations/hermes
hermes plugins update hindsight
```

Installed from the source path rather than the catalog name, the same update command becomes a git pull of our `main`. Unreviewed by definition. Useful when you are chasing something specific with us, not what we would run in production.

## Two timing facts that will otherwise confuse you

**A fix we merge is not a fix you have.** The catalog pin is the release boundary. Our merge is step one; the pin bump is what reaches you, and that takes a follow-up change to `hermes-agent`. If you are waiting on something, you are waiting on the pin, not on us.

**Hermes re-fetches the catalog at most once every six hours.** So even after a pin moves, a freshly released version can take that long to show up as available to you. If something we announced is not there yet, this is usually why, and it is not worth a bug report until the six hours are up.

## What you get in exchange

A memory provider living in someone else's tree moves at that tree's pace. A bug in the Hindsight connector had to be fixed by people whose project is an agent, not a memory system, and the fix reached you when Hermes next shipped. That is a slow path for code sitting in the hot loop of every turn your agent takes.

Now the people who build the memory system maintain the thing that talks to it. Issues go to the [Hindsight repository](https://github.com/vectorize-io/hindsight/issues), we fix them there, and they ship on the next pin rather than on an unrelated release.

You also get the three-way choice above, which did not exist when the provider was bundled. If a fix matters enough, you can run it the day it lands instead of waiting; if stability matters more, you can hold a commit and know nothing will move it. Neither was available when your memory layer shipped on someone else's release train.

## Installing fresh

If you are setting up rather than migrating:

```bash
hermes plugins install hindsight
hermes memory setup           # select "hindsight"
```

Hindsight is in the catalog, so the name is all you need on the first line.

**Do not skip the second command.** Installing the plugin does not switch it on. Hermes treats memory providers as `kind: exclusive`, and its plugin-enable gate deliberately skips them, so `hermes plugins enable` is not what activates a provider. What activates one is `memory.provider` in `config.yaml`, which setup writes for you. This catches people regardless of the migration, and it is the single most common reason a correctly installed plugin appears to do nothing.

Note also that `plugins install` prompts before enabling. Pass `--enable` or `--no-enable` to skip the prompt in a script.

## One other change in the same window

Unrelated to the move, but it landed close enough to be confused with it: `recall_types` now defaults to **observations only**, where it previously returned all three fact types.

Observations are the consolidated layer — deduplicated beliefs with proof counts, rather than the individual facts underneath them. For per-turn context injection they are denser per token. If you want the old behaviour, set `"recall_types": "observation,world,experience"` in `~/.hermes/hindsight/config.json`. It governs both auto-recall and the `hindsight_recall` tool.

## If something looks wrong

A short list of the things that actually come up.

**`Timeout context manager should be used inside a task`** — you have `hindsight-embed` 0.10.0, which breaks `local_embedded` mode. This affects installs between 14 and 21 September 2026. Run `hermes update`, which is the fix here because the problem is a dependency rather than the plugin code. Cloud and `local_external` are unaffected.

**The provider reports "not available" in embedded mode** — you installed the plugin but skipped `hermes memory setup`. Embedded mode needs the `hindsight-all` package rather than just the client, and the setup wizard installs it.

**Installed and enabled, but memory does nothing** — `plugins enable` does not activate a provider. Check `memory.provider`, or run `hermes memory setup`.

**`plugins update` says there is nothing to do** — either you are pinned with `--ref`, in which case it refuses by design, or the catalog has not re-fetched yet.

**`hermes update` appears to hang** — it is waiting for input. It prompts before preparing a plugin's Python dependencies, and again about restoring stashed local changes if your Hermes tree has modifications.

**Recall fails with an HTTP status rather than a plugin error** — a 401, 402 or 403 is Hindsight rejecting the request, not the plugin misbehaving. Check your API key and account status.

## Frequently asked questions

**Do I need to migrate manually?**
No. Hermes does it on `hermes update` or on first agent start, provided `security.allow_lazy_installs` is on, which is the default.

**Will I lose any memories?**
No. Nothing about your bank is read or written during the migration.

**Does this affect the Hermes desktop app?**
It migrates the same way, on first agent start. Desktop users configure Hindsight entirely in Settings → Memory & Context and never touch the plugin layer. Desktop supports Cloud and Local External modes only.

**Can I keep using the bundled provider?**
Not once you update past the removal. While both existed the bundled copy won, because provider lookup goes bundled, then `~/.hermes/plugins/`, then project, then entry point, first hit wins.

**How do I tell which version I am on?**
`hermes plugins list` shows the installed version and flags `update_available`. `~/.hermes/plugins/.install-metadata.json` shows the resolved commit and whether you are pinned, which is what actually decides whether `plugins update` will move you.

**Where do I report a bug now?**
The [Hindsight repository](https://github.com/vectorize-io/hindsight/issues).

## Learn more

- [Hermes Agent integration reference](https://hindsight.vectorize.io/sdks/integrations/hermes) for the full configuration surface
- [Hermes Desktop](https://hindsight.vectorize.io/sdks/integrations/hermes-desktop) for the settings-only path
- [Does Hindsight + Hermes = AGI?](https://hindsight.vectorize.io/blog/2026/09/25/hindsight-hermes-plugin-catalog) for the shorter, more opinionated version
- [Give Every Hermes Bot Its Own Memory](https://hindsight.vectorize.io/blog/2026/08/18/hermes-bot-mode-memory) on per-bot bank isolation
