# Integration Test Runner

## Overview

The `run_all_integrations.py` script runs the Khan Academy chef for all supported language/curriculum variants in separate subprocesses. This isolates memory and avoids global state issues that could arise from running all variants in a single process.

## SUPPORTED Flags

The `constants.py` file contains `LANGUAGE_CURRICULUM_MAP` with `supported` flags at both the language and curriculum level:

- **Language-level `supported` flag**: Indicates if the language should be imported at all
- **Curriculum-level `supported` flag**: For languages with multiple curriculum variants, indicates which specific variants should be imported

### Logic for Determining What to Run

1. **If language is not supported**: Skip entirely
2. **If language is supported and has curricula**:
   - If at least one curriculum is supported: Run only supported curricula
   - If no curricula are supported: Run "pure language" version (no variant)
3. **If language is supported and has no curricula**: Run "pure language" version

### Currently Supported

As of the latest update:
- **37 supported languages** out of 52 total
- **3 supported curriculum variants**:
  - `en/in-in` - English (CBSE India Curriculum)
  - `en/ph-ph` - English (Philippines Curriculum)
  - `en/us-cc` - English (US Common Core)

## Usage

### Run all supported variants

```bash
python run_all_integrations.py
```

### Dry run (show what would be executed)

```bash
python run_all_integrations.py --dry-run
```

### Continue on error

By default, the script stops at the first failure. To continue running all variants even if some fail:

```bash
python run_all_integrations.py --continue-on-error
```

### Filter by language

```bash
python run_all_integrations.py --filter-lang en
```

### Filter by curriculum variant

```bash
python run_all_integrations.py --filter-variant us-cc
```

### Pass additional arguments to the chef

Any additional arguments after `--` are passed through to each chef run:

```bash
python run_all_integrations.py -- --download-attempts=3 --compress
```

## Maintaining SUPPORTED Flags

The `analyze_tsv_languages.py` script automatically preserves `supported` flags when regenerating `LANGUAGE_CURRICULUM_MAP`.

### To add support for a new language:

1. Edit `constants.py` and set `"supported": True` for the language entry
2. Run `python analyze_tsv_languages.py` to verify the flag is preserved
3. Commit the changes

### To add support for a new curriculum variant:

1. Edit `constants.py` and set `"supported": True` for the specific curriculum entry
2. Add appropriate `title` and `description` if needed
3. Run `python analyze_tsv_languages.py` to verify the flag is preserved
4. Commit the changes

## Helper Functions

The `constants.py` module provides helper functions:

```python
from constants import get_supported_languages, get_supported_language_curriculum_runs

# Get list of all supported language codes
langs = get_supported_languages()
# Returns: ['az', 'bg', 'bn', 'cs', 'da', 'de', 'el', 'en', ...]

# Get list of all (language, variant) tuples to run
runs = get_supported_language_curriculum_runs()
# Returns: [('az', None), ('bg', None), ..., ('en', 'in-in'), ('en', 'ph-ph'), ('en', 'us-cc'), ...]
```

## Subprocess Isolation

Each language/curriculum variant runs in a separate subprocess, which:
- **Isolates memory**: Each run starts fresh, avoiding memory leaks from global state
- **Enables monitoring**: Failed runs are logged separately
- **Improves reliability**: One failure doesn't crash the entire batch

The runner monitors each subprocess and logs success/failure, providing a final summary report.
