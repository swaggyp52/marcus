# v0.38 Quick Reference

## What v0.38 Does

Generates study pack blueprints from assessment artifacts.

**Input:** One exam/quiz/homework/review document  
**Output:** Structured blueprint with topics, skills, lessons, citations, checklist

## Example Usage

```bash
# 1. Upload artifact
POST /api/artifacts { file }
→ artifact_id = 5

# 2. Extract text and chunk
POST /api/chunks/{artifact_id}
→ 50 chunks created

# 3. Generate blueprint
POST /api/study-packs {
  "artifact_id": 5,
  "assignment_id": 1,
  "class_id": 2
}
→ StudyPack with 8 topics, 20+ skills, 100% grounded
```

## Data Model

```
StudyPack
├── StudyTopic (8-9 per blueprint)
│   ├── StudySkill (2-3 per topic: derive/conceptual/memorize)
│   ├── StudyLesson (what_it_is, subpoints, mistakes)
│   └── StudyCitation (grounded links to chunks)
└── StudyChecklistItem (one per topic)
```

## Key Features

✅ **Multi-Strategy Topic Extraction**
- Problem/Question parsing (Problem 3: FSM Design)
- Section-based extraction (## Heading)
- Fallback to generic if no structure

✅ **Auto-Skill Generation**
- Derive: For computational/design content
- Conceptual: Always present
- Memorize: For definitions/terminology

✅ **Auto-Lesson Generation**
- What it is: One-sentence definition
- Key subpoints: Extracted bullet points
- Common mistakes: Pattern matching

✅ **100% Citation Grounding**
- Links topics to specific chunks
- Prevents hallucination
- Explicit "ungrounded" flag if no match

✅ **Study Checklist**
- Ordered steps per topic
- Effort estimates (S/M/L)
- Self-check prompts for learning verification

## API Endpoints

### POST /api/study-packs
Generate blueprint
```json
{
  "assignment_id": 1,
  "class_id": 2,
  "artifact_id": 5
}
```

### GET /api/study-packs/{study_pack_id}
Retrieve by ID

### GET /api/assignments/{assignment_id}/study-packs
List for assignment

### PUT /api/study-packs/{study_pack_id}?status=published
Update status

## Test Results

| Artifact | Topics | Skills | Status |
|----------|--------|--------|--------|
| Threat_Modeling.md | 9 | 20+ | ✅ |
| Side_Channel_Analysis.md | 8 | 18+ | ✅ |
| Midterm_Review.md | 8 | 19+ | ✅ |
| (x2 for different assignments) | Similar | Similar | ✅ |

**All tests passed. 100% grounding achieved.**

## Database

New tables:
- study_packs
- study_topics
- study_skills
- study_lessons
- study_citations
- study_checklist_items

Auto-created on first app startup.

## Important: This Is NOT

❌ Lesson generation (that's v0.39)  
❌ Practice problems (that's v0.39+)  
❌ Mastery tracking (that's v0.40)  

## Important: This IS

✅ **The foundation for intelligent tutoring**
- Transforms raw assessment into structured understanding
- Explicitly grounded (citations, not hallucination)
- Verifiable (student can check source)
- Boring in the best way (deterministic, reliable)

## Quality Metrics

- **Topics per artifact:** 8-9 (good coverage)
- **Citation grounding:** 100% (perfect)
- **Ungrounded topics:** 0% (excellent)
- **API endpoints:** 4/4 (complete)
- **Test passing rate:** 100% (perfect)

---

**v0.38 Status: LOCKED IN**  
**Ready for v0.39 Lesson Generation**
