"""
Positional Scarcity Adjuster
Enforces positional value caps to prevent relievers asking for starter money
"""

import pandas as pd
from typing import Dict, List


class PositionalScarcityAdjuster:
    """Calculate Fair Market Value (FMV) with positional adjustments"""
    
    # Position weights - premium positions get full value, low-value positions get discounted
    POSITION_WEIGHTS = {
        'SP': 1.00,   # Premium positions
        'SS': 1.00,
        'CF': 1.00,
        'C': 0.95,    # Slightly less
        '3B': 0.90,
        '2B': 0.90,
        'LF': 0.85,   # Corner outfield
        'RF': 0.85,
        '1B': 0.80,   # Low-value positions
        'DH': 0.75,
        'RP': 0.50,   # Relievers capped at 50% of starter value
        'CL': 0.60,   # Closers slightly higher than RP
        'MR': 0.50,   # Middle reliever
        'SU': 0.55,   # Setup man
    }
    
    @staticmethod
    def calculate_league_dollars_per_war(free_agents_df: pd.DataFrame) -> float:
        """Calculate league-wide $/WAR based on FA demands
        
        Args:
            free_agents_df: DataFrame with 'demand' and 'war' columns
        
        Returns:
            League dollars per WAR (float)
        """
        # Filter to players with positive WAR
        valid_players = free_agents_df[
            (free_agents_df['war'] > 0) & (free_agents_df['demand'] > 0)
        ].copy()
        
        if len(valid_players) == 0:
            return 5_000_000  # Default fallback
        
        total_demands = valid_players['demand'].sum()
        total_war = valid_players['war'].sum()
        
        if total_war == 0:
            return 5_000_000  # Default fallback
        
        return total_demands / total_war
    
    @staticmethod
    def get_position_weight(position: str) -> float:
        """Get position weight, with fallback for unknown positions
        
        Args:
            position: Position code (e.g., 'SP', 'SS', 'RP')
        
        Returns:
            Position weight (0.50 to 1.00)
        """
        # Handle multi-position players (e.g., "2B/SS")
        if '/' in position:
            positions = position.split('/')
            # Use the higher weight
            weights = [PositionalScarcityAdjuster.POSITION_WEIGHTS.get(pos.strip(), 0.85) 
                      for pos in positions]
            return max(weights)
        
        return PositionalScarcityAdjuster.POSITION_WEIGHTS.get(position, 0.85)
    
    @staticmethod
    def calculate_fmv(player: Dict, league_dollars_per_war: float, 
                     market_liquidity: Dict = None) -> Dict:
        """Calculate Fair Market Value for a player
        
        Args:
            player: Dictionary with 'war', 'position', 'overall', 'demand' keys
            league_dollars_per_war: League $/WAR ratio
            market_liquidity: Optional market liquidity data with top teams' buying power
        
        Returns:
            Dictionary with FMV calculation breakdown:
            - base_value: WAR × $/WAR
            - position_weight: Positional adjustment factor
            - position_adjusted_value: Base × position weight
            - market_cap: Cap based on tier (if applicable)
            - fmv: Final Fair Market Value
            - tier: Player tier (1, 2, or 3)
            - original_demand: Player's OOTP demand
            - fmv_vs_demand: Percentage difference
        """
        war = player.get('war', 0)
        position = player.get('position', 'DH')
        overall = player.get('overall', 2.5)
        demand = player.get('demand', 0)
        
        # Calculate base value
        base_value = war * league_dollars_per_war
        
        # Get position weight
        position_weight = PositionalScarcityAdjuster.get_position_weight(position)
        
        # Calculate position-adjusted value
        position_adjusted_value = base_value * position_weight
        
        # Determine tier
        if overall >= 5.0:
            tier = 1
        elif overall >= 4.0:
            tier = 2
        else:
            tier = 3
        
        # Apply market cap based on tier
        market_cap = None
        fmv = position_adjusted_value
        
        if market_liquidity and 'top_10_teams' in market_liquidity:
            top_teams = market_liquidity['top_10_teams']
            
            # Determine buying power column
            bp_col = market_liquidity.get('liquidity_column', 'available_for_fa')
            
            if tier == 1:
                # Tier 1: Top 5 teams average
                top_5_bp = [team.get(bp_col, 0) for team in top_teams[:5]]
                if top_5_bp:
                    market_cap = sum(top_5_bp) / len(top_5_bp)
                    fmv = min(position_adjusted_value, market_cap)
            
            elif tier == 2:
                # Tier 2: Top 15 teams average (use top 10 as proxy if we don't have 15)
                top_15_bp = [team.get(bp_col, 0) for team in top_teams]
                if top_15_bp:
                    market_cap = sum(top_15_bp) / len(top_15_bp)
                    fmv = min(position_adjusted_value, market_cap)
        
        # Calculate difference from OOTP demand
        if demand > 0:
            fmv_vs_demand = ((fmv - demand) / demand) * 100
        else:
            fmv_vs_demand = 0
        
        return {
            'base_value': base_value,
            'position_weight': position_weight,
            'position_adjusted_value': position_adjusted_value,
            'market_cap': market_cap,
            'fmv': fmv,
            'tier': tier,
            'original_demand': demand,
            'fmv_vs_demand': fmv_vs_demand
        }
    
    @staticmethod
    def calculate_fmv_for_all_players(players_df: pd.DataFrame, 
                                     market_liquidity: Dict = None) -> pd.DataFrame:
        """Calculate FMV for all free agents
        
        Args:
            players_df: DataFrame with free agent data
            market_liquidity: Optional market liquidity data
        
        Returns:
            DataFrame with FMV calculations added
        """
        # Calculate league $/WAR
        league_dollars_per_war = PositionalScarcityAdjuster.calculate_league_dollars_per_war(
            players_df
        )
        
        results = []
        
        for _, player in players_df.iterrows():
            player_dict = player.to_dict()
            fmv_result = PositionalScarcityAdjuster.calculate_fmv(
                player_dict, league_dollars_per_war, market_liquidity
            )
            
            # Merge with original player data
            result = {**player_dict, **fmv_result, 'league_dollars_per_war': league_dollars_per_war}
            results.append(result)
        
        return pd.DataFrame(results)
