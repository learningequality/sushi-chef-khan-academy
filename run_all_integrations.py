#!/usr/bin/env python
"""
Run integration tests for all supported Khan Academy language/curriculum variants.

This script loops through all supported language and curriculum combinations
from LANGUAGE_CURRICULUM_MAP and runs each chef run in a subprocess to isolate
memory and avoid global state issues.

The logic for determining what to run:
1. If language is not supported: Skip entirely
2. If language is supported and has curricula:
   a. If at least one curriculum is supported: Run only supported curricula
   b. If no curricula are supported: Run "pure language" version (no variant)
3. If language is supported and has no curricula: Run "pure language" version
"""
import subprocess
import sys
import argparse
import ast


def load_language_curriculum_map():
    """Load LANGUAGE_CURRICULUM_MAP from constants.py without importing it."""
    with open('constants.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the LANGUAGE_CURRICULUM_MAP section
    begin_marker = "LANGUAGE_CURRICULUM_MAP = ["
    end_marker = "# END AUTO-GENERATED LANGUAGE_CURRICULUM_MAP"

    start_idx = content.find(begin_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError("Could not find LANGUAGE_CURRICULUM_MAP markers in constants.py")

    # Extract the list definition
    map_code = content[start_idx:end_idx]
    map_code = map_code[len("LANGUAGE_CURRICULUM_MAP = "):]

    # Evaluate the Python literal
    return ast.literal_eval(map_code)


def get_runs_to_execute():
    """
    Determine which language/curriculum combinations should be run.

    Returns:
        list: List of tuples (le_lang, variant, description) where variant may be None
    """
    # Load the language curriculum map
    lang_map = load_language_curriculum_map()
    runs = []

    for lang_entry in lang_map:
        le_lang = lang_entry["le_lang"]
        is_lang_supported = lang_entry.get("supported", False)

        # Skip unsupported languages entirely
        if not is_lang_supported:
            continue

        # If language has curricula, check if any are supported
        if "curricula" in lang_entry:
            supported_curricula = [
                curr for curr in lang_entry["curricula"]
                if curr.get("supported", False)
            ]

            if supported_curricula:
                # Run each supported curriculum variant
                for curriculum in supported_curricula:
                    variant = curriculum["curriculum_key"]
                    title = curriculum.get("title", f"{le_lang}/{variant}")
                    runs.append((le_lang, variant, title))
            else:
                # Language is supported but no curricula are - run pure language
                title = lang_entry.get("title", f"Khan Academy ({le_lang})")
                runs.append((le_lang, None, title))
        else:
            # No curricula defined - run pure language version
            title = lang_entry.get("title", f"Khan Academy ({le_lang})")
            runs.append((le_lang, None, title))

    return runs


def run_chef_subprocess(le_lang, variant=None, dry_run=False, extra_args=None):
    """
    Run the Khan Academy chef in a subprocess for the given language/variant.

    Args:
        le_lang: le-utils language code
        variant: Optional curriculum variant key
        dry_run: If True, only print what would be run
        extra_args: Additional arguments to pass to the chef

    Returns:
        int: Return code from subprocess (0 for success, non-zero for failure)
    """
    # Build command
    cmd = [sys.executable, "sushichef.py", f"--lang={le_lang}"]

    if variant:
        cmd.append(f"--variant={variant}")

    # Add any extra arguments
    if extra_args:
        cmd.extend(extra_args)

    # Log what we're running
    variant_str = f" variant={variant}" if variant else ""
    print(f"\n{'='*80}")
    print(f"Running: lang={le_lang}{variant_str}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")

    if dry_run:
        print("[DRY RUN] Would execute the above command\n")
        return 0

    # Run the subprocess
    try:
        result = subprocess.run(
            cmd,
            check=False,  # Don't raise exception on non-zero exit
            capture_output=False,  # Let output stream to console
        )
        return result.returncode
    except Exception as e:
        print(f"ERROR: Exception while running chef: {e}")
        return 1


def main():
    """Main entry point for running all integration tests."""
    parser = argparse.ArgumentParser(
        description="Run Khan Academy chef for all supported language/curriculum variants"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be run without actually executing"
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue running even if some runs fail"
    )
    parser.add_argument(
        "--filter-lang",
        help="Only run languages matching this filter (e.g., 'en' or 'pt-BR')"
    )
    parser.add_argument(
        "--filter-variant",
        help="Only run curriculum variants matching this filter (e.g., 'us-cc')"
    )

    # Allow passing through arguments to the chef
    parser.add_argument(
        "chef_args",
        nargs="*",
        help="Additional arguments to pass to the chef"
    )

    args = parser.parse_args()

    # Get all runs to execute
    all_runs = get_runs_to_execute()

    # Apply filters if specified
    if args.filter_lang:
        all_runs = [r for r in all_runs if r[0] == args.filter_lang]
    if args.filter_variant:
        all_runs = [r for r in all_runs if r[1] == args.filter_variant]

    # Summary
    print(f"Khan Academy Integration Test Runner")
    print(f"{'='*80}\n")
    print(f"Total runs to execute: {len(all_runs)}")
    print(f"Dry run: {args.dry_run}")
    print(f"Continue on error: {args.continue_on_error}")
    if args.filter_lang:
        print(f"Language filter: {args.filter_lang}")
    if args.filter_variant:
        print(f"Variant filter: {args.filter_variant}")
    print()

    # List all runs
    print("Scheduled runs:")
    for i, (lang, variant, title) in enumerate(all_runs, 1):
        variant_str = f" / {variant}" if variant else ""
        print(f"  {i}. {lang}{variant_str}: {title}")
    print()

    # Track results
    results = []
    failed_runs = []

    # Execute each run
    for i, (lang, variant, title) in enumerate(all_runs, 1):
        print(f"\n{'#'*80}")
        print(f"# Run {i}/{len(all_runs)}: {lang}" + (f"/{variant}" if variant else ""))
        print(f"# {title}")
        print(f"{'#'*80}")

        returncode = run_chef_subprocess(
            lang,
            variant=variant,
            dry_run=args.dry_run,
            extra_args=args.chef_args
        )

        results.append((lang, variant, title, returncode))

        if returncode != 0:
            failed_runs.append((lang, variant, title))
            print(f"\n❌ FAILED: {lang}" + (f"/{variant}" if variant else ""))

            if not args.continue_on_error:
                print(f"\nStopping due to failure. Use --continue-on-error to continue.")
                break
        else:
            print(f"\n✓ SUCCESS: {lang}" + (f"/{variant}" if variant else ""))

    # Final summary
    print(f"\n\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}\n")

    successful = len([r for r in results if r[3] == 0])
    failed = len([r for r in results if r[3] != 0])

    print(f"Total runs: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed_runs:
        print(f"\nFailed runs:")
        for lang, variant, title in failed_runs:
            variant_str = f"/{variant}" if variant else ""
            print(f"  ❌ {lang}{variant_str}: {title}")

    # Exit with error if any runs failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
