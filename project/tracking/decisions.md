# Key Decisions Log

Format: Date-based entries with context, decision, and rationale

---

## 2025-10-11: Adopted hierarchical session storage (.ai/ directory)

**Context**: Claude Code sessions were hitting context limits (30-50K tokens), causing auto-compaction and loss of continuity.

**Problem**: Reading full PROJECT_MASTER_TRACKER.md (670 lines) and multiple status files consumed 5000+ tokens per session start.

**Decision**: Create .ai/ directory with:
- daily/ - Session logs (gitignored, 7-day retention)
- monthly/ - Aggregated summaries (gitignored, 90-day retention)
- permanent/ - Architecture decisions (git tracked)
- current-session.md - Auto-generated compact summary (<100 lines)

**Rationale**:
- Reduce session start from 5000 to 100 tokens (98% reduction)
- Organize by access frequency (daily vs permanent)
- Optional S3 backup for full history (~$0.0005/month)

**Impact**: Expected 80-93% reduction in overall session context usage

**References**:
- docs/plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md
- docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md

---

## 2025-10-11: Split PROJECT_MASTER_TRACKER.md into focused files

**Context**: Single 670-line tracker file too expensive to read repeatedly (1000 tokens per read).

**Problem**: Every status check required reading full file, even when only one section needed.

**Decision**: Split into:
- PROJECT_STATUS.md (root, 50 lines) - Quick reference
- project/status/*.md - Detailed status by category
- project/tracking/*.log - Append-only progress logs
- project/metrics/*.md - On-demand analytics

**Rationale**:
- Read only what you need (75-225 tokens vs 1000 tokens)
- Append-only logs never need to be read (10 tokens vs 1000 tokens)
- Index-based navigation for discovery

**Impact**: 85-93% reduction in status check token usage

**References**:
- project/index.md
- docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md

---

## 2025-10-10: Adopted FastMCP framework for MCP server

**Context**: Original server used basic MCP SDK patterns.

**Problem**: Needed better context injection, lifespan management, and tool registration patterns.

**Decision**: Migrate to FastMCP framework with:
- Pydantic models for all parameters
- Decorator-based tool registration
- Lifespan event handlers
- Settings management

**Rationale**:
- Industry best practice (from MCP SDK team)
- Better type safety and validation
- Cleaner code organization
- Easier testing

**Impact**: All 90 tools migrated successfully, 100% test pass rate maintained

**References**:
- mcp_server/fastmcp_server.py
- mcp_server/fastmcp_settings.py
- docs/sprints/completed/SPRINT_5_COMPLETE.md

---

## 2025-10-09: Corrected tracker after comprehensive audit

**Context**: Tracker claimed 71% complete (88/124 tools), but felt inaccurate.

**Problem**: Tracker didn't match actual codebase (math/stats/NBA tools were already implemented but marked "not started").

**Decision**: Conduct comprehensive audit:
1. Count @mcp.tool() decorators in fastmcp_server.py
2. Verify helper file implementations
3. Check test coverage
4. Correct all documentation

**Outcome**: Actual status is 85% complete (93/109 tools)
- 88 tools registered (verified)
- 5 tools implemented but not registered
- 16 tools truly pending

**Rationale**: Better to have accurate 85% than inflated 90% or underestimated 71%

**Impact**: Restored confidence in tracking, identified 5 quick wins

**References**:
- TRACKER_AUDIT_REPORT.md
- VERIFICATION_COMPLETE.md
- PROJECT_MASTER_TRACKER.md v3.0

---

## 2025-10-05: Built ML toolkit instead of web scraping (Sprint 7 scope change)

**Context**: Sprint 7 originally planned for MCP prompts & resources.

**Problem**: Prompts/resources are UX enhancements, but system lacked ML capabilities.

**Decision**: Pivot Sprint 7 to Machine Learning Core:
- Clustering (5 tools)
- Classification (7 tools)
- Anomaly Detection (3 tools)
- Feature Engineering (3 tools)

**Rationale**:
- ML tools provide more analytical value
- NBA analytics require ML capabilities
- Prompts/resources can be added later (Phase 9C)
- Stakeholder approved scope change

**Impact**: Complete unsupervised learning suite + 18 tools with 100% test pass rate

**References**:
- docs/sprints/completed/SPRINT_7_COMPLETED.md
- scripts/test_sprint7_features.py

---

## 2025-10-01: Built AWS integration instead of web scraping (Sprint 6 scope change)

**Context**: Sprint 6 originally planned for web scraping (3 tools).

**Problem**: Web scraping is nice-to-have, but AWS integration critical for production.

**Decision**: Pivot Sprint 6 to AWS Integration:
- AWS Glue tools (10 tools)
- Action tools (12 tools)
- Advanced analytics (18 tools)

**Rationale**:
- AWS Glue needed for ETL pipelines
- Action tools provide immediate user value
- Web scraping can be added later (Phase 9B)

**Impact**: Complete AWS integration + 40 tools beyond original scope

**References**:
- docs/sprints/completed/SPRINT_6_COMPLETE.md

---

## Format for New Entries

```markdown
## YYYY-MM-DD: Decision title

**Context**: Background information

**Problem**: What issue prompted this decision

**Decision**: What was decided (be specific)

**Rationale**: Why this decision was made
- Reason 1
- Reason 2

**Impact**: Consequences and outcomes

**References**: Links to related docs/code
```
