# Research Epic Manager | Agent Skills

Autonomous research as an agent skill: This repo contains a collection of agent 
skills which enable an agent to run scientific research projects, from idea to 
manuscript. 

In order to organise the long-horizon work of a research project, we use an
Agile-inspired tracking system. Plain markdown files (`EPIC.md`, `ISSUE.md`, `comments/*.md`) track all work, keeping orchestration and revision documents 
separate from project files. Agent skills encode the bookkeeping of this system,
operating completely within the local file system. Human feedback is integrated naturally, from agent conversations → issue comments. 

The core "tracker" skills are highly flexible and are useful for organising any long-horizon project. Hence, the "research project management" component is 
defined as a 
specialised "epic manager" skill — to define the lifecycle of what issues need 
to be generated throughout the project from idea, development and
revisions. 

## Installation

### DeepSeek Harness (DSH)

1. Symlink or copy `skills/` into your discovery root (`.dsh/skills` under
   your workspace root).
2. Paste `AGENTS.md` into your tracker root (`EPICS_ROOT`, default
   `/workspace/epics/`); the copy inside `skills/` stays with the skill
   directory, and the root copy is what the harness reads as workspace
   instructions. If your layout differs, edit the two path definitions in
   `skills/AGENTS.md`.

### Other harnesses

> These agent skills are **not harness-agnostic**. Currently, only DSH has been tested.

That being said, there is actually no hard dependency on DSH. To 
install in your harness:

1. Copy `skills/` and `AGENTS.md` into your harness-specific locations. 
2. Overwrite the DSH-native sub-agent dispatch mechanics in  `issue-subagent-orchestration` and `research-project-epic-manager` skills for 
your harness-specific conventions. 

## Skill catalog

| Skill | One-liner |
|---|---|
| `add-epic` | Create an epic container (directory + `EPIC.md`) |
| `add-issue` | Add an issue (draft-first lifecycle + readiness gate → `open`) |
| `add-comment` | Append an anonymous, chronological comment |
| `issue-manager` | Protocol for a chat working an issue (roles, dispatch, verification) |
| `issue-subagent-orchestration` | DSH-native: documents the harness's delegation tools (`subagent`, `workflow`, `send_message`, `job_output`, `interrupt_agent`) |
| `research-project-epic-manager` | Specialised epic manager (DSH-native dispatch mechanics): spins up issues + issue managers to take projects through a 5-phase Scope → Generate → Dispatch → Collect → Synthesize loop, with gated verdicts |

**DeepSeek-Harness-specific bits:** `skills/issue-subagent-orchestration/SKILL.md`
is harness-native: it documents the harness's delegation tools (`subagent`,
`workflow`, `send_message`, `job_output`, `interrupt_agent`). The
`research-project-epic-manager` skill's dispatch mechanics (the Phase-C brief
templates in its `references/`) likewise reference the harness's delegation
tools (`subagent`, `job_output`, `send_message`, `interrupt_agent`) and must
be mapped onto another runtime's delegation tools.

## User guide

Start a whole project by asking the chat to "manage a research project":

> Manage a research project - create a workshop paper under
> https://www.climatechange.ai/events/neurips2026 as the theme. Limitations:
> CPU-only data analysis. Deliverable: a 4-page PDF with workshop formatting.

The orchestrator takes a **research brief** and a **project config** (start
from `skills/research-project-epic-manager/assets/project-config-template.yaml`)
and runs five phases: scoping, just-in-time issue generation per stage,
dispatch of coder/reviewer children, staging/collecting of stage outputs into a
flat `project.json` manifest, and synthesis of the deliverable.

**Watching it:** everything is files — `EPIC.md` (issue index),
`project.json` (manifest), the append-only `verdict_history` on the
orchestration log, and the project workspace plus the `project.json`
manifest's append-only `artifacts` map. Any "status of epic `<X>`?" works.

**You, mid- or post-run:** in the default `autonomous` mode the run does not stop for
approval — it decides, records the decision, and proceeds. Your steer lands as
an anonymous `[human-directive:<digest>]` comment on the affected issue, dated
and routed, appended *before* it is acted on; project-level input also lands on
the orchestration log. Prefer approval points? Set `autonomy.mode: gated` in
the config. Either way, genuine blockers (exhausted review loops, catastrophic
failures, missing route targets) surface as blocked issues with manager
notices; unblock them with a directive or by working the issue yourself
("work on issue `<X>`" makes that chat the issue manager, who verifies before
closing anything).

> Act as issue manager for `<path to issue>`: ... describe a request/comment/question

Or talk directly to the epic manager:

> Include a constraint to this project ... 

## Comparison to other systems

The table grades the 2024–2026 cohort of autonomous research systems.

**How to read the marks**

| Mark | Meaning |
|---|---|
| ✅ | yes — demonstrated in the surveyed sources |
| 🟡 | partial — some form exists, or a claim is not independently verified |
| ❌ | no — nothing found |
| ❔ | not recorded — absence of evidence (not evidence of absence) |

Column scales: **Setup** (entry requirement you face): 📖 open source · 🔒 closed · 🧪 paper-only prototype · ❔ not recorded • **Lifecycle coverage** (phases that run unaided): ✅ full loop · 🟡 decisive subset · ❌ single phase • **Lifecycle auditability** (can you reconstruct how the run proceeded): ✅ decision record · 🟡 artifacts only · ❌ nothing inspectable · ❔ not recorded • **Self-improvement** (does the system improve itself, weakest→strongest): 🔄 object-level · 🧠 memory-informed · 🎓 weight-level · 🪞 protocol-level. 

| System | Setup | Lifecycle coverage | Lifecycle auditability | Self-improvement |
|---|---|---|---|---|
| **research-epic-manager (this repo)** | 📖 six SKILL.md files + stdlib batteries; Python 3 only | ✅ full loop — scoping → synthesis, gates included | ✅ decision record — append-only verdict history, executed backward invalidation | 🪞 protocol-level — gate failures become findings; fixes tracked in-tracker |
| AI-Scientist v1/v2 | 📖 OSS repo + LLM keys + GPU | ✅ full loop — ideation → experiment → write-up → LLM review | 🟡 artifacts only — run dirs + cost tracking | 🔄 object-level — tree search within one paper |
| CycleResearcher | 📖 open-weight models | 🟡 writing + review half | 🟡 artifacts only — training-loop records | 🎓 weights — retrains its own models |
| Agent Laboratory / AgentRxiv | 📖 OSS; frontier-model dependent | 🟡 lit review → experiment → report | 🟡 artifacts only — feedback lives in conversation | 🔄 object-level — co-pilot steering |
| STORM / Co-STORM | 📖 OSS pip package | ❌ pre-writing only | 🟡 artifacts only — mind map persists | ❌ none recorded |
| DeepScientist | ❔ containerised; month-scale | 🟡 hypothesise → verify → analyse tiers | 🟡 artifacts only — Findings Memory; forward-only | 🧠 memory — failures retained across runs |
| Kosmos | ❔ not recorded | 🟡 long-horizon discovery; write-up unclear | 🟡 artifacts only — world model summaries each cycle | 🧠 memory — world model steers next cycle |
| ASI-Arch | ❔ not recorded — ~20k GPU-hours | ❌ architecture discovery only | 🟡 artifacts only — every trial archived, searchable | 🧠 memory — trial archive feeds future cycles |
| CodeScientist | 🧪 release not recorded | 🟡 ideation → construct → report | 🟡 artifacts only — judge-scored stages | ❔ not recorded |
| Co-Scientist | 🔒 limited access | 🟡 hypothesis + protocol design | 🟡 artifacts only — debate records + Elo | 🔄 object-level — tournament evolution |
| Robin | 🔒 proprietary | 🟡 propose → analyse loop; humans run the lab | ❔ not recorded | 🔄 object-level — re-propose iterations |
| Zochi | 🔒 closed, doc-only internals | 🟡 claimed full loop — unverified | ❌ nothing inspectable | ❔ not recorded |
| FunSearch | 🔒 closed — Nature paper | ❌ search-discovery only | ❔ not recorded | 🔄 object-level — evolving program islands |
| ResearchAgent | 🧪 no public release | ❌ ideation only | 🟡 artifacts only — ~5 scored rounds described | 🔄 object-level — reviewer-scored refinement |

## Validation

Sanity check: ask the LLM to run the validation batteries (each skill's
`scripts/test_*.py`) and expect exit code 0; or ask the LLM to explain how
the system works and check the explanation against the docs. The batteries
are stdlib-only Python and self-deleting: `test_add_epic.py`,
`test_add_issue.py` and `test_add_comment.py` drive the real skill scripts
against a scratch epic that removes itself on exit (unless `--keep`), and
`test_lifecycle.py` additionally enforces cross-cutting invariants
(discovery roots, git hygiene, layout, and the ASCII-only rule for .md
files). The `research-project-epic-manager` skill's own batteries are
`scripts/validate_execution.py` and `scripts/validate_protocol.py`.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md): MIT license, collective field-level
attribution, anonymous tracker comments vs. normal git history, the
ASCII-only rule for agent-facing files, and how to validate a change.