"""
Test script for draft CSV import/export functionality.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from auction.csv_handler import (
    import_draft_csv, 
    import_free_agents_csv,
    export_auction_results_csv,
    validate_draft_csv_format
)
from auction.engine import AuctionEngine, AuctionState, BidType, AuctionResult
from auction.budget import BudgetConfig, BudgetManager
from auction.bidding_ai import AIBidderPool

def test_draft_csv_import():
    """Test importing draft CSV for team IDs"""
    print("Testing Draft CSV Import...")
    
    # Use sample draft CSV
    draft_csv_path = "sample_draft.csv"
    
    if not os.path.exists(draft_csv_path):
        print(f"⚠ Warning: {draft_csv_path} not found, skipping test")
        return
    
    # Validate format
    valid, error, fields = validate_draft_csv_format(draft_csv_path)
    assert valid, f"Draft CSV validation failed: {error}"
    assert 'Team Name' in fields
    assert 'Team ID' in fields
    
    # Import team ID mapping
    team_id_map = import_draft_csv(draft_csv_path)
    assert len(team_id_map) > 0, "No teams loaded from draft CSV"
    assert 'Soucis Comets' in team_id_map
    assert team_id_map['Soucis Comets'] == '2437'
    
    print(f"✓ Loaded {len(team_id_map)} teams from draft CSV")
    print("✓ Draft CSV Import tests passed")


def test_draft_export_format():
    """Test exporting auction results in draft format"""
    print("Testing Draft Export Format...")
    
    # Create mock auction results with new fields
    mock_results = [
        {
            'player': {'Player ID': '378837', 'Name': 'Josh Hazlewood', 'POS': 'SP', 'Age': '28'},
            'team_name': 'Castries Capitals',
            'team_id': '2434',
            'player_id': '378837',
            'price': 12.5,
            'order': 1
        },
        {
            'player': {'Player ID': '340322', 'Name': 'Mike Johnson', 'POS': 'C', 'Age': '25'},
            'team_name': 'Vieux Fort Sharks',
            'team_id': '2436',
            'player_id': '340322',
            'price': 8.0,
            'order': 2
        },
        {
            'player': {'Player ID': '382754', 'Name': 'Tom Williams', 'POS': 'SS', 'Age': '30'},
            'team_name': 'Castries Capitals',
            'team_id': '2434',
            'player_id': '382754',
            'price': 15.0,
            'order': 3
        }
    ]
    
    # Export to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_file = f.name
    
    try:
        export_auction_results_csv(mock_results, temp_file, format_type='ootp')
        
        # Read back and verify
        with open(temp_file, 'r') as f:
            lines = f.readlines()
            
        # Check header
        assert 'Round,Supplemental,Pick,Team Name,Team ID,Player ID' in lines[0]
        
        # Check first result
        assert '2434' in lines[1]  # Team ID
        assert '378837' in lines[1]  # Player ID
        assert 'Castries Capitals' in lines[1]  # Team Name
        
        # Check order is preserved
        assert lines[1].startswith('1,0,1,')  # First sale
        assert lines[2].startswith('1,0,2,')  # Second sale
        assert lines[3].startswith('1,0,3,')  # Third sale
        
        print("✓ Draft format export verified")
        print("✓ Round/Pick numbers assigned chronologically")
        print("✓ Team IDs and Player IDs included")
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    print("✓ Draft Export Format tests passed")


def test_auction_engine_with_team_ids():
    """Test auction engine tracks team IDs properly"""
    print("Testing Auction Engine with Team IDs...")
    
    # Setup team ID mapping
    team_id_map = {
        'NYY': '1001',
        'BOS': '1002'
    }
    
    # Create config and managers
    teams = list(team_id_map.keys())
    config = BudgetConfig.default_config(teams, budget_per_team=100.0)
    manager = BudgetManager(config)
    ai_pool = AIBidderPool()
    
    # Create engine with team_id_map
    engine = AuctionEngine(manager, ai_pool, team_id_map)
    
    # Setup auction
    players = [
        {'Player ID': '12345', 'Name': 'Test Player 1', 'POS': 'SP', 'Age': '28'},
        {'Player ID': '67890', 'Name': 'Test Player 2', 'POS': 'C', 'Age': '26'}
    ]
    starting_prices = {'Test Player 1': 5.0, 'Test Player 2': 3.0}
    
    engine.initialize_auction(players, starting_prices)
    engine.start_auction()
    
    # Place bid and sell
    success, error = engine.place_bid('NYY', 6.0, BidType.HUMAN)
    assert success, f"Bid failed: {error}"
    
    result = engine.sell_current_player()
    assert result is not None
    assert result.winning_team == 'NYY'
    assert result.team_id == '1001'
    assert result.player_id == '12345'
    assert result.order == 1
    
    # Sell second player
    success, error = engine.place_bid('BOS', 4.0, BidType.HUMAN)
    assert success, f"Bid failed: {error}"
    
    result2 = engine.sell_current_player()
    assert result2 is not None
    assert result2.team_id == '1002'
    assert result2.player_id == '67890'
    assert result2.order == 2
    
    print("✓ Team IDs tracked correctly in auction results")
    print("✓ Player IDs extracted from player data")
    print("✓ Order numbers assigned sequentially")
    print("✓ Auction Engine with Team IDs tests passed")


def run_all_draft_tests():
    """Run all draft-related tests"""
    print("=" * 50)
    print("Running Draft CSV Tests")
    print("=" * 50)
    
    try:
        test_draft_csv_import()
        test_draft_export_format()
        test_auction_engine_with_team_ids()
        
        print("=" * 50)
        print("✓ All draft CSV tests passed!")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_draft_tests()
    sys.exit(0 if success else 1)
