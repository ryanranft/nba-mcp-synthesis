# Architecture Decision Record (ADR) Template

**Title**: [Short descriptive title]
**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Deprecated | Superseded
**Supersedes**: [Link to ADR] (if applicable)
**Superseded by**: [Link to ADR] (if applicable)

---

## 📋 Context

**Background**: What is the issue or situation that motivates this decision?

**Problem Statement**: What specific problem are we trying to solve?

**Constraints**:
- Technical constraint 1
- Business constraint 2
- Resource constraint 3

**Stakeholders**:
- Stakeholder 1 (role)
- Stakeholder 2 (role)

---

## 🎯 Decision

**Summary**: One sentence describing the decision.

**Detailed Decision**:
Full explanation of what was decided, including:
- What will be done
- How it will be implemented
- When it will take effect
- Who is responsible

---

## 🔍 Options Considered

### Option 1: [Name]
**Description**: What this option entails

**Pros**:
- Pro 1
- Pro 2
- Pro 3

**Cons**:
- Con 1
- Con 2
- Con 3

**Cost/Effort**: Low | Medium | High

---

### Option 2: [Name]
[Repeat structure]

---

### Option 3: [Name]
[Repeat structure]

---

## ✅ Rationale

**Why This Decision**:
Detailed explanation of why the chosen option was selected over alternatives.

**Trade-offs Accepted**:
- Trade-off 1: We accept X in exchange for Y
- Trade-off 2: We sacrifice A to gain B

**Risks Acknowledged**:
- Risk 1: Description and mitigation
- Risk 2: Description and mitigation

---

## 📊 Impact Analysis

### Code Impact
**Files Affected**: N files
**Components Modified**:
- Component 1: Nature of change
- Component 2: Nature of change

**Migration Path**: How to transition from old to new

### Performance Impact
**Expected Changes**:
- Metric 1: Before → After
- Metric 2: Before → After

**Benchmarks**: Link to benchmark results

### Developer Experience Impact
**Learning Curve**: Low | Medium | High
**Documentation Needs**: What needs to be documented
**Training Required**: Yes | No - details

### Operational Impact
**Deployment**: Changes to deployment process
**Monitoring**: New metrics or alerts needed
**Maintenance**: Long-term maintenance considerations

---

## 🧪 Validation

**Success Criteria**:
- [ ] Criterion 1 - how to measure
- [ ] Criterion 2 - how to measure
- [ ] Criterion 3 - how to measure

**Testing Strategy**:
- Test type 1: What will be tested
- Test type 2: What will be tested

**Rollback Plan**: How to revert if this doesn't work

---

## 🔗 References

**Related Decisions**:
- [ADR-XXX: Related decision](link)
- [ADR-YYY: Another related decision](link)

**Documentation**:
- [Guide: Topic](link)
- [API Docs: Module](link)

**External Resources**:
- [Article/Blog: Title](url)
- [Library Docs: Name](url)

**Discussion**:
- [Issue #XXX](url)
- [PR #YYY](url)
- [Slack thread](url)

---

## 📅 Timeline

**Proposed**: YYYY-MM-DD
**Discussed**: YYYY-MM-DD (stakeholder meeting)
**Accepted**: YYYY-MM-DD
**Implemented**: YYYY-MM-DD to YYYY-MM-DD
**Reviewed**: YYYY-MM-DD (post-implementation review)

---

## 📝 Update Log

### YYYY-MM-DD
**Change**: Description of update
**Reason**: Why the update was needed
**By**: Name/Role

---

## 🏷️ Tags

`#architecture` `#performance` `#migration` `#api-design` `#security` `#testing`

---

## 💡 Examples

**Example Use Case 1**: Description of how this decision applies

**Example Use Case 2**: Description of how this decision applies

**Code Example**:
```python
# Before
old_code_here()

# After
new_code_here()
```

---

**Archive Instructions**:
- This file is PERMANENTLY tracked in git
- Never delete this file
- Mark as "Superseded" if replaced by newer decision
- Link to superseding decision in header
