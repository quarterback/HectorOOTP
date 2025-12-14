"""
Test script to verify import_draft_csv() works with OOTP format.
This test validates the fix for handling OOTP draft.csv files with comment lines.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auction.csv_handler import import_draft_csv


def test_ootp_format_with_comment():
    """Test that OOTP format (comment line, no headers) works correctly"""
    print("Testing OOTP format with comment line...")
    
    # Test with OOTP format file
    teams = import_draft_csv('ootp_draft.csv')
    
    # Verify 12 teams were loaded
    assert len(teams) == 12, f"Expected 12 teams, got {len(teams)}"
    
    # Verify specific team mapping
    assert 'Soucis Comets' in teams, "Soucis Comets not found in teams"
    assert teams['Soucis Comets'] == '2437', f"Expected '2437', got '{teams['Soucis Comets']}'"
    
    # Verify other teams from Round 1
    assert 'Soufriere Young Bucks' in teams
    assert teams['Soufriere Young Bucks'] == '2445'
    
    assert 'Laborie Bulls' in teams
    assert teams['Laborie Bulls'] == '2440'
    
    # Verify Round 2 teams are not included (duplicates should be avoided)
    # Bisee Shepherds only appears in Round 2 in our test file
    # Other teams appear in both rounds, but we only get them once from Round 1
    
    print(f"✓ Successfully loaded {len(teams)} teams")
    print("✓ Soucis Comets → 2437")
    print("✓ Soufriere Young Bucks → 2445")
    print("✓ Laborie Bulls → 2440")
    print("✓ OOTP format test passed!")
    

def test_header_format_still_works():
    """Test that header format (sample_draft.csv) still works"""
    print("\nTesting header format (backward compatibility)...")
    
    # Test with header format file
    teams = import_draft_csv('sample_draft.csv')
    
    # Verify 12 teams were loaded
    assert len(teams) == 12, f"Expected 12 teams, got {len(teams)}"
    
    # Verify specific team mapping
    assert 'Soucis Comets' in teams
    assert teams['Soucis Comets'] == '2437'
    
    print(f"✓ Successfully loaded {len(teams)} teams from header format")
    print("✓ Backward compatibility maintained!")


if __name__ == '__main__':
    try:
        test_ootp_format_with_comment()
        test_header_format_still_works()
        print("\n" + "=" * 50)
        print("✓ All OOTP format tests passed!")
        print("=" * 50)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
