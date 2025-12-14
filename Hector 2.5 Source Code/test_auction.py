"""
Simple test script for auction system modules.
Tests core functionality without GUI.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_budget_config():
    """Test budget configuration"""
    from auction.budget import BudgetConfig, BudgetManager
    
    print("Testing Budget Config...")
    
    # Create config
    teams = ['NYY', 'BOS', 'TB', 'TOR', 'BAL']
    config = BudgetConfig.default_config(teams, budget_per_team=100.0)
    
    assert len(config.team_budgets) == 5
    assert config.team_budgets['NYY'] == 100.0
    assert config.min_spend_percentage == 0.75
    
    # Test budget manager
    manager = BudgetManager(config)
    assert manager.get_remaining_budget('NYY') == 100.0
    
    # Record acquisition
    test_player = {'Name': 'Test Player', 'POS': 'SP'}
    manager.record_acquisition('NYY', test_player, 25.0)
    assert manager.get_remaining_budget('NYY') == 75.0
    assert manager.roster_sizes['NYY'] == 1
    
    # Test validation
    valid, error = manager.validate_bid('NYY', 30.0)
    assert valid, f"Validation failed: {error}"
    
    # Test invalid bid (too expensive)
    valid, error = manager.validate_bid('NYY', 80.0)
    assert not valid, "Should fail - not enough budget for required roster"
    
    print("✓ Budget Config tests passed")


def test_csv_handler():
    """Test CSV import/export"""
    from auction.csv_handler import import_free_agents_csv, validate_csv_format, create_sample_free_agents_csv
    import os
    
    print("Testing CSV Handler...")
    
    # Create sample CSV
    test_file = '/tmp/test_auction.csv'
    create_sample_free_agents_csv(test_file)
    assert os.path.exists(test_file)
    
    # Validate format
    valid, error, fields = validate_csv_format(test_file)
    assert valid, f"CSV validation failed: {error}"
    assert 'Name' in fields
    assert 'POS' in fields
    assert 'Age' in fields
    
    # Import players
    players = import_free_agents_csv(test_file)
    assert len(players) == 3
    assert players[0]['Name'] == 'John Smith'
    assert players[0]['POS'] == 'SP'
    
    # Cleanup
    os.remove(test_file)
    
    print("✓ CSV Handler tests passed")


def test_valuations():
    """Test player valuations"""
    from auction.valuations import calculate_player_valuation, parse_rating
    import pitcher_weights
    import batter_weights
    
    print("Testing Valuations...")
    
    # Use actual weights from the project
    pitcher_section_weights = pitcher_weights.section_weights
    batter_section_weights = batter_weights.section_weights
    
    # Test pitcher
    pitcher = {
        'Name': 'Ace Pitcher',
        'POS': 'SP',
        'Age': '27',
        'OVR': '70',
        'POT': '75',
        'STU': '70',
        'MOV': '65',
        'CON': '70'
    }
    
    valuation = calculate_player_valuation(pitcher, pitcher_section_weights, batter_section_weights, base_budget=100.0)
    
    assert 'suggested_price' in valuation
    assert 'max_price' in valuation
    assert valuation['suggested_price'] > 0
    assert valuation['max_price'] >= valuation['suggested_price']
    
    # Test batter
    batter = {
        'Name': 'Star Batter',
        'POS': 'SS',
        'Age': '25',
        'OVR': '75',
        'POT': '80',
        'CON': '70',
        'POW': '75',
        'EYE': '65'
    }
    
    valuation = calculate_player_valuation(batter, pitcher_section_weights, batter_section_weights, base_budget=100.0)
    
    assert valuation['suggested_price'] > 0
    assert valuation['position_multiplier'] == 1.12  # SS scarcity
    
    print("✓ Valuation tests passed")


def test_ai_bidding():
    """Test AI bidding logic"""
    from auction.bidding_ai import AIBidder, BiddingStrategy
    from auction.budget import BudgetConfig, BudgetManager
    
    print("Testing AI Bidding...")
    
    # Setup
    teams = ['NYY', 'BOS']
    config = BudgetConfig.default_config(teams, budget_per_team=100.0)
    manager = BudgetManager(config)
    
    # Mock valuations
    valuations = {
        'Test Player': {
            'suggested_price': 10.0,
            'base_score': 65.0
        }
    }
    
    # Create AI bidder
    bidder = AIBidder('NYY', BiddingStrategy.BALANCED, manager, valuations)
    
    # Test should_bid
    player = {'Name': 'Test Player', 'POS': 'SP', 'Age': '28'}
    should_bid = bidder.should_bid(player, 5.0)
    # Note: This might be False due to randomness, but the method should execute
    
    # Test calculate_max_bid
    max_bid = bidder.calculate_max_bid(player)
    assert max_bid > 0
    assert max_bid <= manager.get_remaining_budget('NYY')
    
    print("✓ AI Bidding tests passed")


def test_auction_engine():
    """Test auction engine"""
    from auction.engine import AuctionEngine, AuctionState, BidType
    from auction.bidding_ai import AIBidderPool
    from auction.budget import BudgetConfig, BudgetManager
    
    print("Testing Auction Engine...")
    
    # Setup
    teams = ['NYY', 'BOS']
    config = BudgetConfig.default_config(teams, budget_per_team=100.0)
    manager = BudgetManager(config)
    ai_pool = AIBidderPool()
    
    # Create engine
    engine = AuctionEngine(manager, ai_pool)
    assert engine.state == AuctionState.SETUP
    
    # Setup auction
    players = [
        {'Name': 'Player 1', 'POS': 'SP', 'Age': '28'},
        {'Name': 'Player 2', 'POS': 'C', 'Age': '26'}
    ]
    starting_prices = {'Player 1': 5.0, 'Player 2': 3.0}
    
    engine.initialize_auction(players, starting_prices)
    engine.start_auction()
    
    assert engine.state == AuctionState.IN_PROGRESS
    assert engine.current_player is not None
    assert engine.current_player['Name'] == 'Player 1'
    assert engine.current_price == 5.0
    
    # Place bid
    success, error = engine.place_bid('NYY', 6.0, BidType.HUMAN)
    assert success, f"Bid failed: {error}"
    assert engine.current_price == 6.0
    assert engine.current_high_bidder == 'NYY'
    
    # Sell player
    result = engine.sell_current_player()
    assert result is not None
    assert result.winning_team == 'NYY'
    assert result.final_price == 6.0
    
    # Check progress
    progress = engine.get_progress()
    assert progress['players_sold'] == 1
    assert progress['current_index'] == 1
    
    print("✓ Auction Engine tests passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Running Auction System Tests")
    print("=" * 50)
    
    try:
        test_budget_config()
        test_csv_handler()
        test_valuations()
        test_ai_bidding()
        test_auction_engine()
        
        print("=" * 50)
        print("✓ All tests passed!")
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
    success = run_all_tests()
    sys.exit(0 if success else 1)
