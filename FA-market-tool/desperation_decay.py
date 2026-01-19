"""
Desperation Decay Calculator
Forces players to lower demands as the offseason progresses (the "Boras Correction")
"""

import datetime
from typing import Dict, List
import pandas as pd


class DesperationDecayCalculator:
    """Calculate demand decay for unsigned free agents"""
    
    # Decay parameters
    DECAY_START_MONTH = 1  # January
    DECAY_START_DAY = 15
    DECAY_RATE = 0.02  # 2% per day
    MAX_DECAY = 0.50   # Cap at 50% reduction
    
    @staticmethod
    def calculate_desperation_decay(player: Dict, current_date: datetime.date, 
                                   market_liquidity: Dict) -> Dict:
        """Apply decay to player demands if unsigned after January 15
        
        Args:
            player: Player data including demand, overall, position, name
            current_date: Current date in the simulation
            market_liquidity: Market liquidity analysis with top teams data
        
        Returns:
            Dictionary with:
            - original_demand: Player's original demand
            - decay_applied: Whether decay was applied
            - days_past_deadline: Days after Jan 15
            - decay_percentage: Percentage reduction
            - adjusted_demand: New demand after decay
            - reason: Explanation for decay decision
        """
        # Use current year from the date
        decay_start_date = datetime.date(current_date.year, 
                                        DesperationDecayCalculator.DECAY_START_MONTH, 
                                        DesperationDecayCalculator.DECAY_START_DAY)
        
        original_demand = player.get('demand', 0)
        
        # Check if past decay date
        if current_date <= decay_start_date:
            return {
                'original_demand': original_demand,
                'decay_applied': False,
                'days_past_deadline': 0,
                'decay_percentage': 0.0,
                'adjusted_demand': original_demand,
                'reason': f'Before {decay_start_date.strftime("%B %d")} deadline'
            }
        
        days_past = (current_date - decay_start_date).days
        
        # Get top 3 teams average buying power
        if 'top_10_teams' in market_liquidity and len(market_liquidity['top_10_teams']) >= 3:
            top_3_teams = market_liquidity['top_10_teams'][:3]
            bp_col = market_liquidity.get('liquidity_column', 'available_for_fa')
            
            avg_top_3_liquidity = sum([team.get(bp_col, 0) for team in top_3_teams]) / 3
        else:
            # Fallback if market data not available
            avg_top_3_liquidity = original_demand * 1.5
        
        # Check if demand exceeds market capacity
        if original_demand > avg_top_3_liquidity:
            # Apply decay
            total_decay = min(DesperationDecayCalculator.MAX_DECAY, 
                            days_past * DesperationDecayCalculator.DECAY_RATE)
            adjusted_demand = original_demand * (1 - total_decay)
            
            return {
                'original_demand': original_demand,
                'decay_applied': True,
                'days_past_deadline': days_past,
                'decay_percentage': total_decay * 100,
                'adjusted_demand': adjusted_demand,
                'reason': f'Demand ${original_demand/1e6:.1f}M exceeds top 3 teams avg ${avg_top_3_liquidity/1e6:.1f}M'
            }
        else:
            return {
                'original_demand': original_demand,
                'decay_applied': False,
                'days_past_deadline': days_past,
                'decay_percentage': 0.0,
                'adjusted_demand': original_demand,
                'reason': 'Demand within market range'
            }
    
    @staticmethod
    def apply_decay_to_all_players(players_df: pd.DataFrame, current_date: datetime.date,
                                   market_liquidity: Dict) -> pd.DataFrame:
        """Apply desperation decay to all free agents
        
        Args:
            players_df: DataFrame with free agent data
            current_date: Current simulation date
            market_liquidity: Market liquidity analysis
        
        Returns:
            DataFrame with decay calculations added
        """
        results = []
        
        for _, player in players_df.iterrows():
            player_dict = player.to_dict()
            decay_result = DesperationDecayCalculator.calculate_desperation_decay(
                player_dict, current_date, market_liquidity
            )
            
            # Merge with original player data
            result = {**player_dict, **decay_result}
            results.append(result)
        
        return pd.DataFrame(results)
    
    @staticmethod
    def get_recommended_action(decay_data: Dict, fmv: float = None) -> str:
        """Get recommended action based on decay and FMV
        
        Args:
            decay_data: Decay calculation result
            fmv: Optional Fair Market Value for comparison
        
        Returns:
            Recommended action string with emoji
        """
        adjusted_demand = decay_data['adjusted_demand']
        
        if fmv is not None:
            # Compare adjusted demand to FMV
            if adjusted_demand <= fmv * 1.05:  # Within 5% of FMV
                return "✅ Fair - Sign at adjusted demand"
            elif adjusted_demand <= fmv * 1.15:  # Within 15% of FMV
                return "⚠️ Slightly High - Negotiate down"
            else:
                return "🔥 Still High - Wait or force sign"
        else:
            # Without FMV, just use decay status
            if decay_data['decay_applied']:
                if decay_data['decay_percentage'] >= 40:
                    return "✅ Good Value - Consider signing"
                elif decay_data['decay_percentage'] >= 20:
                    return "⚠️ Better Value - Monitor"
                else:
                    return "🔥 Still High - Keep waiting"
            else:
                return "⏳ No Decay Yet"
    
    @staticmethod
    def simulate_future_decay(player: Dict, market_liquidity: Dict, 
                            start_date: datetime.date, days_to_simulate: int = 60) -> List[Dict]:
        """Simulate future decay trajectory for a player
        
        Args:
            player: Player data
            market_liquidity: Market liquidity analysis
            start_date: Starting date for simulation
            days_to_simulate: Number of days to simulate forward
        
        Returns:
            List of dictionaries with daily decay projections
        """
        projections = []
        
        for day_offset in range(0, days_to_simulate + 1, 7):  # Weekly snapshots
            simulation_date = start_date + datetime.timedelta(days=day_offset)
            decay_result = DesperationDecayCalculator.calculate_desperation_decay(
                player, simulation_date, market_liquidity
            )
            
            projections.append({
                'date': simulation_date,
                'days_past_deadline': decay_result['days_past_deadline'],
                'decay_percentage': decay_result['decay_percentage'],
                'adjusted_demand': decay_result['adjusted_demand'],
                'decay_applied': decay_result['decay_applied']
            })
        
        return projections
