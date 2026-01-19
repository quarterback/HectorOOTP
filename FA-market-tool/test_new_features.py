"""
Test script for new FA Market Tool features
"""

from parser import OOTPParser
from market_engine import MarketAnalyzer

def test_new_methods():
    """Test all new methods added to MarketAnalyzer"""
    
    print("="*80)
    print("Testing FA Market Tool New Features")
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
    
    # Initialize analyzer
    analyzer = MarketAnalyzer(teams, fas, signed)
    print("   ✓ MarketAnalyzer initialized")
    
    # Test get_salary_bands
    print("\n2. Testing get_salary_bands()...")
    try:
        bands = analyzer.get_salary_bands(position='SP', source='both')
        print(f"   ✓ Retrieved {len(bands)} salary bands for SP")
        if len(bands) > 0:
            print(f"   Example: {bands.iloc[0]['tier']} - {bands.iloc[0]['source']} - Median: ${bands.iloc[0]['median']/1e6:.2f}M")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test get_position_tier_matrix
    print("\n3. Testing get_position_tier_matrix()...")
    try:
        matrix = analyzer.get_position_tier_matrix(metric='median', source='both')
        print(f"   ✓ Created matrix with {len(matrix)} positions and {len(matrix.columns)} tiers")
        print(f"   Positions: {', '.join(matrix.index[:5].tolist())}...")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test get_market_gap_analysis
    print("\n4. Testing get_market_gap_analysis()...")
    try:
        gap = analyzer.get_market_gap_analysis()
        print(f"   ✓ Retrieved {len(gap)} position/tier combinations")
        if len(gap) > 0:
            avg_gap = gap['gap_percentage'].mean()
            print(f"   Average FA premium: {avg_gap:.1f}%")
            top_gap = gap.nlargest(1, 'gap_percentage').iloc[0]
            print(f"   Highest gap: {top_gap['position']} {top_gap['tier']} at {top_gap['gap_percentage']:.1f}%")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test get_player_pricing
    print("\n5. Testing get_player_pricing()...")
    try:
        pricing = analyzer.get_player_pricing('SP', 4.0, 4.5)
        print(f"   ✓ Found {pricing['total_comps']} comparables for 4.0-4.5★ SP")
        print(f"   Median salary: ${pricing['median']/1e6:.2f}M")
        print(f"   Range: ${pricing['p25']/1e6:.2f}M - ${pricing['p75']/1e6:.2f}M")
        print(f"   Signed: {pricing['signed_comps']}, FA: {pricing['fa_comps']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test calculate_offer_percentile
    print("\n6. Testing calculate_offer_percentile()...")
    try:
        pricing = analyzer.get_player_pricing('SP', 4.0, 4.5)
        if pricing['total_comps'] > 0:
            test_offer = pricing['median']
            percentile = analyzer.calculate_offer_percentile(test_offer, pricing['comparables'])
            print(f"   ✓ Median offer (${test_offer/1e6:.2f}M) ranks at {percentile:.1f} percentile")
            
            # Test a high offer
            high_offer = pricing['p75']
            high_pct = analyzer.calculate_offer_percentile(high_offer, pricing['comparables'])
            print(f"   ✓ 75th percentile offer (${high_offer/1e6:.2f}M) ranks at {high_pct:.1f} percentile")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*80)
    print("All tests completed successfully!")
    print("="*80)

if __name__ == "__main__":
    test_new_methods()
