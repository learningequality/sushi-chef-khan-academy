#!/usr/bin/env python
"""
Test to demonstrate how multiple instances with the same source_id
get tracked together in the metadata tracking system.
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

        # Include object id to distinguish between separate instances
        instance_id = id(node)

        history_entry = {
            'stage': stage,
            'categories': categories,
            'grade_levels': grade_levels,
            'instance_id': instance_id,
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
            print(f"\n{'='*80}")
            print(f"Node: {data['title']} ({data['kind']})")
            print(f"Source ID: {node_id}")
            print(f"{'='*80}")
            for i, history in enumerate(data['history'], 1):
                print(f"\n  Step {i}: {history['stage']}")
                print(f"    Instance ID: {history['instance_id']}")
                if 'source' in history:
                    print(f"    Source: {history['source']}")
                print(f"    Categories: {history['categories']}")
                print(f"    Grade Levels: {history['grade_levels']}")

def test_multiple_instances():
    """Test tracking multiple instances with the same source_id"""
    print("Testing multiple instances with same source_id...\n")

    manager = MockTSVManager(verbose=True)

    # Simulate the SAME video being created 3 times in different topics
    # In the real chef, this happens when a video appears under multiple parent topics

    print("Creating Instance 1 (appears in 'Algebra Basics' topic)...")
    instance1 = MockNode("Introduction to Algebra", "video", "intro-algebra-123")
    instance1.categories = ['Algebra']
    instance1.grade_levels = ['Upper Primary']
    manager._track_metadata(instance1, 'initial', 'METADATA_BY_SLUG[intro-algebra]')
    manager._track_metadata(instance1, 'after_ancestors', 'parent: Algebra Basics')
    manager._track_metadata(instance1, 'before_sibling_sharing', 'topic: Algebra Basics')
    instance1.categories = ['Mathematics', 'Algebra']  # After sibling sharing
    manager._track_metadata(instance1, 'after_sibling_sharing', 'topic: Algebra Basics, 5 siblings')

    print("Creating Instance 2 (appears in 'Math Foundations' topic)...")
    instance2 = MockNode("Introduction to Algebra", "video", "intro-algebra-123")  # SAME source_id!
    instance2.categories = ['Algebra']
    instance2.grade_levels = ['Upper Primary']
    manager._track_metadata(instance2, 'initial', 'METADATA_BY_SLUG[intro-algebra]')
    manager._track_metadata(instance2, 'after_ancestors', 'parent: Math Foundations')
    manager._track_metadata(instance2, 'before_sibling_sharing', 'topic: Math Foundations')
    instance2.categories = ['Mathematics', 'Algebra', 'Basic Skills']  # After sibling sharing
    instance2.grade_levels = ['Upper Primary', 'Lower Secondary']
    manager._track_metadata(instance2, 'after_sibling_sharing', 'topic: Math Foundations, 8 siblings')

    print("Creating Instance 3 (appears in 'Problèmes' topic with CONTAMINATION)...")
    instance3 = MockNode("Introduction to Algebra", "video", "intro-algebra-123")  # SAME source_id!
    instance3.categories = ['Algebra']
    instance3.grade_levels = ['Upper Primary']
    manager._track_metadata(instance3, 'initial', 'METADATA_BY_SLUG[intro-algebra]')
    manager._track_metadata(instance3, 'after_ancestors', 'parent: Problèmes')
    manager._track_metadata(instance3, 'before_sibling_sharing', 'topic: Problèmes')
    # This topic has a sibling with visual arts, so after sharing it gets contaminated
    instance3.categories = ['Mathematics', 'Algebra', 'Visual Art', 'Arts']  # CONTAMINATED!
    instance3.grade_levels = ['Upper Primary', 'Lower Secondary', 'Tertiary']
    manager._track_metadata(instance3, 'after_sibling_sharing', 'topic: Problèmes, 12 siblings')

    # Print the report
    manager.print_tracking_report()

    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    print(f"\nInstance 1 object ID: {id(instance1)}")
    print(f"Instance 2 object ID: {id(instance2)}")
    print(f"Instance 3 object ID: {id(instance3)}")
    print("\nAll three instances have:")
    print(f"  - Same source_id: 'intro-algebra-123'")
    print(f"  - Different Python object IDs (they are SEPARATE objects)")
    print(f"\nThe tracking report shows ALL 12 steps (3 instances × 4 steps each)")
    print(f"under the SAME source_id, making it look like one object going through")
    print(f"12 transformations when it's actually 3 separate objects.")
    print("\nInstance 3 gets contaminated in the 'Problèmes' topic because")
    print("_share_sibling_metadata() spreads visual arts from one of its 12 siblings.")
    print("\nBUT: This contamination only affects Instance 3, not Instances 1 or 2,")
    print("because they are SEPARATE objects in the tree!")
    print("="*80)

if __name__ == "__main__":
    test_multiple_instances()
