"""
Test suite for parser.py to verify team_id addition and proper parsing
"""

import sys
from pathlib import Path
from parser import OOTPParser

def test_parse_team_financials():
    """Test that parse_team_financials adds team_id and parses all teams"""
    parser = OOTPParser(html_dir=".")
    
    # Parse teams
    teams_df = parser.parse_team_financials(filename="TeamFin.html")
    
    # Verify team_id column exists
    assert 'team_id' in teams_df.columns, "team_id column should exist"
    
    # Verify team_ids are sequential starting from 0
    team_ids = teams_df['team_id'].tolist()
    expected_ids = list(range(len(teams_df)))
    assert team_ids == expected_ids, f"team_ids should be sequential from 0 to {len(teams_df)-1}"
    
    # Verify we have team data
    assert len(teams_df) > 0, "Should parse at least one team"
    
    # Verify all required columns exist
    required_columns = ['team_id', 'team_name', 'abbr', 'payroll', 'budget', 'available_for_fa']
    for col in required_columns:
        assert col in teams_df.columns, f"Column {col} should exist"
    
    # Verify no team_id is None or NaN
    assert teams_df['team_id'].notna().all(), "All team_ids should be valid"
    
    # Verify team_names are not empty
    assert (teams_df['team_name'] != '').all(), "All teams should have names"
    
    print(f"✅ Successfully parsed {len(teams_df)} teams")
    print(f"✅ team_id range: {teams_df['team_id'].min()} to {teams_df['team_id'].max()}")
    print(f"✅ All required columns present")
    print("\nFirst 5 teams:")
    print(teams_df[['team_id', 'team_name', 'abbr']].head())
    print("\nLast 5 teams:")
    print(teams_df[['team_id', 'team_name', 'abbr']].tail())
    
    return True

if __name__ == "__main__":
    try:
        test_parse_team_financials()
        print("\n✅ All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
