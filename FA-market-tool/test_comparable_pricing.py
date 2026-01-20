"""
Test Comparable-Based Market Analyzer
Tests new methods for FA pricing guide
"""

import pandas as pd
import datetime
from parser import OOTPParser
from market_engine import MarketAnalyzer


def test_comparable_pricing():
    """Test the complete Comparable-Based Market Analyzer"""
    
    print("="*80)
    print("Testing Comparable-Based Market Analyzer")
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
    
    # Create analyzer
    analyzer = MarketAnalyzer(teams, fas, signed)
    
    # Test similarity score calculation
    print("\n2. Testing similarity score calculation...")
    
    # Test exact match
    score_exact = analyzer.calculate_similarity_score(4.0, 28, 4.0, 28)
    assert score_exact == 100.0, f"Expected 100.0, got {score_exact}"
    print(f"   ✓ Exact match: {score_exact}")
    
    # Test with differences
    score_diff = analyzer.calculate_similarity_score(4.0, 28, 3.5, 31)
    expected_diff = 100 - (0.5 * 20) - (3 * 2)  # 100 - 10 - 6 = 84
    assert score_diff == expected_diff, f"Expected {expected_diff}, got {score_diff}"
    print(f"   ✓ With differences (0.5 stars, 3 years): {score_diff}")
    
    # Test get_comparable_contracts
    print("\n3. Testing get_comparable_contracts...")
    
    # Test for a 4.0★ SP age 28
    comps = analyzer.get_comparable_contracts(4.0, 28, 'SP', overall_tolerance=0.5, age_tolerance=3)
    print(f"   ✓ Found {len(comps)} comparables for 4.0★ SP age 28")
    
    if len(comps) > 0:
        assert 'similarity_score' in comps.columns, "Missing similarity_score column"
        assert comps['similarity_score'].max() <= 100, "Similarity score exceeds 100"
        assert comps['similarity_score'].min() >= 0, "Similarity score below 0"
        print(f"   ✓ Similarity scores range: {comps['similarity_score'].min():.1f} - {comps['similarity_score'].max():.1f}")
        print(f"   ✓ Top comp: {comps.iloc[0]['name']} ({comps.iloc[0]['overall']:.1f}★, age {comps.iloc[0]['age']}) - Score: {comps.iloc[0]['similarity_score']:.1f}")
    
    # Test edge case: elite player (5.0★)
    print("\n4. Testing edge case: Elite 5.0★ player...")
    elite_fas = fas[fas['overall'] == 5.0]
    if len(elite_fas) > 0:
        elite_fa = elite_fas.iloc[0]
        elite_comps = analyzer.get_comparable_contracts(
            elite_fa['overall'], elite_fa['age'], elite_fa['position'],
            overall_tolerance=0.5, age_tolerance=3
        )
        print(f"   ✓ Elite player: {elite_fa['name']} ({elite_fa['position']}, age {elite_fa['age']})")
        print(f"   ✓ Found {len(elite_comps)} comparables")
    else:
        print("   ⚠ No 5.0★ FAs to test")
    
    # Test edge case: fringe player (1.5★ or lower)
    print("\n5. Testing edge case: Fringe player...")
    fringe_fas = fas[fas['overall'] <= 1.5]
    if len(fringe_fas) > 0:
        fringe_fa = fringe_fas.iloc[0]
        fringe_comps = analyzer.get_comparable_contracts(
            fringe_fa['overall'], fringe_fa['age'], fringe_fa['position'],
            overall_tolerance=0.5, age_tolerance=3
        )
        print(f"   ✓ Fringe player: {fringe_fa['name']} ({fringe_fa['position']}, age {fringe_fa['age']})")
        print(f"   ✓ Found {len(fringe_comps)} comparables")
    else:
        print("   ⚠ No fringe players to test")
    
    # Test calculate_market_fmv_for_all_fas
    print("\n6. Testing calculate_market_fmv_for_all_fas...")
    fmv_df = analyzer.calculate_market_fmv_for_all_fas()
    
    print(f"   ✓ Processed {len(fmv_df)} free agents")
    assert len(fmv_df) == len(fas), f"Expected {len(fas)} results, got {len(fmv_df)}"
    
    # Check required columns
    required_cols = ['name', 'position', 'overall', 'age', 'demand', 
                     'comparable_median', 'comparable_count', 'recommendation']
    for col in required_cols:
        assert col in fmv_df.columns, f"Missing required column: {col}"
    print(f"   ✓ All required columns present")
    
    # Check fallback logic worked
    no_comps = fmv_df[fmv_df['comparable_count'] == 0]
    some_comps = fmv_df[(fmv_df['comparable_count'] > 0) & (fmv_df['comparable_count'] < 5)]
    many_comps = fmv_df[fmv_df['comparable_count'] >= 5]
    
    print(f"   ✓ Players with 0 comparables: {len(no_comps)} ({len(no_comps)/len(fmv_df)*100:.1f}%)")
    print(f"   ✓ Players with 1-4 comparables: {len(some_comps)} ({len(some_comps)/len(fmv_df)*100:.1f}%)")
    print(f"   ✓ Players with 5+ comparables: {len(many_comps)} ({len(many_comps)/len(fmv_df)*100:.1f}%)")
    
    # Test recommendations
    fair_asks = fmv_df[fmv_df['recommendation'].str.contains('fair', case=False, na=False)]
    negotiate = fmv_df[fmv_df['recommendation'].str.contains('Negotiate', case=False, na=False)]
    insufficient = fmv_df[fmv_df['recommendation'].str.contains('Insufficient', case=False, na=False)]
    
    print(f"   ✓ Fair ask recommendations: {len(fair_asks)}")
    print(f"   ✓ Negotiate recommendations: {len(negotiate)}")
    print(f"   ✓ Insufficient data: {len(insufficient)}")
    
    # Test get_fa_detailed_analysis
    print("\n7. Testing get_fa_detailed_analysis...")
    
    # Test with first FA
    test_fa_name = fas.iloc[0]['name']
    analysis = analyzer.get_fa_detailed_analysis(test_fa_name, max_comparables=20)
    
    assert 'fa_details' in analysis, "Missing fa_details"
    assert 'comparables' in analysis, "Missing comparables"
    assert 'stats' in analysis, "Missing stats"
    assert 'recommendation' in analysis, "Missing recommendation"
    
    print(f"   ✓ Analyzed: {test_fa_name}")
    print(f"   ✓ Position: {analysis['fa_details']['position']}")
    print(f"   ✓ Overall: {analysis['fa_details']['overall']:.1f}★")
    print(f"   ✓ Age: {analysis['fa_details']['age']}")
    print(f"   ✓ Demand: ${analysis['fa_details']['demand']/1e6:.2f}M")
    print(f"   ✓ Comparables found: {analysis['stats']['count']}")
    
    if analysis['stats']['count'] > 0:
        print(f"   ✓ FMV (median): ${analysis['stats']['median']/1e6:.2f}M")
        print(f"   ✓ Recommended range: ${analysis['recommendation']['recommended_min']/1e6:.2f}M - ${analysis['recommendation']['recommended_max']/1e6:.2f}M")
        print(f"   ✓ Demand percentile: {analysis['recommendation']['demand_percentile']:.0f}th")
    
    # Test with non-existent player
    invalid_analysis = analyzer.get_fa_detailed_analysis("INVALID_PLAYER_XYZ")
    assert 'error' in invalid_analysis, "Should return error for invalid player"
    print(f"   ✓ Correctly handles invalid player name")
    
    # Sample output
    print("\n" + "="*80)
    print("SAMPLE RESULTS")
    print("="*80)
    
    # Show some high-demand FAs
    high_demand = fmv_df.nlargest(5, 'demand')[['name', 'position', 'overall', 'demand', 'comparable_median', 'comparable_count', 'recommendation']]
    print("\nTop 5 Free Agents by Demand:")
    for _, row in high_demand.iterrows():
        print(f"  {row['name']} ({row['position']}, {row['overall']:.1f}★)")
        print(f"    Demand: ${row['demand']/1e6:.2f}M | FMV: ${row['comparable_median']/1e6:.2f}M | Comps: {row['comparable_count']}")
        print(f"    Recommendation: {row['recommendation']}")
    
    # Show players with fair asks
    if len(fair_asks) > 0:
        fair_sample = fair_asks.head(3)[['name', 'position', 'overall', 'demand', 'comparable_median', 'difference_pct']]
        print("\nSample Fair Ask Players:")
        for _, row in fair_sample.iterrows():
            print(f"  {row['name']} ({row['position']}, {row['overall']:.1f}★): ${row['demand']/1e6:.2f}M (FMV: ${row['comparable_median']/1e6:.2f}M, {row['difference_pct']:+.1f}%)")
    
    print("\n" + "="*80)
    print("✓ All tests completed successfully!")
    print("="*80)


if __name__ == "__main__":
    test_comparable_pricing()
