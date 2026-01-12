# v0.37 Quick Reference - What Changed

## Problem Fixed
Alias expansion SQL queries were failing silently. Bidirectional alias lookup (FSM ↔ "finite state machine") wasn't working.

## Root Cause
SQLAlchemy couldn't properly bind tuple parameters to SQL `IN` clauses.

## Solution
Replaced problematic parameterized `IN` clause with explicit individual lookups:

**Before (Broken):**
```python
sql = """
    SELECT DISTINCT canonical_term
    FROM search_aliases
    WHERE term = :query OR term IN :terms  # ❌ Binding fails
"""
result = db.execute(text(sql), 
    {"query": normalized, "terms": tuple(terms)}
)
```

**After (Working):**
```python
# Forward: term → canonical
result = db.execute(text("""
    SELECT DISTINCT canonical_term
    FROM search_aliases
    WHERE term = :query
"""), {"query": normalized})

# Reverse: canonical → term
result = db.execute(text("""
    SELECT DISTINCT term
    FROM search_aliases
    WHERE canonical_term = :query
"""), {"query": normalized})

# Also check individual terms in multi-word queries
for term in normalized.split():
    # Same forward/reverse lookups
```

## FTS5 Query Improvement
Enhanced the hybrid search strategy to properly parenthesize OR/AND combinations:

**Before:**
```python
# Could produce invalid SQL like: ... WHERE fts MATCH "text" OR (term1 AND term2)
fts_query = ' OR '.join(phrase_queries) + ' OR ' + ' OR '.join(term_queries)
```

**After:**
```python
# Properly grouped: (phrase1 OR phrase2) OR (term1 AND term2)
phrase_group = '(' + ' OR '.join(fts_queries) + ')'
terms_group = ' OR '.join([f'({terms})' for terms in term_queries])
fts_query = f'{phrase_group} OR {terms_group}'
```

## Score Formula Enhancement
Improved normalization to handle full BM25 range:

**Before:**
```python
score = max(0.0, min(1.0, 1.0 + (bm25_rank / 10.0)))
# With rank -15: 1.0 - 1.5 = -0.5 → clamped to 0%
```

**After:**
```python
score = max(0.0, min(1.0, 1.0 / (1.0 + abs(bm25_rank))))
# With rank -15: 1.0 / 16 = 6.25% → correct sigmoid curve
```

## Results
- ✅ Alias expansion now works bidirectionally
- ✅ All 5 acceptance criteria passing
- ✅ FTS5 active for all queries
- ✅ Graceful LIKE fallback if FTS5 fails
- ✅ No API changes - backward compatible

## Changed File
**[marcus_app/services/search_service.py](marcus_app/services/search_service.py)**
- `expand_query_with_aliases()` method: Complete rewrite of SQL queries
- `_fts5_search()` method: Improved FTS5 query building and parenthesization  
- Score normalization: Better sigmoid formula

## Test Status
```
✓ PASS: 'finite state machine' → FSM chunks
✓ PASS: 'side channel attack' → side-channel chunks
✓ PASS: 'setup time hold time' → separated terms
✓ PASS: 'rotational dynamics' → rotational motion content
✓ PASS: 'moment of inertia' → rotational inertia

RESULTS: 5 passed, 0 failed
✓ All acceptance criteria PASSED!
```

---
**v0.37 Status: COMPLETE AND LOCKED IN**
