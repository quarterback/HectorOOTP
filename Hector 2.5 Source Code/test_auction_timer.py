"""
Test script for timer-based auction system and OVR-based bidding.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_timer_functionality():
    """Test timer functionality"""
    from auction.engine import AuctionEngine, AuctionState
    from auction.bidding_ai import AIBidderPool, BiddingStrategy
    from auction.budget import BudgetConfig, BudgetManager
    
    print("Testing Timer Functionality...")
    
    # Setup
    teams = ['NYY', 'BOS']
    config = BudgetConfig.default_config(teams, budget_per_team=100.0)
    manager = BudgetManager(config)
    ai_pool = AIBidderPool()
    
    # Create engine
    engine = AuctionEngine(manager, ai_pool)
    
    # Test timer enable/disable
    engine.enable_timer(60)
    assert engine.timer_enabled == True
    assert engine.timer_duration == 60
    
    # Test timer bounds
    engine.enable_timer(200)  # Too high, should default to 60
    assert engine.timer_duration == 60
    
    engine.enable_timer(45)  # Valid
    assert engine.timer_duration == 45
    
    # Setup and start auction
    players = [
        {'Name': 'Player 1', 'POS': 'SP', 'Age': '28', 'OVR': '70'},
        {'Name': 'Player 2', 'POS': 'C', 'Age': '26', 'OVR': '65'}
    ]
    starting_prices = {'Player 1': 5.0, 'Player 2': 3.0}
    
    engine.initialize_auction(players, starting_prices)
    engine.start_auction()
    
    # Check timer started
    assert engine.timer_active == True
    assert engine.get_timer_remaining() > 0
    
    # Test pause/resume
    initial_remaining = engine.get_timer_remaining()
    engine.pause_auction()
    assert engine.timer_active == False
    time.sleep(0.1)
    paused_remaining = engine.get_timer_remaining()
    assert abs(paused_remaining - initial_remaining) < 0.5  # Should be roughly the same
    
    engine.resume_auction()
    assert engine.timer_active == True
    
    # Test timer info
    timer_info = engine.get_timer_info()
    assert timer_info['enabled'] == True
    assert timer_info['duration'] == 45
    assert timer_info['remaining'] > 0
    
    print("✓ Timer Functionality tests passed")


def test_ovr_based_bidding():
    """Test OVR-based bidding thresholds"""
    from auction.bidding_ai import AIBidder, BiddingStrategy
    from auction.budget import BudgetConfig, BudgetManager
    from auction.valuations import calculate_player_valuation
    import pitcher_weights
    import batter_weights
    
    print("Testing OVR-Based Bidding...")
    
    # Setup
    teams = ['NYY']
    config = BudgetConfig.default_config(teams, budget_per_team=100.0)
    manager = BudgetManager(config)
    
    # Use actual weights
    pitcher_section_weights = pitcher_weights.section_weights
    batter_section_weights = batter_weights.section_weights
    
    # Test players with different OVRs
    low_ovr_player = {
        'Name': 'Low OVR Player',
        'POS': 'SP',
        'Age': '27',
        'OVR': '30',  # Very low OVR
        'POT': '35',
        'STU': '40',
        'MOV': '35',
        'CON': '40'
    }
    
    med_ovr_player = {
        'Name': 'Med OVR Player',
        'POS': 'SP',
        'Age': '27',
        'OVR': '55',
        'POT': '60',
        'STU': '60',
        'MOV': '55',
        'CON': '60'
    }
    
    high_ovr_player = {
        'Name': 'High OVR Player',
        'POS': 'SP',
        'Age': '27',
        'OVR': '75',
        'POT': '80',
        'STU': '75',
        'MOV': '70',
        'CON': '75'
    }
    
    # Calculate valuations
    low_val = calculate_player_valuation(low_ovr_player, pitcher_section_weights, batter_section_weights, 100.0)
    med_val = calculate_player_valuation(med_ovr_player, pitcher_section_weights, batter_section_weights, 100.0)
    high_val = calculate_player_valuation(high_ovr_player, pitcher_section_weights, batter_section_weights, 100.0)
    
    print(f"  Low OVR (30) valuation: ${low_val['suggested_price']:.2f}M")
    print(f"  Med OVR (55) valuation: ${med_val['suggested_price']:.2f}M")
    print(f"  High OVR (75) valuation: ${high_val['suggested_price']:.2f}M")
    
    # Low OVR players should have very low valuations
    assert low_val['suggested_price'] <= 2.0, f"Low OVR player valued too high: ${low_val['suggested_price']:.2f}M"
    
    # Higher OVR should have higher valuations
    assert med_val['suggested_price'] > low_val['suggested_price']
    assert high_val['suggested_price'] > med_val['suggested_price']
    
    # Test AI bidding thresholds
    valuations = {
        'Low OVR Player': low_val,
        'Med OVR Player': med_val,
        'High OVR Player': high_val
    }
    
    # Aggressive bidder (min OVR 55)
    aggressive = AIBidder('NYY', BiddingStrategy.AGGRESSIVE, manager, valuations)
    
    # Should NOT bid on low OVR (30)
    should_bid_low = aggressive.should_bid(low_ovr_player, 1.0)
    print(f"  Aggressive bidder on OVR 30: {should_bid_low}")
    assert should_bid_low == False, "Aggressive bidder should not bid on OVR 30 player"
    
    # Should bid on med OVR (55) if conditions met
    # Note: might be false due to randomness, but shouldn't crash
    should_bid_med = aggressive.should_bid(med_ovr_player, 5.0)
    print(f"  Aggressive bidder on OVR 55: {should_bid_med}")
    
    # Balanced bidder (min OVR 45)
    balanced = AIBidder('NYY', BiddingStrategy.BALANCED, manager, valuations)
    
    # Should NOT bid on low OVR (30)
    should_bid_low_balanced = balanced.should_bid(low_ovr_player, 1.0)
    print(f"  Balanced bidder on OVR 30: {should_bid_low_balanced}")
    assert should_bid_low_balanced == False, "Balanced bidder should not bid on OVR 30 player"
    
    # Conservative bidder (min OVR 40)
    conservative = AIBidder('NYY', BiddingStrategy.CONSERVATIVE, manager, valuations)
    
    # Should NOT bid on low OVR (30)
    should_bid_low_conservative = conservative.should_bid(low_ovr_player, 1.0)
    print(f"  Conservative bidder on OVR 30: {should_bid_low_conservative}")
    assert should_bid_low_conservative == False, "Conservative bidder should not bid on OVR 30 player"
    
    print("✓ OVR-Based Bidding tests passed")


def test_player_sorting():
    """Test that players are sorted by OVR"""
    print("Testing Player Sorting...")
    
    players = [
        {'Name': 'Player A', 'OVR': '50'},
        {'Name': 'Player B', 'OVR': '75'},
        {'Name': 'Player C', 'OVR': '30'},
        {'Name': 'Player D', 'OVR': '90'},
        {'Name': 'Player E', 'OVR': '60 Stars'},  # Test with "Stars" suffix
    ]
    
    # Sort function (same as in auction_tab.py)
    def get_ovr(player):
        ovr_str = str(player.get('OVR', '0')).strip()
        ovr_str = ovr_str.replace(' Stars', '').replace('Stars', '').strip()
        try:
            return float(ovr_str)
        except:
            return 0.0
    
    players.sort(key=get_ovr, reverse=True)
    
    # Check order: should be D(90), B(75), E(60), A(50), C(30)
    assert players[0]['Name'] == 'Player D'
    assert players[1]['Name'] == 'Player B'
    assert players[2]['Name'] == 'Player E'
    assert players[3]['Name'] == 'Player A'
    assert players[4]['Name'] == 'Player C'
    
    print("✓ Player Sorting tests passed")


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Running Timer and OVR Auction Tests")
    print("=" * 50)
    
    try:
        test_timer_functionality()
        test_ovr_based_bidding()
        test_player_sorting()
        
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
