# Documentation Map

**Purpose**: Canonical locations for all project topics
**Last Updated**: 2025-10-11
**Status**: Active reference

---

## 🎯 Overview

This map defines the single source of truth for each topic in the project documentation. Use this to avoid duplication and ensure consistent information.

### Cross-Reference Rules
- **Primary Source**: Always link to the canonical location
- **Brief Reference**: Use "See [Topic](link) for details" pattern
- **No Duplication**: Don't repeat information, link instead
- **Update Source**: Only update the canonical location

---

## 📚 Topic Map

### Project Status & Tracking
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **Current Status** | [PROJECT_STATUS.md](../PROJECT_STATUS.md) | Quick project overview |
| **Detailed Status** | [project/status/index.md](../project/status/index.md) | Comprehensive status tracking |
| **Tool Registration** | [project/status/tools.md](../project/status/tools.md) | Tool registration details |
| **Sprint Progress** | [project/status/sprints.md](../project/status/sprints.md) | Sprint completion status |
| **Blockers & Issues** | [project/status/blockers.md](../project/status/blockers.md) | Current blockers |
| **Daily Progress** | [project/tracking/progress.log](../project/tracking/progress.log) | Append-only log |
| **Key Decisions** | [project/tracking/decisions.md](../project/tracking/decisions.md) | Architecture decisions |
| **Milestones** | [project/tracking/milestones.md](../project/tracking/milestones.md) | Major achievements |

### Session Management
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **Operations Guide** | [CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md](../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md) | Daily operations, decision tree |
| **Session Management Guide** | [.ai/index.md](../.ai/index.md) | Complete session management |
| **Current Session** | [.ai/current-session.md](../.ai/current-session.md) | Active session state |
| **Tool Registry** | [.ai/permanent/tool-registry.md](../.ai/permanent/tool-registry.md) | Searchable tool list |
| **Session Scripts** | [scripts/session_start.sh](../scripts/session_start.sh) | Session management scripts |
| **Archive Management** | [scripts/session_archive.sh](../scripts/session_archive.sh) | Session archiving |

### Planning & Strategy
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **Master Plan** | [docs/plans/MASTER_PLAN.md](plans/MASTER_PLAN.md) | Overall project strategy |
| **Context Optimization Plan** | [docs/plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md](plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md) | Current optimization effort |
| **Context Requirements Verification** | [CONTEXT_OPTIMIZATION_REQUIREMENTS_VERIFICATION.md](../CONTEXT_OPTIMIZATION_REQUIREMENTS_VERIFICATION.md) | Requirements verification (all 10 met) |
| **NBA MCP Improvement Plan** | [docs/plans/detailed/NBA_MCP_IMPROVEMENT_PLAN.md](plans/detailed/NBA_MCP_IMPROVEMENT_PLAN.md) | Improvement roadmap |
| **Verification Report** | [docs/plans/VERIFICATION_REPORT_2025-10-11.md](plans/VERIFICATION_REPORT_2025-10-11.md) | Latest verification status |

### Guides & Documentation
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **Quick Reference** | [docs/guides/QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) | Essential commands and workflows |
| **Context Optimization Guide** | [docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md](guides/CONTEXT_OPTIMIZATION_GUIDE.md) | Best practices for context management |
| **Production Deployment Guide** | [docs/guides/PRODUCTION_DEPLOYMENT_GUIDE.md](guides/PRODUCTION_DEPLOYMENT_GUIDE.md) | Deployment procedures |
| **Claude Desktop Setup** | [docs/guides/CLAUDE_DESKTOP_SETUP.md](guides/CLAUDE_DESKTOP_SETUP.md) | Claude Desktop configuration |
| **Setup Guide** | [docs/SETUP_GUIDE.md](SETUP_GUIDE.md) | Detailed installation instructions |
| **Quick Start Guide** | [QUICKSTART.md](../QUICKSTART.md) | Get up and running quickly |

### Sprint History
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **Sprint History** | [docs/sprints/index.md](sprints/index.md) | Sprint overview and navigation |
| **Sprint 5 Complete** | [docs/sprints/completed/SPRINT_5_COMPLETE.md](sprints/completed/SPRINT_5_COMPLETE.md) | Sprint 5 completion |
| **Sprint 6 Complete** | [docs/sprints/completed/SPRINT_6_COMPLETE.md](sprints/completed/SPRINT_6_COMPLETE.md) | Sprint 6 completion |
| **Sprint 7 Complete** | [docs/sprints/completed/SPRINT_7_COMPLETED.md](sprints/completed/SPRINT_7_COMPLETED.md) | Sprint 7 completion |
| **Sprint 8 Complete** | [docs/sprints/completed/SPRINT_8_COMPLETED.md](sprints/completed/SPRINT_8_COMPLETED.md) | Sprint 8 completion |

### Analysis & Research
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **Repository Analysis** | [docs/analysis/LOCAL_REPOSITORY_ANALYSIS_SUMMARY.md](analysis/LOCAL_REPOSITORY_ANALYSIS_SUMMARY.md) | Repository overview |
| **MCP Patterns** | [docs/analysis/MCP_REPOSITORY_ANALYSIS_ADVANCED_PATTERNS.md](analysis/MCP_REPOSITORY_ANALYSIS_ADVANCED_PATTERNS.md) | Advanced MCP patterns |
| **Graphiti Analysis** | [docs/analysis/GRAPHITI_MCP_ANALYSIS.md](analysis/GRAPHITI_MCP_ANALYSIS.md) | Graphiti integration analysis |

### Enhancements & Future Work
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **MCP Enhancements** | [docs/enhancements/MCP_ENHANCEMENTS.md](enhancements/MCP_ENHANCEMENTS.md) | Enhancement roadmap |
| **Next Steps** | [docs/enhancements/NEXT_STEPS.md](enhancements/NEXT_STEPS.md) | Immediate next actions |
| **Ollama Workflow** | [docs/enhancements/OLLAMA_PRIMARY_WORKFLOW.md](enhancements/OLLAMA_PRIMARY_WORKFLOW.md) | Ollama integration workflow |

### Archive & Historical
| Topic | Canonical Location | Purpose |
|-------|-------------------|---------|
| **October 2025 Archive** | [docs/archive/2025-10/index.md](archive/2025-10/index.md) | Historical documentation |
| **Completion Documents** | [docs/archive/2025-10/completion/](archive/2025-10/completion/) | Historical completion summaries |
| **Session Documents** | [docs/archive/2025-10/sessions/](archive/2025-10/sessions/) | Historical session summaries |

---

## 🔗 Cross-Reference Patterns

### Standard Patterns
```markdown
# Brief Reference Pattern
See [Tool Registration](project/status/tools.md) for details.

# Detailed Reference Pattern
For comprehensive information, see [Session Management Guide](.ai/index.md).

# Navigation Pattern
Navigate to [Sprint History](docs/sprints/index.md) for sprint details.

# Status Pattern
Current status: [PROJECT_STATUS.md](../PROJECT_STATUS.md)
```

### Topic-Specific Patterns

#### Tool Registration
- **Primary**: [project/status/tools.md](../project/status/tools.md)
- **Registry**: [.ai/permanent/tool-registry.md](../.ai/permanent/tool-registry.md)
- **Pattern**: "See [Tool Registration](project/status/tools.md) for details"

#### Sprint Status
- **Primary**: [project/status/sprints.md](../project/status/sprints.md)
- **History**: [docs/sprints/index.md](sprints/index.md)
- **Pattern**: "See [Sprint Progress](project/status/sprints.md) for current status"

#### Session Management
- **Primary**: [.ai/index.md](../.ai/index.md)
- **Current**: [.ai/current-session.md](../.ai/current-session.md)
- **Pattern**: "See [Session Management Guide](.ai/index.md) for details"

#### Context Optimization
- **Primary**: [docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md](guides/CONTEXT_OPTIMIZATION_GUIDE.md)
- **Plan**: [docs/plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md](plans/detailed/CONTEXT_OPTIMIZATION_PLAN.md)
- **Pattern**: "See [Context Optimization Guide](docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md) for best practices"

---

## 📊 Duplication Prevention

### Common Duplicated Topics
1. **Tool Registration Process** - Found in 5+ files
   - **Canonical**: [project/status/tools.md](../project/status/tools.md)
   - **Action**: Replace duplicates with cross-references

2. **Sprint Status** - Found in 4+ files
   - **Canonical**: [project/status/sprints.md](../project/status/sprints.md)
   - **Action**: Point to canonical location

3. **Session Management** - Found in 3+ files
   - **Canonical**: [.ai/index.md](../.ai/index.md)
   - **Action**: Use brief references

4. **Context Optimization** - Found in 3+ files
   - **Canonical**: [docs/guides/CONTEXT_OPTIMIZATION_GUIDE.md](guides/CONTEXT_OPTIMIZATION_GUIDE.md)
   - **Action**: Link to guide

### Refactoring Strategy
1. **Identify Duplicates**: Use audit script
2. **Choose Canonical**: Select best source
3. **Replace Content**: Use cross-reference pattern
4. **Update Links**: Ensure all links point to canonical
5. **Test**: Verify links work correctly

---

## 🎯 Usage Guidelines

### For Writers
- **Check this map** before writing about any topic
- **Link to canonical** instead of duplicating
- **Update canonical** if information changes
- **Use standard patterns** for cross-references

### For Readers
- **Start with canonical** for comprehensive information
- **Use cross-references** for related topics
- **Check links** if information seems outdated
- **Report broken links** to maintain quality

### For Maintainers
- **Update this map** when adding new topics
- **Run audit script** monthly to find new duplicates
- **Refactor duplicates** using this map
- **Maintain link integrity** across all documents

---

## 🔍 Search & Discovery

### Quick Find
```bash
# Find canonical location for topic
grep -i "topic_name" docs/DOCUMENTATION_MAP.md

# Find all references to topic
grep -r "topic_name" docs/ --include="*.md"

# Check for duplicates
./scripts/audit_cross_references.sh
```

### Topic Categories
- **Status & Tracking**: 8 topics
- **Session Management**: 5 topics
- **Planning & Strategy**: 4 topics
- **Guides & Documentation**: 6 topics
- **Sprint History**: 5 topics
- **Analysis & Research**: 3 topics
- **Enhancements**: 3 topics
- **Archive & Historical**: 3 topics

---

## 📈 Maintenance

### Regular Tasks
- **Monthly**: Run audit script
- **Quarterly**: Review canonical locations
- **As Needed**: Update cross-references
- **Always**: Maintain link integrity

### Quality Metrics
- **Duplication Rate**: <5% (target)
- **Broken Links**: 0 (target)
- **Cross-Reference Usage**: >80% (target)
- **Canonical Coverage**: 100% (target)

---

**Note**: This map is part of Phase 9 of the Context Optimization plan. Use it to eliminate duplication and maintain single sources of truth.
