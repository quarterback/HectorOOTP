"""
Market Liquidity Analyzer
Calculates the "real" money available in the market, not just total budgets
"""

import pandas as pd
from typing import Dict, List


class MarketLiquidityAnalyzer:
    """Analyze market liquidity across teams"""
    
    def __init__(self, teams_df: pd.DataFrame):
        """Initialize with team financial data
        
        Args:
            teams_df: DataFrame with team financial data including 'available_for_fa',
                     'mode', 'win_pct', 'fan_interest'
        """
        self.teams = teams_df.copy()
    
    def calculate_market_liquidity(self, sentiment_data: pd.DataFrame = None) -> Dict:
        """Calculate total market liquidity metrics
        
        Args:
            sentiment_data: Optional DataFrame with sentiment analysis including
                          'real_buying_power' column. If None, uses 'available_for_fa'
        
        Returns:
            Dictionary with market liquidity metrics:
            - total_market_liquidity: Sum of all teams' available FA money
            - top_tier_liquidity: Sum of top 10 richest teams
            - star_liquidity: Sum of competitive teams (Win Now + Dynasty)
            - top_10_teams: List of top 10 team objects
            - competitive_teams: List of competitive team objects
        """
        # Determine which column to use for liquidity
        if sentiment_data is not None and 'real_buying_power' in sentiment_data.columns:
            teams_with_sentiment = self.teams.merge(
                sentiment_data[['team_name', 'real_buying_power']], 
                on='team_name', 
                how='left'
            )
            liquidity_col = 'real_buying_power'
            teams_data = teams_with_sentiment
        else:
            liquidity_col = 'available_for_fa'
            teams_data = self.teams
        
        # Calculate total market liquidity
        total_market_liquidity = teams_data[liquidity_col].sum()
        
        # Get top 10 richest teams
        top_10_teams = teams_data.nlargest(10, liquidity_col)
        top_tier_liquidity = top_10_teams[liquidity_col].sum()
        
        # Get competitive teams (Win Now + Dynasty)
        competitive_teams = teams_data[
            teams_data['mode'].str.contains('Win Now!|Build a Dynasty!', case=False, na=False)
        ]
        star_liquidity = competitive_teams[liquidity_col].sum()
        
        return {
            'total_market_liquidity': total_market_liquidity,
            'top_tier_liquidity': top_tier_liquidity,
            'star_liquidity': star_liquidity,
            'top_10_teams': top_10_teams.to_dict('records'),
            'competitive_teams': competitive_teams.to_dict('records'),
            'liquidity_column': liquidity_col
        }
    
    def calculate_position_specific_liquidity(self, position_needs: Dict[str, List[str]], 
                                             sentiment_data: pd.DataFrame = None) -> Dict[str, float]:
        """Calculate liquidity available from teams with specific positional needs
        
        Args:
            position_needs: Dictionary mapping position codes to list of team names
                          e.g., {'SP': ['Yankees', 'Dodgers'], 'SS': ['Red Sox']}
            sentiment_data: Optional DataFrame with sentiment analysis
        
        Returns:
            Dictionary mapping position codes to available liquidity
        """
        # Determine which column to use for liquidity
        if sentiment_data is not None and 'real_buying_power' in sentiment_data.columns:
            teams_with_sentiment = self.teams.merge(
                sentiment_data[['team_name', 'real_buying_power']], 
                on='team_name', 
                how='left'
            )
            liquidity_col = 'real_buying_power'
            teams_data = teams_with_sentiment
        else:
            liquidity_col = 'available_for_fa'
            teams_data = self.teams
        
        position_liquidity = {}
        
        for position, team_names in position_needs.items():
            teams_with_need = teams_data[teams_data['team_name'].isin(team_names)]
            position_liquidity[position] = teams_with_need[liquidity_col].sum()
        
        return position_liquidity
    
    def get_top_n_average_buying_power(self, n: int, sentiment_data: pd.DataFrame = None) -> float:
        """Get average buying power of top N teams
        
        Args:
            n: Number of top teams to average
            sentiment_data: Optional DataFrame with sentiment analysis
        
        Returns:
            Average buying power of top N teams
        """
        # Determine which column to use for liquidity
        if sentiment_data is not None and 'real_buying_power' in sentiment_data.columns:
            teams_with_sentiment = self.teams.merge(
                sentiment_data[['team_name', 'real_buying_power']], 
                on='team_name', 
                how='left'
            )
            liquidity_col = 'real_buying_power'
            teams_data = teams_with_sentiment
        else:
            liquidity_col = 'available_for_fa'
            teams_data = self.teams
        
        top_n_teams = teams_data.nlargest(n, liquidity_col)
        return top_n_teams[liquidity_col].mean()
