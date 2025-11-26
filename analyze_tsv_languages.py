#!/usr/bin/env python
"""
Script to analyze Khan Academy TSV exports for available languages and curriculum codes.

This script:
1. Discovers all available language codes from the Khan Academy GCS export bucket
2. Downloads the latest TSV export for each language
3. Parses English TSV first to identify cross-contamination curriculum codes
4. Filters out English curriculum codes from other languages
5. Generates a consolidated lookup with le-utils language codes, titles, and descriptions
"""

import csv
import json
import os
import re
from html import unescape
from google.cloud import storage
from le_utils.constants import languages as le_languages

# Import constants from the existing codebase
from constants import (
    KHAN_ACADEMY_LANGUAGE_MAPPING,
    LANGUAGE_CURRICULUM_MAP,
)

# Constants
KHAN_TSV_EXPORT_BUCKET_NAME = "public-content-export-data"
KHAN_TSV_CACHE_DIR = os.path.join("chefdata", "khantsvcache")
OUTPUT_JSON_FILE = "language_curriculum_analysis.json"

# Reverse mapping: le-utils code -> KA kalang
LE_TO_KA_MAPPING = {v: k for k, v in KHAN_ACADEMY_LANGUAGE_MAPPING.items()}


def get_le_lang_code(kalang):
    """
    Convert Khan Academy language code to le-utils language code.

    Args:
        kalang: Khan Academy language code (e.g., 'pt', 'fv', 'zh-hans')

    Returns:
        str: le-utils language code (e.g., 'pt-BR', 'fuv', 'zh-CN')
    """
    # Check if this kalang has a reverse mapping
    if kalang in LE_TO_KA_MAPPING:
        return LE_TO_KA_MAPPING[kalang]
    return kalang


def discover_available_languages():
    """
    Scan the GCS bucket to find all available language codes.

    Returns:
        list: Sorted list of unique KA language codes (e.g., ['en', 'es', 'fr', ...])
    """
    print("Discovering available languages from GCS bucket...")
    storage_client = storage.Client.create_anonymous_client()
    blobs = storage_client.list_blobs(KHAN_TSV_EXPORT_BUCKET_NAME)

    # Extract language codes from blob names matching pattern: {lang}-export-...
    export_file_pattern = re.compile(r'^([a-z]{2}(?:-[a-z]+)?)-export-')
    language_codes = set()

    for blob in blobs:
        match = export_file_pattern.match(blob.name)
        if match:
            lang_code = match.group(1)
            language_codes.add(lang_code)

    sorted_languages = sorted(language_codes)
    print(f"Found {len(sorted_languages)} KA languages: {', '.join(sorted_languages)}")
    return sorted_languages


def download_latest_tsv_export(kalang, filepath):
    """
    Download latest TSV data for the language code `kalang` from the exports
    bucket and save it to the local path `filepath`.

    Args:
        kalang: Khan Academy language code (e.g., 'en', 'es', 'pt')
        filepath: Local file path to save the downloaded TSV

    Returns:
        bool: True if successful, False otherwise
    """
    storage_client = storage.Client.create_anonymous_client()
    blobs = storage_client.list_blobs(
        KHAN_TSV_EXPORT_BUCKET_NAME, prefix=kalang + "-export"
    )
    valid_file_re = re.compile(
        kalang
        + r"-export-[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+-]{1}[0-9]{4}\.tsv"
    )
    blob_names = [blob.name for blob in blobs if valid_file_re.match(blob.name)]

    if not blob_names:
        print(f"  WARNING: No TSV files found for language '{kalang}'")
        return False

    latest_blob_name = sorted(blob_names, reverse=True)[0]
    print(f"  Downloading: {latest_blob_name}")

    bucket = storage_client.bucket(KHAN_TSV_EXPORT_BUCKET_NAME)
    blob = bucket.blob(latest_blob_name)
    blob.download_to_filename(filepath)
    return True


def strip_html_tags(html_text):
    """
    Remove HTML tags and decode HTML entities from text.

    Args:
        html_text: HTML string

    Returns:
        str: Plain text
    """
    if not html_text:
        return ""
    # Simple HTML tag removal (not perfect but good enough for descriptions)
    import re
    text = re.sub(r'<[^>]+>', '', html_text)
    # Decode HTML entities
    text = unescape(text)
    return text.strip()


def extract_curriculum_info_from_tsv(filepath, lang_code):
    """
    Parse a TSV file and extract curriculum information.

    Args:
        filepath: Path to the TSV file
        lang_code: le-utils language code for title/description lookup

    Returns:
        set: Set of curriculum_key values found in the file
    """
    curriculum_codes = set()

    try:
        with open(filepath, encoding="utf-8-sig") as tsvfile:
            reader = csv.DictReader(tsvfile, dialect="excel-tab")
            for row in reader:
                curriculum_key = row.get("curriculum_key", "").strip()
                if curriculum_key:
                    curriculum_codes.add(curriculum_key)
    except Exception as e:
        print(f"  ERROR parsing {filepath}: {e}")
        return set()

    return curriculum_codes


def analyze_all_languages():
    """
    Main function to discover languages, download TSVs, and extract curriculum codes.
    Filters out English curriculum codes from other languages.

    Returns:
        list: List of language objects with curricula information
    """
    # Ensure cache directory exists
    if not os.path.exists(KHAN_TSV_CACHE_DIR):
        os.makedirs(KHAN_TSV_CACHE_DIR, exist_ok=True)

    # Discover available languages
    kalangs = discover_available_languages()

    # Process English first to get its curriculum codes
    print("\n" + "="*80)
    print("STEP 1: Processing English to identify cross-contamination codes")
    print("="*80)

    english_curriculum_codes = set()
    if 'en' in kalangs:
        print("\nLanguage: en (English)")
        filepath = os.path.join(KHAN_TSV_CACHE_DIR, "topic_tree_export.en.tsv")

        if not os.path.exists(filepath):
            download_latest_tsv_export('en', filepath)
        else:
            print(f"  Using cached file: {filepath}")

        english_curriculum_codes = extract_curriculum_info_from_tsv(filepath, 'en')
        print(f"  Found {len(english_curriculum_codes)} curriculum codes: {', '.join(sorted(english_curriculum_codes))}")

    # Process all other languages
    print("\n" + "="*80)
    print("STEP 2: Processing all languages and filtering cross-contamination")
    print("="*80)

    results = []

    for kalang in sorted(kalangs):
        le_lang = get_le_lang_code(kalang)
        print(f"\nLanguage: {kalang} -> le-utils: {le_lang}")

        # Get language object from le-utils
        try:
            lang_obj = le_languages.getlang(le_lang)
            if lang_obj is None:
                print(f"  WARNING: Language '{le_lang}' not found in le-utils, skipping")
                continue
        except Exception as e:
            print(f"  WARNING: Language '{le_lang}' not found in le-utils ({e}), skipping")
            continue

        # Determine filename
        filename = f"topic_tree_export.{kalang}.tsv"
        filepath = os.path.join(KHAN_TSV_CACHE_DIR, filename)

        # Download the TSV if needed
        if not os.path.exists(filepath):
            success = download_latest_tsv_export(kalang, filepath)
            if not success:
                continue
        else:
            print(f"  Using cached file: {filepath}")

        # Extract curriculum codes
        curricula_codes = extract_curriculum_info_from_tsv(filepath, le_lang)

        # Filter out English curriculum codes for non-English languages
        if kalang != 'en':
            original_count = len(curricula_codes)
            curricula_codes = curricula_codes - english_curriculum_codes
            filtered_count = original_count - len(curricula_codes)
            if filtered_count > 0:
                print(f"  Filtered out {filtered_count} English curriculum codes")

        # Build language object
        lang_data = {
            "ka_lang": kalang,
            "le_lang": le_lang,
            "name": lang_obj.name,
            "native_name": lang_obj.native_name,
        }

        # Find existing entry in LANGUAGE_CURRICULUM_MAP to preserve titles/descriptions
        existing_entry = None
        for entry in LANGUAGE_CURRICULUM_MAP:
            if entry["le_lang"] == le_lang:
                existing_entry = entry
                break

        # Add curricula if any exist
        if curricula_codes:
            # Build curricula list with info from existing LANGUAGE_CURRICULUM_MAP
            curricula_list = []
            for curriculum_key in sorted(curricula_codes):
                curriculum_obj = {
                    "curriculum_key": curriculum_key,
                }

                # Try to get title, description, and supported from existing entry
                title = ""
                description = ""
                supported = False  # Default to False for new curricula
                if existing_entry and "curricula" in existing_entry:
                    for existing_curr in existing_entry["curricula"]:
                        if existing_curr["curriculum_key"] == curriculum_key:
                            title = existing_curr.get("title", "")
                            description = existing_curr.get("description", "")
                            supported = existing_curr.get("supported", False)
                            break

                curriculum_obj["title"] = title
                curriculum_obj["description"] = description
                curriculum_obj["supported"] = supported

                curricula_list.append(curriculum_obj)

            lang_data["curricula"] = curricula_list
            print(f"  Unique curricula ({len(curricula_list)}): {', '.join([c['curriculum_key'] for c in curricula_list])}")
        else:
            # No curricula - get default title, description, and supported from existing entry or use fallback
            if existing_entry:
                lang_data["title"] = existing_entry.get("title", f"Khan Academy ({lang_obj.first_native_name})")
                lang_data["description"] = existing_entry.get("description", f"Khan Academy content for {lang_obj.name}.")
                lang_data["supported"] = existing_entry.get("supported", False)
            else:
                # Fallback for new languages not yet in LANGUAGE_CURRICULUM_MAP
                lang_data["title"] = f"Khan Academy ({lang_obj.first_native_name})"
                lang_data["description"] = f"Khan Academy content for {lang_obj.name}."
                lang_data["supported"] = False  # Default to False for new languages

            print(f"  No curricula - using default title and description")

        results.append(lang_data)

    return results


def generate_constants_update(results):
    """
    Generate Python code to update constants.py with the new language data.

    Args:
        results: List of language objects with curricula information

    Returns:
        str: Python code defining the LANGUAGE_CURRICULUM_MAP constant
    """
    lines = []
    lines.append("# BEGIN AUTO-GENERATED LANGUAGE_CURRICULUM_MAP")
    lines.append("# This section is auto-generated by analyze_tsv_languages.py")
    lines.append("# Do not manually edit between BEGIN and END markers")
    lines.append("#")
    lines.append("# Auto-generated comprehensive language and curriculum lookup")
    lines.append("# This constant consolidates information from Khan Academy TSV exports")
    lines.append("# and replaces SUPPORTED_LANGS, CHANNEL_TITLE_LOOKUP, and CHANNEL_DESCRIPTION_LOOKUP")
    lines.append("#")
    lines.append("# Each language entry contains:")
    lines.append("#   - ka_lang: Khan Academy language code")
    lines.append("#   - le_lang: le-utils language code")
    lines.append("#   - name: English name of the language")
    lines.append("#   - native_name: Native name of the language")
    lines.append("#   - curricula: Optional list of curriculum variants (if any)")
    lines.append("#   - title: Channel title (if no curricula)")
    lines.append("#   - description: Channel description (if no curricula)")
    lines.append("#   - supported: Whether this language/curriculum is supported (default: false for new additions)")
    lines.append("LANGUAGE_CURRICULUM_MAP = [")

    for lang in results:
        lines.append("    {")
        lines.append(f"        \"ka_lang\": {json.dumps(lang['ka_lang'], ensure_ascii=False)},")
        lines.append(f"        \"le_lang\": {json.dumps(lang['le_lang'], ensure_ascii=False)},")
        lines.append(f"        \"name\": {json.dumps(lang['name'], ensure_ascii=False)},")
        lines.append(f"        \"native_name\": {json.dumps(lang['native_name'], ensure_ascii=False)},")

        if "curricula" in lang:
            lines.append("        \"curricula\": [")
            for curriculum in lang["curricula"]:
                lines.append("            {")
                lines.append(f"                \"curriculum_key\": {json.dumps(curriculum['curriculum_key'], ensure_ascii=False)},")
                lines.append(f"                \"title\": {json.dumps(curriculum['title'], ensure_ascii=False)},")
                lines.append(f"                \"description\": {json.dumps(curriculum['description'], ensure_ascii=False)},")
                lines.append(f"                \"supported\": {curriculum.get('supported', False)},")
                lines.append("            },")
            lines.append("        ],")
        else:
            lines.append(f"        \"title\": {json.dumps(lang.get('title', ''), ensure_ascii=False)},")
            lines.append(f"        \"description\": {json.dumps(lang.get('description', ''), ensure_ascii=False)},")
            lines.append(f"        \"supported\": {lang.get('supported', False)},")

        lines.append("    },")

    lines.append("]")
    lines.append("# END AUTO-GENERATED LANGUAGE_CURRICULUM_MAP")

    return "\n".join(lines)


def generate_report(results):
    """
    Generate and display a formatted report of languages and curriculum codes.
    Also updates constants.py with the new data.

    Args:
        results: List of language objects with curricula information
    """
    print("\n" + "="*80)
    print("CONSOLIDATED LANGUAGE AND CURRICULUM LOOKUP")
    print("="*80)

    # Statistics
    total_languages = len(results)
    languages_with_curricula = sum(1 for lang in results if "curricula" in lang)
    total_unique_curricula = len(set(
        c["curriculum_key"]
        for lang in results
        if "curricula" in lang
        for c in lang["curricula"]
    ))

    print(f"\nSummary:")
    print(f"  Total languages: {total_languages}")
    print(f"  Languages with curricula: {languages_with_curricula}")
    print(f"  Languages without curricula: {total_languages - languages_with_curricula}")
    print(f"  Total unique curriculum codes: {total_unique_curricula}")

    # Detailed breakdown
    print(f"\nDetailed Breakdown:")
    print("-" * 80)

    for lang in results:
        print(f"\nLanguage: {lang['le_lang']} ({lang['native_name']})")
        print(f"  KA lang: {lang['ka_lang']}")

        if "curricula" in lang:
            print(f"  Curricula ({len(lang['curricula'])}):")
            for curriculum in lang["curricula"]:
                title_status = "✓" if curriculum['title'] else "✗"
                desc_status = "✓" if curriculum['description'] else "✗"
                print(f"    - {curriculum['curriculum_key']}: [T:{title_status} D:{desc_status}] {curriculum['title'] or '(needs title)'}")
        else:
            print(f"  Title: {lang.get('title', 'N/A')[:60]}...")
            print(f"  Description: {lang.get('description', 'N/A')[:80]}...")

    # All unique curriculum codes
    all_curricula = sorted(set(
        c["curriculum_key"]
        for lang in results
        if "curricula" in lang
        for c in lang["curricula"]
    ))
    print(f"\n{'-'*80}")
    print(f"All Unique Curriculum Codes ({len(all_curricula)}):")
    print(f"  {', '.join(all_curricula)}")

    # Generate constants update
    print(f"\n{'-'*80}")
    print("Generating constants update...")

    constants_code = generate_constants_update(results)

    # Read current constants.py
    constants_file = "constants.py"
    with open(constants_file, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # Check if markers exist
    begin_marker = "# BEGIN AUTO-GENERATED LANGUAGE_CURRICULUM_MAP"
    end_marker = "# END AUTO-GENERATED LANGUAGE_CURRICULUM_MAP"

    if begin_marker in current_content and end_marker in current_content:
        # Replace the section between markers
        print("  Replacing existing LANGUAGE_CURRICULUM_MAP section...")
        before = current_content.split(begin_marker)[0]
        after = current_content.split(end_marker)[1]
        new_content = before + constants_code + after

        with open(constants_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  LANGUAGE_CURRICULUM_MAP updated in: {constants_file}")
    else:
        # Append to constants.py
        print("  Adding new LANGUAGE_CURRICULUM_MAP section...")
        with open(constants_file, 'a', encoding='utf-8') as f:
            f.write("\n\n")
            f.write(constants_code)
        print(f"  LANGUAGE_CURRICULUM_MAP added to: {constants_file}")


def main():
    """Main entry point for the script."""
    print("Khan Academy TSV Language and Curriculum Analysis")
    print("="*80)

    # Run the analysis
    results = analyze_all_languages()

    # Generate and display the report
    generate_report(results)


if __name__ == "__main__":
    main()
