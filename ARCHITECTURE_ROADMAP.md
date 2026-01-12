# Marcus Architecture v0.38 — The Path From Here

## Current State: Foundation Complete

```
v0.36 ──────────────> Secure storage (Auth Wall)
       ✅ Password protection
       ✅ Session management
       ✅ Access control

v0.37 ──────────────> Reliable retrieval (Search Quality)
       ✅ FTS5 full-text search
       ✅ BM25 ranking
       ✅ Query normalization
       ✅ Alias expansion
       ✅ Graceful fallback

v0.38 ──────────────> Structured understanding (Blueprints)
       ✅ Topic extraction
       ✅ Skill typing
       ✅ Lesson scaffolding
       ✅ Citation grounding
       ✅ Checklist generation
```

## Why This Matters

**Before v0.38:** System could retrieve material reliably.  
**From v0.38 onward:** System understands material structure.

This changes what becomes possible:

| Build | Without Blueprint | With Blueprint (v0.38+) |
|-------|------------------|----------------------|
| v0.39 Lessons | "Generate explanation for..." (risky, often hallucinates) | "Generate lesson for Topic X which we know exists and has these chunks" (safe, grounded) |
| v0.40 Mastery | "Did student learn something?" (vague) | "Did student demonstrate all 3 skills for Topic X?" (measurable) |
| v0.41 Adaptive | "What should we teach next?" (guessing) | "Which unmastered topic builds on Topic X?" (certain) |

**Blueprints transform Marcus from reactive to intentional.**

---

## The Boring Build List (Remaining)

### Safe to Build (No Foundation Questions)

**v0.39 — Lesson Generation** (~40% confidence foundation is sufficient)
- Input: StudyPack blueprint
- Output: Narrative lessons (1-2 pages per topic)
- Constraints: Only for topics blueprint says exist
- Risk: Low (uses blueprint as guardrail)

**v0.40 — Mastery Tracking** (~70% confidence)
- Input: Student interactions
- Output: Topic mastery levels (0-100%)
- Constraints: Measured against blueprint skills
- Risk: Low (blueprint defines success)

**v0.41 — Adaptive Routing** (~80% confidence)
- Input: Current mastery + blueprint structure
- Output: Next recommended topic
- Constraints: Graph-walk on blueprint DAG
- Risk: Low (follows blueprint structure)

### Risky to Build (Need More Foundation)

**v0.42 — Cross-Material Synthesis** (~30% confidence)
- "Topics A, B, C appear in multiple materials. How do they differ?"
- Constraint: Only makes sense if blueprints from 3+ materials agree
- Blocker: v0.38 doesn't have synthesis rules yet

**v0.43 — Gap Analysis** (~20% confidence)
- "Student appears to understand A but not B. Why might B be hard?"
- Constraint: Needs pedagogical model of prerequisite chains
- Blocker: v0.38 doesn't model prerequisites

**v0.44 — Exam Prediction** (~40% confidence)
- "If student masters these topics, what exam score?"
- Constraint: Needs item-response theory model
- Blocker: No empirical calibration data yet

---

## One-Sentence Philosophy

**Boring systems are reliable systems.**  
**Reliable systems are usable systems.**  
**Usable systems become intelligent systems.**

---

## Next: v0.39 Lesson Generation

When ready to begin:

### Design Phase
- What is a "lesson"? (narrative length? worked examples? required?)
- How to map blueprint → lessons? (1:1? hierarchical?)
- When to include citations? (always? optional?)

### Implementation Phase  
- LLM integration for narrative generation
- Citation embedding in lesson text
- Quality gates (fluency, grounding, scope)

### Testing Phase
- Generate lessons for 3-5 blueprints
- Manual review: "Is this useful for studying?"
- Compare student feedback: "Blueprint+Lesson vs Blueprint alone"

### Success Criteria
- Lessons are readable (no obvious AI artifacts)
- Lessons are grounded (all claims have citations)
- Lessons are focused (no scope creep beyond topic)
- Students prefer lessons to raw source material

---

## Confidence Checklist

Before starting v0.39:

- [ ] All v0.38 API endpoints return expected data
- [ ] Blueprints from 5+ different documents exist
- [ ] Manual inspection: "Each topic seems reasonable"
- [ ] Manual inspection: "Citations match topics well"
- [ ] Database queries are fast (<500ms)
- [ ] No ungrounded topics in test set
- [ ] Documentation is clear
- [ ] No one has found a "lurking bug"

**Only then:** v0.39 is safe.

---

## The Vision (v0.38 makes this possible)

A student walks in with an exam.

Marcus:
1. ✅ Scans it (v0.36+)
2. ✅ Reads it reliably (v0.37)
3. ✅ Understands its structure (v0.38)
4. → Generates study materials (v0.39)
5. → Identifies weaknesses (v0.40)
6. → Personalizes next steps (v0.41)
7. → Predicts readiness (v0.42+)

**Step 3 is complete. Steps 4-7 become possible.**

---

**Build Status:** Awaiting confirmation to proceed with v0.39
