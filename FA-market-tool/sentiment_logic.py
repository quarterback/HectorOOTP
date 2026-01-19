"""
Owner Sentiment Engine
Apply realistic multipliers to team budgets based on owner behavior and team state
"""

import pandas as pd
from typing import Dict


class OwnerSentimentEngine:
    """Calculate owner sentiment and real buying power"""
    
    # Sentiment multiplier ranges by archetype
    ARCHETYPE_RANGES = {
        'Rebuild': (0.10, 0.25),
        'Competitive': (0.26, 0.55),
        'Win Now': (0.56, 0.95),
        'Dynasty': (1.00, 2.00)
    }
    
    # Special case multiplier
    OVER_BUDGET_MULTIPLIER = 0.05
    
    @staticmethod
    def determine_archetype(team_data: Dict) -> str:
        """Determine team archetype based on win%, mode, and fan interest
        
        Args:
            team_data: Dictionary with 'win_pct', 'mode', 'fan_interest', 'budget_space'
        
        Returns:
            Archetype string: 'Rebuild', 'Competitive', 'Win Now', or 'Dynasty'
        """
        win_pct = team_data.get('win_pct', 0.500)
        mode = team_data.get('mode', 'Neutral').lower()
        fan_interest = team_data.get('fan_interest', 50)
        budget_space = team_data.get('budget_space', 0)
        
        # Special case: Over budget teams are in desperation mode
        if budget_space < 0:
            return 'Rebuild'
        
        # Dynasty: High win%, Dynasty mode, high fan interest
        if win_pct > 0.580 and 'dynasty' in mode and fan_interest > 80:
            return 'Dynasty'
        
        # Win Now: Good win% and Win Now mode, or recent success
        if win_pct > 0.506 and ('win now' in mode or win_pct > 0.580):
            return 'Win Now'
        
        # Rebuild: Poor win% or Rebuilding mode
        if win_pct < 0.432 or 'rebuild' in mode:
            return 'Rebuild'
        
        # Default: Competitive
        return 'Competitive'
    
    @staticmethod
    def calculate_sentiment_multiplier(archetype: str, team_data: Dict) -> float:
        """Calculate sentiment multiplier based on archetype and team specifics
        
        Args:
            archetype: Team archetype ('Rebuild', 'Competitive', 'Win Now', 'Dynasty')
            team_data: Dictionary with team data including 'budget_space', 'win_pct', 
                      'fan_interest'
        
        Returns:
            Sentiment multiplier (0.05 to 2.0)
        """
        budget_space = team_data.get('budget_space', 0)
        win_pct = team_data.get('win_pct', 0.500)
        fan_interest = team_data.get('fan_interest', 50)
        
        # Special case: Over budget
        if budget_space < 0:
            return OwnerSentimentEngine.OVER_BUDGET_MULTIPLIER
        
        # Get base range for archetype
        min_mult, max_mult = OwnerSentimentEngine.ARCHETYPE_RANGES[archetype]
        
        # Calculate position within range based on performance and interest
        if archetype == 'Rebuild':
            # Lower rebuilds spend less
            if win_pct < 0.400:
                multiplier = min_mult
            else:
                # Interpolate between min and max
                range_pct = (win_pct - 0.350) / (0.432 - 0.350)
                multiplier = min_mult + (max_mult - min_mult) * min(1.0, max(0.0, range_pct))
        
        elif archetype == 'Competitive':
            # Middle teams vary by mode and interest
            range_pct = (win_pct - 0.432) / (0.580 - 0.432)
            multiplier = min_mult + (max_mult - min_mult) * min(1.0, max(0.0, range_pct))
        
        elif archetype == 'Win Now':
            # Win Now teams vary by how close to playoffs
            range_pct = (win_pct - 0.506) / (0.617 - 0.506)
            multiplier = min_mult + (max_mult - min_mult) * min(1.0, max(0.0, range_pct))
        
        else:  # Dynasty
            # Dynasty teams can spend big, especially with high fan interest
            base_mult = (min_mult + max_mult) / 2
            
            # Boost for high fan interest
            if fan_interest > 90:
                interest_boost = 0.4
            elif fan_interest > 85:
                interest_boost = 0.2
            else:
                interest_boost = 0.0
            
            multiplier = min(max_mult, base_mult + interest_boost)
        
        return multiplier
    
    @staticmethod
    def calculate_real_buying_power(team_data: Dict, market_context: Dict = None) -> Dict:
        """Calculate how much a team will ACTUALLY spend
        
        Args:
            team_data: Single team's financial data with keys:
                      'available_for_fa', 'budget_space', 'win_pct', 'mode', 
                      'fan_interest', 'team_name'
            market_context: Optional league-wide market liquidity data
        
        Returns:
            Dictionary with:
            - available_cash: What they have
            - sentiment_multiplier: Willingness to spend (0.05 - 2.0)
            - real_buying_power: available_cash * sentiment_multiplier
            - archetype: Team archetype
            - max_player_spend: Max on one player (40% of buying power)
            - positional_needs: Positions they'll pay premium for (placeholder)
        """
        available_cash = team_data.get('available_for_fa', 0)
        
        # Determine archetype
        archetype = OwnerSentimentEngine.determine_archetype(team_data)
        
        # Calculate sentiment multiplier
        sentiment_multiplier = OwnerSentimentEngine.calculate_sentiment_multiplier(
            archetype, team_data
        )
        
        # Calculate real buying power
        real_buying_power = available_cash * sentiment_multiplier
        
        # Max spend on one player (40% of buying power)
        max_player_spend = real_buying_power * 0.40
        
        # Check for recent championship bonus (placeholder - would need historical data)
        # For now, we'll use a simple heuristic: if win_pct > 0.617 and Win Now/Dynasty
        recent_champion_bonus = False
        if team_data.get('win_pct', 0) > 0.617 and archetype in ['Win Now', 'Dynasty']:
            recent_champion_bonus = True
            # Apply 25% bonus
            sentiment_multiplier *= 1.25
            real_buying_power = available_cash * sentiment_multiplier
            max_player_spend = real_buying_power * 0.40
        
        return {
            'team_name': team_data.get('team_name', 'Unknown'),
            'available_cash': available_cash,
            'sentiment_multiplier': sentiment_multiplier,
            'real_buying_power': real_buying_power,
            'archetype': archetype,
            'max_player_spend': max_player_spend,
            'positional_needs': [],  # Placeholder - would require roster analysis
            'recent_champion_bonus': recent_champion_bonus
        }
    
    @staticmethod
    def analyze_all_teams(teams_df: pd.DataFrame) -> pd.DataFrame:
        """Analyze sentiment for all teams
        
        Args:
            teams_df: DataFrame with team financial data
        
        Returns:
            DataFrame with sentiment analysis for all teams
        """
        results = []
        
        for _, team in teams_df.iterrows():
            team_dict = team.to_dict()
            sentiment_result = OwnerSentimentEngine.calculate_real_buying_power(team_dict)
            
            # Merge with original team data
            result = {**team_dict, **sentiment_result}
            results.append(result)
        
        return pd.DataFrame(results)
