# Permanent References Index

**Purpose**: Navigate permanent architectural decisions and reference materials
**Last Updated**: 2025-10-11
**Status**: Always tracked in git

---

## 📁 Files

### Core References
- **[tool-registry.md](tool-registry.md)** - 90+ MCP tools by category (~100 tokens)
- **[phases.md](phases.md)** - Implementation methodology (~200 tokens)
- **[file-management-policy.md](file-management-policy.md)** - File policies (~150 tokens)
- **[context_budget.json](context_budget.json)** - Token budgets (~50 tokens)
- **[template.md](template.md)** - ADR template (~100 tokens)

---

## 🔍 Quick Lookup

### Find Tools
```bash
grep -i "tool_name" .ai/permanent/tool-registry.md
grep "^## " .ai/permanent/tool-registry.md  # List categories
```

### Check Policies
```bash
grep -A 20 "Decision Tree" .ai/permanent/file-management-policy.md
```

### View Budgets
```bash
cat .ai/permanent/context_budget.json | jq '.budgets'
```

### Review Phases
```bash
grep "^## Phase" .ai/permanent/phases.md  # List all phases
```

---

## 📚 Reference Categories

### Implementation
- **tool-registry.md** - Database, S3, ML, NBA, Stats tools
- **phases.md** - 15-phase implementation guide

### Policies
- **file-management-policy.md** - File decisions, archive triggers
- **context_budget.json** - Token thresholds, session targets

### Templates
- **template.md** - Architecture Decision Records (ADRs)

---

## 🔄 Update Guidelines

**tool-registry.md**: Add new tools to appropriate category
**phases.md**: Rarely update (historical reference)
**file-management-policy.md**: Add new patterns as needed
**context_budget.json**: Adjust thresholds quarterly
**template.md**: Update for new ADR patterns

---

## 🎯 Token Budget

**Total Access**: <600 tokens for complete permanent reference context

| File | Estimated Tokens |
|------|------------------|
| index.md | ~20 |
| tool-registry.md | ~100 |
| phases.md | ~200 |
| file-management-policy.md | ~150 |
| context_budget.json | ~50 |
| template.md | ~100 |

---

## 📈 Usage Patterns

**Daily**: tool-registry.md (tool lookups)
**Weekly**: file-management-policy.md, context_budget.json
**Monthly**: phases.md (replication guide)
**As Needed**: template.md (ADR creation)

---

## 📚 Related

- **[../index.md](../index.md)** - Session management
- **[CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md](../../CONTEXT_OPTIMIZATION_OPERATIONS_GUIDE.md)** - Operations
- **[docs/DOCUMENTATION_MAP.md](../../docs/DOCUMENTATION_MAP.md)** - Canonical locations

---

**Note**: Permanent references are never archived. Mark as "Superseded" if replaced, don't delete.
