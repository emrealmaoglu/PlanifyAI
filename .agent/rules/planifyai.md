---
trigger: always_on
---

Agent Operating Rules for PlanifyAI

These are the rules you must follow while working on the PlanifyAI repository.

1. Source of Truth

The main planning document is docs/ROADMAP.md.

You must also keep these files consistent with your changes:

TODO.md

SYSTEM_ARCHITECTURE_AND_ROADMAP.md

CHANGELOG.md

README.md

RESEARCH_IMPLEMENTATION_STATUS.md (if it exists)

You are not just editing code; you are maintaining the plan + docs + code together.

2. Task Selection

When the user gives you a request (e.g. “start with Faz 0” or “do 1.1.1”):

Open docs/ROADMAP.md.

Find the matching phase and item (e.g. Faz 1.1 – OptimizationResults Bölünmesi, item 1.1.1).

Before changing anything, explicitly state:

Which roadmap item you are working on:

Working on: Faz X.Y – <item title>

3. Plan Before You Code

For each roadmap item:

List the files you expect to touch (backend, frontend, tests, docs).

Write a short step list, for example:

Plan:
1) Create new hook file hooks/useMapInitialization.ts
2) Move map init logic from OptimizationResults.tsx into the hook
3) Update OptimizationResults.tsx to use the new hook
4) Run tests / build
5) Update ROADMAP + TODO + docs


Only then you start editing code.

4. Code Changes

When implementing a roadmap item:

Change only what is necessary for that item.

Prefer small, focused changes over big “god commits”.

After code changes:

Run relevant commands if possible (e.g. npm run build, npm test, pytest).

If something fails:

Fix it or clearly explain what is broken.

5. Documentation & System Files

After each meaningful change, you must update the related docs:

docs/ROADMAP.md

Mark the roadmap item as:

done / in progress / blocked

Optionally add a short note:

Notes: split OptimizationResults into MapContainer + SimulationPanel

TODO.md

Check off completed tasks, or annotate:

- [x] Split OptimizationResults.tsx into smaller components (Faz 1.1)

SYSTEM_ARCHITECTURE_AND_ROADMAP.md

If you changed architecture (e.g. new job store, new component structure), reflect it here.

CHANGELOG.md

Add a brief entry under the current version, e.g.:

- refactor(frontend): split OptimizationResults into modular components (Faz 1.1)

README.md

Update if:

Setup steps changed

Environment variables changed

Commands changed

User-facing behavior changed in a meaningful way

RESEARCH_IMPLEMENTATION_STATUS.md

If you implemented something based on a research doc, mark it as implemented and reference the code.

6. Reporting Back

Whenever you finish a roadmap item (or a part of it), report in a structured way:

Roadmap item:
Faz X.Y.Z – <title>

Code changes:

List key files you modified.

Commands/tests run:

List what you ran and whether they passed.

Docs updated:

docs/ROADMAP.md, TODO.md, etc. (what you changed).

Next suggested step:

Which roadmap item should be done next.

Keep this short, clear, and technical.

7. Constraints & Behaviour

Do not skip updating docs and roadmap – they are first-class citizens.

Do not perform huge refactors in a single step; follow the roadmap granularity (1.1.1, 1.1.2, etc.).

Be explicit when you are uncertain:

e.g. “This part of the domain is unclear; I’m making assumption X.”

Always prefer:

Clear structure

Small steps

Traceable changes

8. Style

Be concise, technical, and action-oriented.

No fluff, no motivational speeches.

Your output should look like it’s written by a senior engineer reporting progress to another senior engineer.

If the roadmap and the code ever conflict, do not silently pick one:

Call it out explicitly:
“Roadmap says X, but code is currently Y. I will adjust roadmap/code in this direction: …”