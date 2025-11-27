# Metadata Contamination Tracking

## Overview

This implementation adds comprehensive metadata tracking to diagnose the issue where visual arts categories are appearing on math content.

## What Was Added

### 1. Tracking Infrastructure (`tsvkhan.py`)

**Line 159**: Added `metadata_tracking` dictionary that stores complete history when `verbose=True`

**Lines 277-306**: `_track_metadata()` method
- Records categories and grade_levels at each stage
- Captures source information (which topic, slug lookup, etc.)
- Tracks the complete evolution of metadata

**Lines 308-366**: `_report_metadata_contamination()` method
- Identifies resources with VISUAL_ART or ARTS categories
- Generates detailed report showing complete update history
- Writes to `metadata_contamination_report.txt`

### 2. Instrumentation Points

**Exercises** (lines 440-447):
- Track initial metadata from METADATA_BY_SLUG
- Track after set_metadata_from_ancestors()

**Videos** (lines 564-571):
- Track initial metadata from METADATA_BY_SLUG
- Track after set_metadata_from_ancestors()

**Sibling Sharing** (lines 338-348):
- Track before _share_sibling_metadata() overwrites
- Track after with sibling count

### 3. Report Generation (line 201-202)

Automatically generates report when chef completes in verbose mode.

## How to Use

### Option 1: Run with Verbose Flag

```bash
# Set up environment
source venv/bin/activate
source credentials/proxy_list.env
source credentials/crowdinkeys.env

# Run with verbose flag
./sushichef.py --lang=en --verbose --token=<your-token>
```

### Option 2: Use Test Script

```bash
chmod +x test_metadata_tracking.sh
./test_metadata_tracking.sh
```

### Option 3: Test Tracking Logic Only

```bash
# No dependencies required - just tests the mechanism
python test_tracking_logic.py
```

## Output

If metadata contamination is detected, you'll get a file `metadata_contamination_report.txt`:

```
================================================================================
METADATA CONTAMINATION REPORT
Found 5 resources with VISUAL_ART or ARTS categories
================================================================================

--------------------------------------------------------------------------------
Resource: Introduction to Algebra
Kind: video
Source ID: abc123xyz

Metadata History:

  Step 1: initial
    Source: METADATA_BY_SLUG[introduction-to-algebra]
    Categories: ['Algebra']
    Grade Levels: ['Upper Primary']

  Step 2: after_ancestors
    Source: parent: Math Basics
    Categories: ['Mathematics', 'Algebra']
    Grade Levels: ['Upper Primary']

  Step 3: before_sibling_sharing
    Source: topic: Math Basics
    Categories: ['Mathematics', 'Algebra']
    Grade Levels: ['Upper Primary']

  Step 4: after_sibling_sharing
    Source: topic: Math Basics, 10 siblings
    Categories: ['Mathematics', 'Algebra', 'Visual Art', 'Arts']  <-- CONTAMINATION!
    Grade Levels: ['Upper Primary', 'Lower Secondary', 'Tertiary']

--------------------------------------------------------------------------------
[More contaminated resources...]
================================================================================
```

## What the Report Shows

For each contaminated resource, you'll see:

1. **Resource Info**: Title, kind (video/exercise), source ID
2. **Complete History**: Every metadata update from creation to final state
3. **Source Attribution**: Which topic, slug lookup, or sibling group caused each change
4. **Exact Contamination Point**: You can see exactly which step introduced the unwanted categories

## Interpreting Results

### If contamination appears at "initial" stage:
- **Problem**: Resource slug matches a topic slug in METADATA_BY_SLUG
- **Example**: Video "v/humanities" becomes "humanities" and gets humanities metadata
- **Solution**: Ensure METADATA_BY_SLUG only has resource-specific slugs, not topic slugs

### If contamination appears at "after_ancestors" stage:
- **Problem**: set_metadata_from_ancestors() is pulling from wrong ancestors
- **Example**: Video inherits from domain-level "Humanities" topic
- **Solution**: Modify ancestor inheritance to skip domain-level nodes or limit depth

### If contamination appears at "after_sibling_sharing" stage:
- **Problem**: _share_sibling_metadata() is spreading metadata across unrelated resources
- **Example**: Topic has mixed-subject children, all get combined metadata
- **Solution**: Remove or modify _share_sibling_metadata() behavior

## Next Steps

Once you run this with `--verbose` and get the contamination report:

1. Review the report to see which stage introduces contamination
2. Check the "Source" field to see which topic or slug is responsible
3. Use the findings to determine root cause
4. Implement targeted fix based on actual contamination pattern

This replaces speculation with concrete evidence!
