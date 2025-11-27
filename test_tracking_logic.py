#!/usr/bin/env python
"""
Simple test to validate the metadata tracking logic works correctly.
This doesn't require full dependencies - just tests the tracking mechanism.
"""

class MockNode:
    """Mock node for testing"""
    def __init__(self, title, kind, source_id):
        self.title = title
        self.kind = kind
        self.source_id = source_id
        self.categories = []
        self.grade_levels = []

class MockTSVManager:
    """Mock TSVManager with just the tracking methods"""
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.metadata_tracking = {} if verbose else None

    def _track_metadata(self, node, stage, source_info=None):
        """
        Track metadata updates for debugging cross-contamination issues.
        Records the state of categories and grade_levels at each stage.
        """
        if self.metadata_tracking is None:
            return

        node_id = getattr(node, 'source_id', str(id(node)))

        if node_id not in self.metadata_tracking:
            self.metadata_tracking[node_id] = {
                'title': getattr(node, 'title', 'Unknown'),
                'kind': getattr(node, 'kind', 'Unknown'),
                'history': []
            }

        categories = list(getattr(node, 'categories', []))
        grade_levels = list(getattr(node, 'grade_levels', []))

        history_entry = {
            'stage': stage,
            'categories': categories,
            'grade_levels': grade_levels,
        }

        if source_info:
            history_entry['source'] = source_info

        self.metadata_tracking[node_id]['history'].append(history_entry)

    def print_tracking_report(self):
        """Print tracking report for testing"""
        if not self.metadata_tracking:
            print("No tracking data")
            return

        for node_id, data in self.metadata_tracking.items():
            print(f"\n{'='*60}")
            print(f"Node: {data['title']} ({data['kind']})")
            print(f"ID: {node_id}")
            print(f"{'='*60}")
            for i, history in enumerate(data['history'], 1):
                print(f"\n  Step {i}: {history['stage']}")
                if 'source' in history:
                    print(f"    Source: {history['source']}")
                print(f"    Categories: {history['categories']}")
                print(f"    Grade Levels: {history['grade_levels']}")

def test_metadata_tracking():
    """Test the metadata tracking"""
    print("Testing metadata tracking mechanism...")

    manager = MockTSVManager(verbose=True)

    # Simulate a video being created
    video = MockNode("Introduction to Algebra", "video", "intro-algebra-123")

    # Step 1: Initial metadata from METADATA_BY_SLUG
    video.categories = ['Algebra']
    video.grade_levels = ['Upper Primary']
    manager._track_metadata(video, 'initial', 'METADATA_BY_SLUG[intro-algebra]')

    # Step 2: After ancestor inheritance (simulating contamination)
    video.categories = ['Mathematics', 'Algebra']
    video.grade_levels = ['Upper Primary']
    manager._track_metadata(video, 'after_ancestors', 'parent: Algebra Basics')

    # Step 3: Before sibling sharing
    manager._track_metadata(video, 'before_sibling_sharing', 'topic: Algebra Basics')

    # Step 4: After sibling sharing (THIS IS WHERE CONTAMINATION HAPPENS)
    video.categories = ['Mathematics', 'Algebra', 'Visual Art', 'Arts']  # Contaminated!
    video.grade_levels = ['Upper Primary', 'Lower Secondary', 'Tertiary']
    manager._track_metadata(video, 'after_sibling_sharing', 'topic: Algebra Basics, 10 siblings')

    # Print the report
    manager.print_tracking_report()

    # Verify tracking captured all stages
    tracking = manager.metadata_tracking['intro-algebra-123']
    assert len(tracking['history']) == 4, f"Expected 4 history entries, got {len(tracking['history'])}"

    # Check that contamination is visible
    final_cats = tracking['history'][-1]['categories']
    assert 'Visual Art' in final_cats, "Contamination not captured in final categories"

    print("\n" + "="*60)
    print("✓ Metadata tracking test PASSED!")
    print("="*60)
    print("\nThe tracking mechanism successfully captures:")
    print("  1. Initial metadata from METADATA_BY_SLUG")
    print("  2. Changes after ancestor inheritance")
    print("  3. State before sibling sharing")
    print("  4. Contamination after sibling sharing")
    print("\nThis will work in the actual chef to identify contamination sources!")

if __name__ == "__main__":
    test_metadata_tracking()
