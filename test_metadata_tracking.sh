#!/bin/bash
# Test script to run the chef with verbose mode to track metadata contamination

# Run the chef with verbose flag for a small subset
# This will create a metadata_contamination_report.txt file if any resources
# have VISUAL_ART or ARTS categories

echo "Running Khan Academy chef with metadata tracking enabled..."
echo "This will generate a metadata_contamination_report.txt file if contamination is found."
echo ""

# Run with verbose flag - adjust lang and variant as needed
python sushichef.py --lang=en --verbose

echo ""
echo "Check metadata_contamination_report.txt for details on any contaminated resources"
