# Tasks: Monorepo Refactor

**Input**: Design documents from `/specs/002-monorepo-refactor/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Tests**: Existing Python tests must pass after migration. No new test tasks (tests already exist).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Monorepo root**: Repository root directory
- **packages/web/**: Next.js/Nextra web application
- **packages/resume-review/**: Python AI review tool
- **resume/**: Resume source and output

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create base directory structure for monorepo

- [x] T001 Create `packages/` directory at repository root
- [x] T002 [P] Create `packages/web/` directory
- [x] T003 [P] Create `resume/` directory at repository root
- [x] T004 [P] Create `resume/output/` directory for generated files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core file moves that must complete before user stories can be validated

**⚠️ CRITICAL**: User story validation depends on these moves completing

- [x] T005 Move `components/` to `packages/web/components/`
- [x] T006 Move `pages/` to `packages/web/pages/`
- [x] T007 Move `styles/` to `packages/web/styles/`
- [x] T008 [P] Move `next.config.mjs` to `packages/web/next.config.mjs`
- [x] T009 [P] Move `theme.config.tsx` to `packages/web/theme.config.tsx`
- [x] T010 [P] Move `tailwind.config.js` to `packages/web/tailwind.config.js`
- [x] T011 [P] Move `tsconfig.json` to `packages/web/tsconfig.json`
- [x] T012 [P] Move `middleware.ts` to `packages/web/middleware.ts`
- [x] T013 [P] Move `postcss.config.js` to `packages/web/postcss.config.js`
- [x] T014 Move `agents/` to `packages/resume-review/`
- [x] T015 Move `public/assets/resume-ja.qmd` to `resume/resume-ja.qmd`
- [x] T016 [P] Move `resume.pdf` to `resume/output/resume-ja.pdf`
- [x] T017 [P] Move `public/assets/resume-ja.html` to `resume/output/resume-ja.html` (if exists)

**Checkpoint**: All files moved - configuration updates can begin

---

## Phase 3: User Story 1 - Developer Navigates Repository Structure (Priority: P1) 🎯 MVP

**Goal**: Repository structure clearly separates web app, AI tools, and resume source

**Independent Test**: New developer can identify component locations within 2 minutes of examining root directory

### Implementation for User Story 1

- [x] T018 [US1] Create `packages/web/package.json` with web dependencies extracted from root package.json
- [x] T019 [US1] Update `packages/web/next.config.mjs` to adjust any relative paths
- [x] T020 [US1] Verify `packages/web/` contains all Next.js/Nextra files (components, pages, styles, configs)
- [x] T021 [US1] Verify `packages/resume-review/` contains Python package with pyproject.toml
- [x] T022 [US1] Verify `resume/` contains resume-ja.qmd as canonical source
- [x] T023 [US1] Update root `.gitignore` to include new paths for node_modules and .next in packages/web/

**Checkpoint**: Structure is clear - packages/web/, packages/resume-review/, resume/ are distinct and identifiable

---

## Phase 4: User Story 2 - Developer Runs Package-Specific Commands (Priority: P2)

**Goal**: All package-specific commands execute from repository root

**Independent Test**: `pnpm dev`, `pnpm review`, `pnpm quarto:pdf` all work from root

### Implementation for User Story 2

- [x] T024 [US2] Update `pnpm-workspace.yaml` with packages list: `packages: ['packages/web']`
- [x] T025 [US2] Update root `package.json` to remove web dependencies (moved to packages/web/)
- [x] T026 [US2] Update root `package.json` scripts for web: `"dev": "pnpm --filter web dev"`, `"build": "pnpm --filter web build"`, `"start": "pnpm --filter web start"`
- [x] T027 [US2] Update root `package.json` scripts for quarto: `"quarto:pdf": "cd resume && quarto render resume-ja.qmd --to pdf -o output/resume-ja.pdf"`, `"quarto:html": "cd resume && quarto render resume-ja.qmd --to html -o output/resume-ja.html"`, `"quarto:preview": "cd resume && quarto preview resume-ja.qmd"`, `"quarto:preview:html": "cd resume && quarto preview resume-ja.qmd --to html"`
- [x] T028 [US2] Update root `package.json` scripts for review: `"review": "cd packages/resume-review && .venv/bin/python -m src.cli review --input ../../resume/resume-ja.qmd"`, `"review:dry": "cd packages/resume-review && .venv/bin/python -m src.cli review --input ../../resume/resume-ja.qmd --dry-run --verbose"`, `"review:full": "cd packages/resume-review && .venv/bin/python -m src.cli review --input ../../resume/resume-ja.qmd --screenshot-url http://localhost:3000/ja --verbose"`
- [x] T029 [US2] Update root `package.json` scripts: `"sync": "python3 scripts/sync_qmd_to_mdx.py"`, `"resume:build": "pnpm quarto:pdf && pnpm quarto:html && pnpm sync"`, `"review:build": "pnpm review && pnpm resume:build"`
- [x] T030 [US2] Update root `package.json` scripts for testing: `"test:python": "cd packages/resume-review && .venv/bin/pytest"`, `"lint:python": "cd packages/resume-review && .venv/bin/ruff check ."`
- [x] T031 [US2] Update `scripts/sync_qmd_to_mdx.py` to use new paths (resume/resume-ja.qmd → packages/web/pages/ja/index.mdx)
- [x] T032 [US2] Run `pnpm install` from root to link workspace packages
- [x] T033 [US2] Verify `pnpm dev` starts web server from packages/web/
- [x] T034 [US2] Verify `pnpm quarto:pdf` generates PDF in resume/output/
- [x] T035 [US2] Verify `pnpm review:dry` executes review command

**Checkpoint**: All root commands work - developers can work from root directory

---

## Phase 5: User Story 3 - Developer Adds New Package (Priority: P3)

**Goal**: Workspace configuration supports adding new packages

**Independent Test**: Create test package in packages/ and verify pnpm recognizes it

### Implementation for User Story 3

- [x] T036 [US3] Verify `pnpm-workspace.yaml` uses glob pattern `packages/*` (or update if using explicit list)
- [x] T037 [US3] Document package creation process in README.md (how to add new workspace package)
- [x] T038 [US3] Verify `pnpm install` correctly resolves workspace packages

**Checkpoint**: Monorepo is extensible - new packages can be added following documented process

---

## Phase 6: User Story 4 - Developer Maintains Workflow Module (Priority: P4)

**Goal**: Workflow code split into files under 200 lines each

**Independent Test**: `wc -l packages/resume-review/src/workflow/*.py packages/resume-review/src/workflow/nodes/*.py` shows all files under 200 lines; all tests pass

### Implementation for User Story 4

- [x] T039 [US4] Rename `packages/resume-review/src/orchestration/` to `packages/resume-review/src/workflow/`
- [x] T040 [US4] Create `packages/resume-review/src/workflow/nodes/` directory
- [x] T041 [US4] Create `packages/resume-review/src/workflow/nodes/__init__.py` with node exports
- [x] T042 [P] [US4] Extract supervisor_node and design_supervisor_node to `packages/resume-review/src/workflow/nodes/supervisor.py`
- [x] T043 [P] [US4] Extract aggregator_node to `packages/resume-review/src/workflow/nodes/aggregator.py`
- [x] T044 [P] [US4] Extract revisor_node to `packages/resume-review/src/workflow/nodes/revisor.py`
- [x] T045 [P] [US4] Extract portfolio_analyzer_node to `packages/resume-review/src/workflow/nodes/portfolio.py`
- [x] T046 [US4] Extract conditional edge functions to `packages/resume-review/src/workflow/conditions.py`
- [x] T047 [US4] Create `packages/resume-review/src/workflow/graph.py` with build_review_workflow function
- [x] T048 [US4] Refactor `packages/resume-review/src/workflow/workflow.py` → `packages/resume-review/src/workflow/runner.py` (keep ReviewWorkflow class only)
- [x] T049 [US4] Update `packages/resume-review/src/workflow/__init__.py` with public exports: ReviewWorkflow, ReviewState, build_review_workflow
- [x] T050 [US4] Update `packages/resume-review/src/cli.py` imports to use new workflow module structure
- [x] T051 [US4] Create `packages/resume-review/src/config/` directory
- [x] T052 [P] [US4] Create `packages/resume-review/src/config/__init__.py`
- [x] T053 [P] [US4] Create `packages/resume-review/src/config/settings.py` with API keys, thresholds, paths
- [x] T054 [P] [US4] Create `packages/resume-review/src/config/prompts.py` with system prompts for each agent
- [x] T055 [P] [US4] Create `packages/resume-review/src/config/weights.py` with scoring weights
- [x] T056 [US4] Update agent imports to use config module for prompts and weights
- [x] T057 [US4] Verify no circular imports: `python -c "from src.workflow import ReviewWorkflow; print('OK')"`
- [x] T058 [US4] Verify all workflow files under 200 lines: `wc -l packages/resume-review/src/workflow/*.py packages/resume-review/src/workflow/nodes/*.py`
- [x] T059 [US4] Run `pytest` in packages/resume-review/ to verify all tests pass

**Checkpoint**: Workflow module is maintainable - all files under 200 lines, tests pass

---

## Phase 7: User Story 5 - Resume Output Files Organized (Priority: P5)

**Goal**: Generated files (PDF, HTML) in dedicated output directory

**Independent Test**: `pnpm resume:build` generates files in resume/output/

### Implementation for User Story 5

- [x] T060 [US5] Verify `resume/output/` directory exists and contains generated files
- [x] T061 [US5] Update `.gitignore` to include resume/output/ contents (keep directory, ignore generated files)
- [x] T062 [US5] Verify `pnpm quarto:pdf` outputs to `resume/output/resume-ja.pdf`
- [x] T063 [US5] Verify `pnpm quarto:html` outputs to `resume/output/resume-ja.html`
- [x] T064 [US5] Add `.gitkeep` to `resume/output/` to preserve directory in git

**Checkpoint**: Output organization complete - all generated files in resume/output/

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and validation

- [x] T065 [P] Update `CLAUDE.md` with new paths for commands
- [x] T066 [P] Update `README.md` with new repository structure and commands
- [x] T067 [P] Update `.specify/memory/constitution.md` to reference new resume path (resume/resume-ja.qmd)
- [x] T068 Remove old `public/assets/` directory if empty (or update for remaining assets)
- [x] T069 Remove old `agents/` directory (now packages/resume-review/)
- [x] T070 Run full test suite: `pnpm test:python`
- [x] T071 Verify web app starts: `pnpm dev`
- [x] T072 Verify resume build: `pnpm resume:build`
- [x] T073 Verify review works: `pnpm review:dry`
- [ ] T074 Run quickstart.md validation checklist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1-US3 can proceed in parallel after Phase 2
  - US4-US5 can proceed in parallel after Phase 2
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 structure
- **User Story 3 (P3)**: Can start after US2 (needs pnpm-workspace.yaml configured)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Verification tasks come after implementation tasks
- File moves before configuration updates
- Import updates after file structure changes

### Parallel Opportunities

**Phase 1 (Setup)**:
```
T002 Create packages/web/
T003 Create resume/
T004 Create resume/output/
```

**Phase 2 (Foundational) - Config Files**:
```
T008 Move next.config.mjs
T009 Move theme.config.tsx
T010 Move tailwind.config.js
T011 Move tsconfig.json
T012 Move middleware.ts
T013 Move postcss.config.js
T016 Move resume.pdf
T017 Move resume-ja.html
```

**Phase 6 (US4) - Node Extraction**:
```
T042 Extract supervisor_node to nodes/supervisor.py
T043 Extract aggregator_node to nodes/aggregator.py
T044 Extract revisor_node to nodes/revisor.py
T045 Extract portfolio_analyzer_node to nodes/portfolio.py
```

**Phase 6 (US4) - Config Creation**:
```
T052 Create config/__init__.py
T053 Create config/settings.py
T054 Create config/prompts.py
T055 Create config/weights.py
```

**Phase 8 (Polish) - Documentation**:
```
T065 Update CLAUDE.md
T066 Update README.md
T067 Update constitution.md
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (13 tasks)
3. Complete Phase 3: User Story 1 (6 tasks)
4. Complete Phase 4: User Story 2 (12 tasks)
5. **STOP and VALIDATE**: Test directory navigation and root commands
6. Deploy if working

### Full Implementation

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Structure clear
3. Add User Story 2 → Commands work
4. Add User Story 3 → Extensibility verified
5. Add User Story 4 → Workflow maintainable
6. Add User Story 5 → Outputs organized
7. Polish → Documentation updated

### Rollback Strategy

Each phase is atomic - if phase fails:
1. `git status` to see changes
2. `git checkout -- .` to revert
3. Fix issues and retry phase

---

## Task Summary

| Phase | User Story | Task Count | Parallel Tasks |
|-------|-----------|------------|----------------|
| 1 | Setup | 4 | 3 |
| 2 | Foundational | 13 | 9 |
| 3 | US1 - Navigation | 6 | 0 |
| 4 | US2 - Commands | 12 | 0 |
| 5 | US3 - Extensibility | 3 | 0 |
| 6 | US4 - Workflow Split | 21 | 8 |
| 7 | US5 - Output Org | 5 | 0 |
| 8 | Polish | 10 | 3 |
| **Total** | | **74** | **23** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Existing Python tests must pass after refactoring (FR-015)
- CLI interface must remain compatible (FR-016)
- No workflow file over 200 lines (FR-009, SC-003)
- Commit after each phase for safe rollback
