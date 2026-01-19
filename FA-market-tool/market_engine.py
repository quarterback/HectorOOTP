"""
OOTP Market Analysis Engine
Analyzes salary market dynamics across positions, teams, and player tiers
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List

class MarketAnalyzer:
    """Analyze salary market dynamics across the league"""
    
    def __init__(self, teams_df: pd.DataFrame, fa_df: pd.DataFrame, signed_df: pd.DataFrame):
        self.teams = teams_df
        self.free_agents = fa_df
        self.signed = signed_df
        
        # Create combined player dataset
        self.all_players = self._combine_player_data()
        
        # Calculate market statistics
        self.position_stats = self._calculate_position_stats()
        self.tier_stats = self._calculate_tier_stats()
        self.team_stats = self._calculate_team_stats()
    
    def _combine_player_data(self) -> pd.DataFrame:
        """Combine free agents and signed players into unified dataset"""
        # Add source column
        fa = self.free_agents.copy()
        fa['source'] = 'Free Agent'
        fa['salary'] = fa['demand']  # Use demand as salary for FAs
        fa['team'] = 'Free Agent'
        
        signed = self.signed.copy()
        signed['source'] = 'Signed'
        signed['demand'] = signed['salary']
        
        # Ensure both have same columns
        common_cols = ['position', 'name', 'age', 'overall', 'potential', 'salary', 'source', 'team']
        
        fa_subset = fa[common_cols].copy()
        signed_subset = signed[common_cols].copy()
        
        combined = pd.concat([fa_subset, signed_subset], ignore_index=True)
        
        # Add salary_per_war if WAR data available
        if 'war' in self.free_agents.columns:
            war_map = dict(zip(self.free_agents['name'], self.free_agents['war']))
            combined['war'] = combined['name'].map(war_map)
            combined['salary_per_war'] = combined.apply(
                lambda x: x['salary'] / x['war'] if pd.notna(x.get('war')) and x.get('war', 0) > 0.5 else np.nan,
                axis=1
            )
        
        return combined
    
    def _calculate_position_stats(self) -> pd.DataFrame:
        """Calculate salary statistics by position"""
        stats = []
        
        for pos in self.all_players['position'].unique():
            pos_players = self.all_players[self.all_players['position'] == pos]
            signed_pos = pos_players[pos_players['source'] == 'Signed']
            fa_pos = pos_players[pos_players['source'] == 'Free Agent']
            
            stat_dict = {
                'position': pos,
                'total_players': len(pos_players),
                'signed_players': len(signed_pos),
                'free_agents': len(fa_pos),
                'avg_salary': pos_players['salary'].mean(),
                'median_salary': pos_players['salary'].median(),
                'min_salary': pos_players['salary'].min(),
                'max_salary': pos_players['salary'].max(),
                'p25_salary': pos_players['salary'].quantile(0.25),
                'p75_salary': pos_players['salary'].quantile(0.75),
                'total_salary': pos_players['salary'].sum(),
            }
            
            # Add WAR-based stats if available
            if 'salary_per_war' in pos_players.columns:
                valid_spw = pos_players['salary_per_war'].dropna()
                if len(valid_spw) > 0:
                    stat_dict['avg_salary_per_war'] = valid_spw.mean()
                    stat_dict['median_salary_per_war'] = valid_spw.median()
            
            # Add signed player specific stats
            if len(signed_pos) > 0:
                stat_dict['avg_signed_salary'] = signed_pos['salary'].mean()
                stat_dict['median_signed_salary'] = signed_pos['salary'].median()
            
            # Add FA specific stats
            if len(fa_pos) > 0:
                stat_dict['avg_fa_demand'] = fa_pos['salary'].mean()
                stat_dict['median_fa_demand'] = fa_pos['salary'].median()
            
            stats.append(stat_dict)
        
        return pd.DataFrame(stats).sort_values('total_salary', ascending=False)
    
    def _calculate_tier_stats(self) -> pd.DataFrame:
        """Calculate salary statistics by player tier (star rating)"""
        stats = []
        
        # Define tiers
        tiers = [
            ('Elite (5.0★)', 5.0, 5.0),
            ('Star (4.5★)', 4.5, 4.9),
            ('Above Average (4.0★)', 4.0, 4.4),
            ('Average (3.5★)', 3.5, 3.9),
            ('Below Average (3.0★)', 3.0, 3.4),
            ('Role Player (<3.0★)', 0.0, 2.9),
        ]
        
        for tier_name, min_ovr, max_ovr in tiers:
            tier_players = self.all_players[
                (self.all_players['overall'] >= min_ovr) & 
                (self.all_players['overall'] <= max_ovr)
            ]
            
            if len(tier_players) == 0:
                continue
            
            signed_tier = tier_players[tier_players['source'] == 'Signed']
            fa_tier = tier_players[tier_players['source'] == 'Free Agent']
            
            stat_dict = {
                'tier': tier_name,
                'min_overall': min_ovr,
                'max_overall': max_ovr,
                'total_players': len(tier_players),
                'signed_players': len(signed_tier),
                'free_agents': len(fa_tier),
                'avg_salary': tier_players['salary'].mean(),
                'median_salary': tier_players['salary'].median(),
                'min_salary': tier_players['salary'].min(),
                'max_salary': tier_players['salary'].max(),
                'p25_salary': tier_players['salary'].quantile(0.25),
                'p75_salary': tier_players['salary'].quantile(0.75),
            }
            
            # Add signed player stats
            if len(signed_tier) > 0:
                stat_dict['avg_signed_salary'] = signed_tier['salary'].mean()
                stat_dict['median_signed_salary'] = signed_tier['salary'].median()
            
            # Add FA stats
            if len(fa_tier) > 0:
                stat_dict['avg_fa_demand'] = fa_tier['salary'].mean()
                stat_dict['median_fa_demand'] = fa_tier['salary'].median()
            
            stats.append(stat_dict)
        
        return pd.DataFrame(stats)
    
    def _calculate_team_stats(self) -> pd.DataFrame:
        """Calculate team spending and roster statistics"""
        stats = []
        
        for _, team in self.teams.iterrows():
            team_players = self.signed[self.signed['team'] == team['team_name']]
            
            stat_dict = {
                'team_name': team['team_name'],
                'abbr': team['abbr'],
                'payroll': team['payroll'],
                'budget': team['budget'],
                'available_for_fa': team['available_for_fa'],
                'budget_utilization': (team['payroll'] / team['budget']) * 100 if team['budget'] > 0 else 0,
                'roster_size': len(team_players),
                'avg_player_salary': 0,
                'median_player_salary': 0,
                'highest_paid': 0,
                'avg_player_overall': 0,
                'elite_players': 0,
            }
            
            if len(team_players) > 0:
                stat_dict['avg_player_salary'] = team_players['salary'].mean()
                stat_dict['median_player_salary'] = team_players['salary'].median()
                stat_dict['highest_paid'] = team_players['salary'].max()
                stat_dict['avg_player_overall'] = team_players['overall'].mean()
                
                # Count elite players (4.0+ stars)
                stat_dict['elite_players'] = len(team_players[team_players['overall'] >= 4.0])
            
            stats.append(stat_dict)
        
        return pd.DataFrame(stats).sort_values('payroll', ascending=False)
    
    def get_position_market_summary(self, position: str = None) -> pd.DataFrame:
        """Get detailed position market summary"""
        if position:
            return self.position_stats[self.position_stats['position'] == position]
        return self.position_stats
    
    def get_tier_market_summary(self, tier: str = None) -> pd.DataFrame:
        """Get detailed tier market summary"""
        if tier:
            return self.tier_stats[self.tier_stats['tier'] == tier]
        return self.tier_stats
    
    def get_team_market_summary(self, team: str = None) -> pd.DataFrame:
        """Get detailed team market summary"""
        if team:
            return self.team_stats[
                (self.team_stats['team_name'] == team) | 
                (self.team_stats['abbr'] == team)
            ]
        return self.team_stats
    
    def get_market_overview(self) -> Dict:
        """Get overall market overview statistics"""
        return {
            'total_teams': len(self.teams),
            'total_league_payroll': self.teams['payroll'].sum(),
            'total_league_budget': self.teams['budget'].sum(),
            'total_fa_capacity': self.teams['available_for_fa'].sum(),
            'avg_team_payroll': self.teams['payroll'].mean(),
            'avg_team_budget': self.teams['budget'].mean(),
            'total_signed_players': len(self.signed),
            'total_free_agents': len(self.free_agents),
            'total_fa_demands': self.free_agents['demand'].sum(),
            'avg_signed_salary': self.signed['salary'].mean(),
            'median_signed_salary': self.signed['salary'].median(),
            'avg_fa_demand': self.free_agents['demand'].mean(),
            'median_fa_demand': self.free_agents['demand'].median(),
        }
    
    def get_comparable_players(self, position: str, overall_min: float, overall_max: float, 
                               limit: int = 20) -> pd.DataFrame:
        """Get comparable players by position and overall rating"""
        comps = self.all_players[
            (self.all_players['position'] == position) &
            (self.all_players['overall'] >= overall_min) &
            (self.all_players['overall'] <= overall_max)
        ].sort_values('salary', ascending=False).head(limit)
        
        return comps[['name', 'position', 'overall', 'potential', 'age', 'salary', 'source', 'team']]


# Usage Example
if __name__ == "__main__":
    # Load parsed data
    teams = pd.read_csv('parsed_teams.csv')
    fas = pd.read_csv('parsed_free_agents.csv')
    signed = pd.read_csv('parsed_signed.csv')
    
    # Initialize analyzer
    analyzer = MarketAnalyzer(teams, fas, signed)
    
    # Market Overview
    print("="*80)
    print("📊 MARKET OVERVIEW")
    print("="*80)
    overview = analyzer.get_market_overview()
    print(f"Total Teams: {overview['total_teams']}")
    print(f"Total League Payroll: ${overview['total_league_payroll']/1e6:.1f}M")
    print(f"Total League Budget: ${overview['total_league_budget']/1e6:.1f}M")
    print(f"Total FA Capacity: ${overview['total_fa_capacity']/1e6:.1f}M")
    print(f"\nSigned Players: {overview['total_signed_players']}")
    print(f"Avg Signed Salary: ${overview['avg_signed_salary']/1e6:.2f}M")
    print(f"Median Signed Salary: ${overview['median_signed_salary']/1e6:.2f}M")
    print(f"\nFree Agents: {overview['total_free_agents']}")
    print(f"Total FA Demands: ${overview['total_fa_demands']/1e6:.1f}M")
    print(f"Avg FA Demand: ${overview['avg_fa_demand']/1e6:.2f}M")
    
    # Position Market Analysis
    print("\n" + "="*80)
    print("💰 POSITION MARKET ANALYSIS")
    print("="*80)
    pos_summary = analyzer.get_position_market_summary()
    print(pos_summary[['position', 'total_players', 'avg_salary', 'median_salary', 'signed_players', 'free_agents']].to_string(index=False))
    
    # Tier Market Analysis
    print("\n" + "="*80)
    print("⭐ PLAYER TIER MARKET ANALYSIS")
    print("="*80)
    tier_summary = analyzer.get_tier_market_summary()
    print(tier_summary[['tier', 'total_players', 'avg_salary', 'median_salary', 'signed_players', 'free_agents']].to_string(index=False))
    
    # Top Spending Teams
    print("\n" + "="*80)
    print("💵 TOP SPENDING TEAMS")
    print("="*80)
    top_teams = analyzer.get_team_market_summary().head(10)
    print(top_teams[['team_name', 'payroll', 'budget', 'available_for_fa', 'roster_size', 'elite_players']].to_string(index=False))
