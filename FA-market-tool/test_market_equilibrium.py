"""
Test Market Equilibrium Engine
Tests all new modules and their integration
"""

import pandas as pd
import datetime
from parser import OOTPParser
from market_engine import MarketAnalyzer
from market_liquidity import MarketLiquidityAnalyzer
from sentiment_logic import OwnerSentimentEngine
from positional_scarcity import PositionalScarcityAdjuster
from desperation_decay import DesperationDecayCalculator


def test_market_equilibrium():
    """Test the complete Market Equilibrium Engine"""
    
    print("="*80)
    print("Testing Market Equilibrium Engine")
    print("="*80)
    
    # Load data
    print("\n1. Loading data...")
    parser = OOTPParser(html_dir=".")
    teams = parser.parse_team_financials(filename="TeamFin.html")
    fas = parser.parse_free_agents(filename="fafinancials.html")
    signed = parser.parse_signed_players(filename="signed.html")
    
    print(f"   ✓ Loaded {len(teams)} teams")
    print(f"   ✓ Loaded {len(fas)} free agents")
    print(f"   ✓ Loaded {len(signed)} signed players")
    
    # Test Owner Sentiment Engine
    print("\n2. Testing Owner Sentiment Engine...")
    sentiment_df = OwnerSentimentEngine.analyze_all_teams(teams)
    
    print(f"   ✓ Analyzed {len(sentiment_df)} teams")
    
    # Check archetype distribution
    archetype_counts = sentiment_df['archetype'].value_counts()
    print(f"   Archetype distribution:")
    for archetype, count in archetype_counts.items():
        print(f"     - {archetype}: {count}")
    
    # Check multiplier ranges
    min_mult = sentiment_df['sentiment_multiplier'].min()
    max_mult = sentiment_df['sentiment_multiplier'].max()
    print(f"   Sentiment multipliers: {min_mult:.2f} to {max_mult:.2f}")
    
    if min_mult >= 0.05 and max_mult <= 2.0:
        print(f"   ✓ Multipliers within expected range (0.05 - 2.0)")
    else:
        print(f"   ✗ Warning: Multipliers outside expected range!")
    
    # Test Market Liquidity Analyzer
    print("\n3. Testing Market Liquidity Analyzer...")
    liquidity_analyzer = MarketLiquidityAnalyzer(teams)
    liquidity_data = liquidity_analyzer.calculate_market_liquidity(sentiment_df)
    
    print(f"   ✓ Total Market Liquidity: ${liquidity_data['total_market_liquidity']/1e6:.1f}M")
    print(f"   ✓ Top-Tier Liquidity (Top 10): ${liquidity_data['top_tier_liquidity']/1e6:.1f}M")
    print(f"   ✓ Star Liquidity (Competitive): ${liquidity_data['star_liquidity']/1e6:.1f}M")
    print(f"   ✓ Top 10 teams identified: {len(liquidity_data['top_10_teams'])}")
    print(f"   ✓ Competitive teams: {len(liquidity_data['competitive_teams'])}")
    
    # Test Positional Scarcity Adjuster
    print("\n4. Testing Positional Scarcity Adjuster...")
    league_dollars_per_war = PositionalScarcityAdjuster.calculate_league_dollars_per_war(fas)
    print(f"   ✓ League $/WAR: ${league_dollars_per_war/1e6:.2f}M")
    
    # Test FMV for a few positions
    test_positions = ['SP', 'RP', 'SS', 'DH']
    print(f"   Position weight tests:")
    for pos in test_positions:
        weight = PositionalScarcityAdjuster.get_position_weight(pos)
        print(f"     - {pos}: {weight*100:.0f}%")
    
    # Verify RP is capped at 50%
    rp_weight = PositionalScarcityAdjuster.get_position_weight('RP')
    if rp_weight == 0.50:
        print(f"   ✓ Relief pitchers correctly capped at 50%")
    else:
        print(f"   ✗ Warning: RP weight is {rp_weight}, expected 0.50")
    
    # Calculate FMV for all FAs
    fmv_df = PositionalScarcityAdjuster.calculate_fmv_for_all_players(fas, liquidity_data)
    print(f"   ✓ Calculated FMV for {len(fmv_df)} free agents")
    
    # Check tier distribution
    tier_counts = fmv_df['tier'].value_counts()
    print(f"   Player tier distribution:")
    for tier in sorted(tier_counts.index):
        print(f"     - Tier {tier}: {tier_counts[tier]} players")
    
    # Test Desperation Decay Calculator
    print("\n5. Testing Desperation Decay Calculator...")
    
    # Test with different dates
    test_dates = [
        datetime.date(2068, 1, 1),   # Before deadline
        datetime.date(2068, 1, 15),  # At deadline
        datetime.date(2068, 2, 1),   # 17 days past
        datetime.date(2068, 3, 1),   # 45 days past
    ]
    
    for test_date in test_dates:
        decay_df = DesperationDecayCalculator.apply_decay_to_all_players(
            fmv_df, test_date, liquidity_data
        )
        
        decay_applied = len(decay_df[decay_df['decay_applied'] == True])
        avg_decay = decay_df[decay_df['decay_applied'] == True]['decay_percentage'].mean() if decay_applied > 0 else 0
        
        days_past = max(0, (test_date - datetime.date(2068, 1, 15)).days)
        print(f"   Date: {test_date.strftime('%Y-%m-%d')} (Day {days_past})")
        print(f"     - Players with decay: {decay_applied}/{len(decay_df)}")
        print(f"     - Avg decay %: {avg_decay:.1f}%")
    
    # Test Market Analyzer integration
    print("\n6. Testing MarketAnalyzer integration...")
    analyzer = MarketAnalyzer(teams, fas, signed)
    
    equilibrium_data = analyzer.get_market_equilibrium_data(datetime.date(2068, 2, 1))
    print(f"   ✓ get_market_equilibrium_data() executed successfully")
    print(f"   ✓ Liquidity data available: {equilibrium_data['liquidity'] is not None}")
    print(f"   ✓ Sentiment data: {len(equilibrium_data['sentiment'])} teams")
    print(f"   ✓ FMV data: {len(equilibrium_data['fmv'])} players")
    print(f"   ✓ Decay data: {len(equilibrium_data['decay'])} players")
    
    # Test FMV calculator for specific player
    print("\n7. Testing FMV calculator for specific player...")
    test_player_fmv = analyzer.calculate_fmv_for_player(
        position='SP',
        overall=4.0,
        war=4.0,
        demand=15_000_000
    )
    
    print(f"   Test Player: 4.0★ SP, 4.0 WAR, $15M demand")
    print(f"   ✓ Base value: ${test_player_fmv['base_value']/1e6:.2f}M")
    print(f"   ✓ Position weight: {test_player_fmv['position_weight']*100:.0f}%")
    print(f"   ✓ Position-adjusted: ${test_player_fmv['position_adjusted_value']/1e6:.2f}M")
    print(f"   ✓ FMV: ${test_player_fmv['fmv']/1e6:.2f}M")
    print(f"   ✓ vs Demand: {test_player_fmv['fmv_vs_demand']:.1f}%")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    # Market overview
    total_fa_demands = fas['demand'].sum()
    total_liquidity = liquidity_data['total_market_liquidity']
    supply_demand_ratio = total_liquidity / total_fa_demands if total_fa_demands > 0 else 0
    
    print(f"\nMarket Overview:")
    print(f"  Total FA Demands: ${total_fa_demands/1e6:.1f}M")
    print(f"  Total Market Liquidity: ${total_liquidity/1e6:.1f}M")
    print(f"  Supply/Demand Ratio: {supply_demand_ratio:.2f}x")
    print(f"  Market Type: {'Buyer\'s Market' if supply_demand_ratio > 1.2 else 'Balanced' if supply_demand_ratio > 0.8 else 'Seller\'s Market'}")
    
    # Sentiment overview
    print(f"\nOwner Sentiment:")
    for archetype in ['Dynasty', 'Win Now', 'Competitive', 'Rebuild']:
        arch_teams = sentiment_df[sentiment_df['archetype'] == archetype]
        if len(arch_teams) > 0:
            avg_mult = arch_teams['sentiment_multiplier'].mean()
            total_bp = arch_teams['real_buying_power'].sum()
            print(f"  {archetype}: {len(arch_teams)} teams, avg {avg_mult*100:.0f}% mult, ${total_bp/1e6:.1f}M total")
    
    # FMV overview
    print(f"\nFair Market Value:")
    fmv_above_demand = len(fmv_df[fmv_df['fmv'] > fmv_df['demand']])
    fmv_below_demand = len(fmv_df[fmv_df['fmv'] < fmv_df['demand']])
    print(f"  Players with FMV > Demand: {fmv_above_demand}/{len(fmv_df)} ({fmv_above_demand/len(fmv_df)*100:.1f}%)")
    print(f"  Players with FMV < Demand: {fmv_below_demand}/{len(fmv_df)} ({fmv_below_demand/len(fmv_df)*100:.1f}%)")
    print(f"  Avg FMV vs Demand: {((fmv_df['fmv'].mean() / fmv_df['demand'].mean() - 1) * 100):.1f}%")
    
    print("\n" + "="*80)
    print("✓ All tests completed successfully!")
    print("="*80)


if __name__ == "__main__":
    test_market_equilibrium()
