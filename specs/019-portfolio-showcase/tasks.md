# Tasks: Portfolio & Agent Showcase

**Feature**: 019-portfolio-showcase  
**Status**: In Progress  
**Started**: 2026-01-11

---

## Overview

- **Goal**: Create portfolio documentation and web pages for resume-review agent system (FR-PF01)
- **Scope**: Stage 1 only (Agent Tools documentation)
- **Out of Scope**: Living Portfolio Chatbot (Stage 2)

---

## Task List

### 📋 Specification
- [x] Create `specs/019-portfolio-showcase/spec.md`
- [x] Create `specs/019-portfolio-showcase/plan.md`
- [x] Create `specs/019-portfolio-showcase/tasks.md`

### 📚 Architecture Documentation
- [ ] Create `packages/resume-review/docs/architecture.md`
  - [ ] Overview section
  - [ ] System Architecture section with Mermaid diagram
  - [ ] State Management section
  - [ ] Multi-Agent Orchestration section
  - [ ] Cost Optimization section
  - [ ] Tool Integration section
- [ ] Update `packages/resume-review/README.md`
  - [ ] Add "Portfolio Showcase" section at top
  - [ ] Add architecture documentation link
  - [ ] Add technology stack highlights

### 🌐 Web Portfolio Pages
- [ ] Create `packages/web/src/pages/portfolio.mdx`
  - [ ] Project overview
  - [ ] Technical highlights list
  - [ ] Simplified architecture diagram (Mermaid)
  - [ ] Links to GitHub and architecture details
- [ ] Create `packages/web/src/pages/portfolio/architecture.mdx`
  - [ ] Convert architecture.md to MDX
  - [ ] Add Astro frontmatter
  - [ ] Apply Tailwind CSS styling
  - [ ] Add breadcrumb navigation

### 🧭 Navigation
- [ ] Update `packages/web/src/layouts/MainLayout.astro`
  - [ ] Add "Portfolio" link to desktop navigation
  - [ ] Add "Portfolio" link to mobile menu
  - [ ] Implement active page highlighting

### 📄 Documentation Updates
- [ ] Update `docs/roadmap.md`
  - [ ] Change feature 16 status to "🟢 進行中" → "✅ 完了"
  - [ ] Add to completed features table
- [ ] Update `CLAUDE.md`
  - [ ] Add to "Recent Changes" section

### ✅ Testing & Validation
- [ ] Run Python tests: `cd packages/resume-review && pytest`
- [ ] Build Astro site: `cd packages/web && pnpm build`
- [ ] Manual testing:
  - [ ] Test `/portfolio` page in browser
  - [ ] Test `/portfolio/architecture` page
  - [ ] Test navigation links (desktop)
  - [ ] Test navigation links (mobile)
  - [ ] Test Mermaid diagrams rendering
  - [ ] Test responsive design
- [ ] Production build test: `VERCEL=1 pnpm build && pnpm preview`

### 📝 Completion
- [ ] Create walkthrough.md
- [ ] Final documentation review
- [ ] Commit and push changes

---

## Progress Tracker

**Current Phase**: 📚 Architecture Documentation  
**Overall Progress**: 15% (3/20 tasks completed)

### Completed
- ✅ Specification files created

### In Progress
- 🔄 Architecture documentation

### Blocked
- None

---

## Notes

- Stage 2 (FR-PF02: Living Portfolio Chatbot) will be implemented in a separate PR
- Focus on clear, concise documentation that appeals to hiring managers
- Ensure all Mermaid diagrams are simple and easy to understand
