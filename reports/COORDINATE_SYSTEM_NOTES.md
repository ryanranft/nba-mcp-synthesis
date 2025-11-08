# Coordinate System Investigation Notes

**Date**: November 6, 2025
**Status**: Undocumented system - cannot be used for distance validation without further research

---

## Summary

The `hoopr_play_by_play` table contains coordinate fields (`coordinate_x`, `coordinate_y`) that represent **court position**, NOT distance from basket. Initial analysis incorrectly assumed coordinates represented distance, leading to unfounded claims that were subsequently retracted.

---

## Database Schema

```sql
coordinate_x (double precision)      -- Court position X-axis
coordinate_y (double precision)      -- Court position Y-axis
coordinate_x_raw (double precision)  -- Raw/source coordinates
coordinate_y_raw (double precision)  -- Raw/source coordinates
```

---

## Key Findings

### Coordinates Are Court Position, Not Distance

**Evidence**:

| Shot Type | Text Description | Coordinates | Naive Distance Calc | Actual Distance |
|-----------|------------------|-------------|---------------------|-----------------|
| Dunk | "1-foot dunk" | (~±40, 0) | ~40 units | < 1 foot |
| Layup | "2-foot layup" | (~±39, ±2) | ~39 units | 2-3 feet |
| Layup | "3-foot layup" | (~±39, ±3) | ~39 units | 3 feet |

**Conclusion**: If coordinates were "feet from basket", dunks would show ~0-1 units, not ~40 units.

### Coordinate System Properties

**Observed Ranges**:
- Valid coordinates: approximately -50 to +50 on both axes
- Invalid coordinates: ±214,748,406.75 (likely NULL/missing markers - 32-bit int overflow)

**Pattern Analysis**:
- Dunks cluster around x = ±38 to ±42, y = ±0 to ±2
- This suggests baskets are located at approximately (±41-42, 0)
- X-axis appears to be length of court
- Y-axis appears to be width of court (sideline to sideline)

**Hypothesis** (unverified):
- Origin (0,0) = Center court
- X-axis = Length (±42-47 units from center to each basket)
- Y-axis = Width (±25 units from center to each sideline)
- Units = Unknown (possibly 1/10th feet, or proprietary ESPN scale)

---

## Why We Cannot Use for Distance Validation

Without documentation, we lack:

1. **Origin point**: Where is (0,0)? Center court? One baseline?
2. **Basket locations**: What are the exact coordinates of each basket?
3. **Scaling factor**: What does 1 unit represent? (feet? pixels? other?)
4. **Transformation formula**: How to convert court position → shot distance?

**Example**:
- Shot at (23.75, -15.0)
- If basket is at (41.75, 0), distance = √[(41.75-23.75)² + (0-(-15))²] = √[324+225] = 23.43 units
- But what is 23.43 units in feet? Unknown without scaling factor.

---

## Data Quality Issues

**Missing/Invalid Coordinates**:
```
min(coordinate_x): -214748406.75  (overflow marker)
max(coordinate_x):  214748406.75
```

Many shots have missing or placeholder coordinates, making systematic analysis incomplete.

---

## Recommendations

### Do NOT Use Coordinates For:
- ❌ Shot distance validation
- ❌ Verifying official scorer accuracy
- ❌ Classifying 2PA vs 3PA based on distance
- ❌ Any analysis without coordinate system documentation

### Potential Future Work:

If coordinate system documentation is needed:

1. **Reverse Engineering Approach**:
   - Find known reference points (e.g., free throw line = 15 feet from basket)
   - Map coordinates to known court positions
   - Derive transformation formula
   - Validate against multiple games

2. **Required Reference Points**:
   - Free throw line (15 ft from basket, center of lane)
   - 3-point arc (23.75 ft from basket at top)
   - 3-point corner (22 ft from basket in corners)
   - Baseline (0 ft from basket)

3. **Validation**:
   - Compare calculated distances to stated distances in text
   - Verify dunks show 0-2 ft distance
   - Verify corner 3s show ~22 ft distance
   - Cross-validate with official NBA court dimensions

---

## What Went Wrong (Lessons Learned)

**Our Mistake**:
1. Assumed (0,0) = basket location (incorrect)
2. Assumed units = feet from basket (incorrect)
3. Calculated "distances" using Pythagorean theorem (meaningless without knowing system)
4. Made strong claims about "official scorer errors" based on bad assumptions

**User Caught Error**:
- User questioned coordinate analysis
- Investigation revealed dunks showing "40 feet" distance (obviously wrong)
- Correctly identified that coordinate system was misunderstood

**Correct Approach**:
1. ✅ Always validate assumptions against known reference points
2. ✅ Check sanity: Do dunks show ~0 ft? Do half-court shots show ~47 ft?
3. ✅ Question results that seem unlikely
4. ✅ User feedback is valuable - don't dismiss skepticism

---

## Current Parser Status (Unaffected)

The coordinate system issue does NOT affect our parser:

✅ **Parser Uses**:
- Play-by-play text descriptions (e.g., "22-foot shot", "three point")
- Points scored (2 or 3 points - definitive)
- Distance thresholds (>= 23 ft for unlabeled shots)

❌ **Parser Does NOT Use**:
- coordinate_x or coordinate_y fields
- Any calculated distances from coordinates

**Result**: Parser remains 100% internally consistent and 98.67% match with Hoopr.

---

## References

- **Coordinate Fields**: `hoopr_play_by_play.coordinate_x`, `coordinate_y`
- **Investigation**: Game 401654761, sequences 234-238, 359, 408
- **Corrected Reports**:
  - `reports/OFFICIAL_SCORER_ERRORS.md` (retitled "Box Score Discrepancy Analysis")
  - `reports/FINAL_PARSER_ACCURACY.md` (claims retracted)

---

*Investigation completed: November 6, 2025*
*Status: Coordinate system undocumented - not suitable for distance validation*
*Parser status: Unaffected - does not use coordinates*
