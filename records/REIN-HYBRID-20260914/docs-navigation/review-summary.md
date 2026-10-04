# Hybrid documentation and navigation review

Scope: existing Chinese content site (0a). No redesign or token-system expansion.

Changed documentation/navigation paths in the hybrid worktree:

- `DECISIONS.md` — D9 records Rust core authority and the TypeScript host/plugin boundary.
- `README.md`, `docs/index.md`, `docs/about.md`, `docs/toc.md` — 01–03 TypeScript entry, optional Rust hello, 05–07 Rust core with historical TS comparison, and 08–16 hybrid roadmap language.
- `docs/chapters/05.md`, `06.md`, `07.md` — current Rust core links and historical comparison framing.
- `docs/chapters/06-plugin.md` — full transition tutorial, marked draft pending core loop/disconnect verification.
- `docs/chapters/15.md`, `16.md` — future plugin/MCP/hooks and domain integration framing.
- `docs/milestones/02.md`, `docs/appendices/a2.md` — current hybrid route framing.
- `docs/.vitepress/theme/SourceVersionSwitch.vue` — edition switch renders only when a real TS/Rust pair exists.
- `docs/.vitepress/theme/sourceVersionState.test.ts` — negative coverage for 05–07 core/legacy routes.
- `contracts/README.md`, `chapter-snapshots/README.md` — protocol boundary and historical bundle distinction.

Checks:

- `npm run build` — passed; VitePress client/server build and page rendering completed.
- `node --import tsx --test docs/.vitepress/theme/sourceVersionState.test.ts` — 4 tests passed.
- Raw outputs: `npm-run-build.stdout`, `nav-test.stdout`.

The 06 Plugin text is intentionally a transition draft until the Rust core loop, side-effect disconnect ledger, exactly-once handling, and crash tests are verified. No formal experiment was run.
