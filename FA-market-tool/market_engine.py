"""
OOTP Market Analysis Engine
Analyzes salary market dynamics across positions, teams, and player tiers
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import random
import datetime

# Import new market equilibrium modules
from market_liquidity import MarketLiquidityAnalyzer
from sentiment_logic import OwnerSentimentEngine
from positional_scarcity import PositionalScarcityAdjuster
from desperation_decay import DesperationDecayCalculator

class OwnerInvestmentCalculator:
    """Calculate owner investment based on team performance, mode, and fan interest"""
    
    # Fire sale percentage range (random reduction)
    FIRE_SALE_MIN = 0.51  # 51% minimum reduction
    FIRE_SALE_MAX = 0.77  # 77% maximum reduction
    
    # Maximum possible aggressiveness score calculation
    MAX_PERFORMANCE_FACTOR = 0.5
    MAX_MODE_FACTOR = 1.0
    MAX_INTEREST_FACTOR = 1.2
    MAX_COMBINED_FACTOR = MAX_PERFORMANCE_FACTOR * MAX_MODE_FACTOR * MAX_INTEREST_FACTOR  # = 0.6
    
    @staticmethod
    def calculate_performance_factor(win_pct: float) -> float:
        """Calculate performance factor based on last year's win percentage
        
        Win % Range -> Factor:
        >0.617 (>100 wins) -> 50%
        0.580-0.617 (94-100) -> 40%
        0.543-0.580 (88-94) -> 30%
        0.506-0.543 (82-88) -> 20%
        0.469-0.506 (76-82) -> 15%
        0.432-0.469 (70-76) -> 10%
        <0.432 (<70 wins) -> 5%
        """
        if win_pct > 0.617:
            return 0.50
        elif win_pct >= 0.580:
            return 0.40
        elif win_pct >= 0.543:
            return 0.30
        elif win_pct >= 0.506:
            return 0.20
        elif win_pct >= 0.469:
            return 0.15
        elif win_pct >= 0.432:
            return 0.10
        else:
            return 0.05
    
    @staticmethod
    def calculate_mode_factor(mode: str) -> float:
        """Calculate mode factor based on team strategy
        
        Win Now! -> 100%
        Build a Dynasty! -> 75%
        Neutral -> 50%
        Rebuilding -> 10%
        """
        mode_lower = mode.lower().strip()
        if 'win now' in mode_lower:
            return 1.00
        elif 'dynasty' in mode_lower:
            return 0.75
        elif 'neutral' in mode_lower:
            return 0.50
        elif 'rebuild' in mode_lower:
            return 0.10
        else:
            return 0.50  # Default to neutral
    
    @staticmethod
    def calculate_interest_factor(fan_interest: int) -> float:
        """Calculate interest factor based on fan interest (0-100)
        
        90-100 -> 120%
        75-89 -> 110%
        60-74 -> 100%
        45-59 -> 90%
        30-44 -> 85%
        <30 -> 80%
        """
        if fan_interest >= 90:
            return 1.20
        elif fan_interest >= 75:
            return 1.10
        elif fan_interest >= 60:
            return 1.00
        elif fan_interest >= 45:
            return 0.90
        elif fan_interest >= 30:
            return 0.85
        else:
            return 0.80
    
    @staticmethod
    def calculate_owner_investment(budget: float, win_pct: float, mode: str, 
                                  fan_interest: int, postseason_bonus: float = 0.0,
                                  fire_sale: bool = False) -> Dict:
        """Calculate owner investment with detailed breakdown
        
        Args:
            budget: Team's base budget
            win_pct: Last year's win percentage
            mode: Team mode (Win Now, Dynasty, Neutral, Rebuilding)
            fan_interest: Fan interest rating (0-100)
            postseason_bonus: Postseason bonus multiplier (0.15 for WC, 0.25 for Division, etc.)
            fire_sale: Whether this is a fire sale scenario
        
        Returns:
            Dictionary with detailed breakdown
        """
        perf_factor = OwnerInvestmentCalculator.calculate_performance_factor(win_pct)
        mode_factor = OwnerInvestmentCalculator.calculate_mode_factor(mode)
        interest_factor = OwnerInvestmentCalculator.calculate_interest_factor(fan_interest)
        
        # Base owner investment
        base_investment = budget * perf_factor * mode_factor * interest_factor
        
        # Apply postseason bonus
        scenario_multiplier = 1.0 + postseason_bonus
        final_investment = base_investment * scenario_multiplier
        
        # Fire sale: random reduction of 51-77%
        fire_sale_reduction = 0.0
        owner_pocketed = 0.0
        if fire_sale:
            fire_sale_pct = random.uniform(
                OwnerInvestmentCalculator.FIRE_SALE_MIN, 
                OwnerInvestmentCalculator.FIRE_SALE_MAX
            )
            fire_sale_reduction = fire_sale_pct
            owner_pocketed = final_investment * fire_sale_pct
            final_investment = final_investment * (1 - fire_sale_pct)
        
        return {
            'performance_factor': perf_factor,
            'mode_factor': mode_factor,
            'interest_factor': interest_factor,
            'base_investment': base_investment,
            'postseason_bonus': postseason_bonus,
            'scenario_multiplier': scenario_multiplier,
            'fire_sale': fire_sale,
            'fire_sale_reduction': fire_sale_reduction,
            'owner_pocketed': owner_pocketed,
            'final_investment': final_investment,
        }
    
    @staticmethod
    def calculate_total_fa_budget(budget: float, payroll: float, budget_space: float,
                                  cash_from_trades: float, owner_investment: float) -> float:
        """Calculate total FA budget
        
        Total FA Budget = (Budget - Payroll) + BgtSpc + CT + Owner Investment
        """
        base_available = budget - payroll
        total = base_available + budget_space + cash_from_trades + owner_investment
        return total
    
    @staticmethod
    def calculate_aggressiveness_score(performance_factor: float, mode_factor: float, 
                                      interest_factor: float) -> float:
        """Calculate owner aggressiveness score (0-100)
        
        Combines all factors into a single 0-100 score
        """
        combined = performance_factor * mode_factor * interest_factor
        score = (combined / OwnerInvestmentCalculator.MAX_COMBINED_FACTOR) * 100
        return min(100, max(0, score))

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
        
        # Ensure both have same columns - include enriched team columns if available
        common_cols = ['position', 'name', 'age', 'overall', 'potential', 'salary', 'source', 'team']
        
        # Add enriched team columns if they exist in signed data
        enriched_team_cols = ['team_abbr', 'team_full_name', 'team_name', 'team_city', 'team_mode', 
                             'team_win_pct', 'team_budget', 'team_payroll', 'team_budget_space',
                             'team_fan_interest', 'team_revenue', 'team_expenses', 
                             'team_last_year_wins', 'team_last_year_losses']
        
        available_enriched_cols = [col for col in enriched_team_cols if col in signed.columns]
        if available_enriched_cols:
            common_cols.extend(available_enriched_cols)
        
        fa_subset = fa[common_cols].copy() if all(col in fa.columns for col in common_cols) else fa[['position', 'name', 'age', 'overall', 'potential', 'salary', 'source', 'team']].copy()
        signed_subset = signed[common_cols].copy() if all(col in signed.columns for col in common_cols) else signed[['position', 'name', 'age', 'overall', 'potential', 'salary', 'source', 'team']].copy()
        
        # Ensure both dataframes have the same columns
        all_cols = set(fa_subset.columns) | set(signed_subset.columns)
        for col in all_cols:
            if col not in fa_subset.columns:
                fa_subset[col] = None
            if col not in signed_subset.columns:
                signed_subset[col] = None
        
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
        
        # Define tiers - Full OOTP star rating tiers (0.5 to 5.0 in 0.5 increments)
        tiers = [
            ('Elite (5.0★)', 5.0, 5.0),
            ('Star (4.5★)', 4.5, 4.5),
            ('Above Average (4.0★)', 4.0, 4.0),
            ('Solid Average (3.5★)', 3.5, 3.5),
            ('Average (3.0★)', 3.0, 3.0),
            ('Below Average (2.5★)', 2.5, 2.5),
            ('Backup/Depth (2.0★)', 2.0, 2.0),
            ('Fringe (1.5★)', 1.5, 1.5),
            ('Minor League (1.0★)', 1.0, 1.0),
            ('Organizational (0.5★)', 0.5, 0.5),
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
        """Calculate team financial statistics from TeamFin.html data with owner investment"""
        stats = []
        
        for _, team in self.teams.iterrows():
            # Calculate owner investment
            investment_calc = OwnerInvestmentCalculator.calculate_owner_investment(
                budget=team.get('budget', 100000000.0),
                win_pct=team.get('win_pct', 0.500),
                mode=team.get('mode', 'Neutral'),
                fan_interest=team.get('fan_interest', 50)
            )
            
            # Calculate total FA budget
            total_fa_budget = OwnerInvestmentCalculator.calculate_total_fa_budget(
                budget=team.get('budget', 100000000.0),
                payroll=team.get('payroll', 0.0),
                budget_space=team.get('budget_space', 0.0),
                cash_from_trades=team.get('cash_from_trades', 0.0),
                owner_investment=investment_calc['final_investment']
            )
            
            # Calculate aggressiveness score
            aggressiveness = OwnerInvestmentCalculator.calculate_aggressiveness_score(
                investment_calc['performance_factor'],
                investment_calc['mode_factor'],
                investment_calc['interest_factor']
            )
            
            stat_dict = {
                'team_name': team.get('team_name', ''),
                'team_city': team.get('team_city', ''),
                'abbr': team.get('abbr', ''),
                'payroll': team.get('payroll', 0.0),
                'budget': team.get('budget', 100000000.0),
                'budget_space': team.get('budget_space', 0.0),
                'cash_from_trades': team.get('cash_from_trades', 0.0),
                'ticket_price': team.get('ticket_price', 0.0),
                'fan_interest': team.get('fan_interest', 50),
                'mode': team.get('mode', 'Neutral'),
                'revenue': team.get('revenue', 0.0),
                'expenses': team.get('expenses', 0.0),
                'last_year_wins': team.get('last_year_wins', 0),
                'last_year_losses': team.get('last_year_losses', 0),
                'win_pct': team.get('win_pct', 0.500),
                'performance_factor': investment_calc['performance_factor'],
                'mode_factor': investment_calc['mode_factor'],
                'interest_factor': investment_calc['interest_factor'],
                'owner_investment': investment_calc['final_investment'],
                'base_fa_budget': team.get('budget', 100000000.0) - team.get('payroll', 0.0),
                'total_fa_budget': total_fa_budget,
                'aggressiveness_score': aggressiveness,
                'available_for_fa': team.get('available_for_fa', 0.0),
                'budget_utilization': (team.get('payroll', 0.0) / team.get('budget', 100000000.0)) * 100 if team.get('budget', 100000000.0) > 0 else 0,
            }
            
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
        
        # Include enriched team columns if available
        base_cols = ['name', 'position', 'overall', 'potential', 'age', 'salary', 'source', 'team']
        enriched_team_cols = ['team_full_name', 'team_abbr', 'team_mode', 'team_win_pct', 
                              'team_budget', 'team_payroll']
        
        for col in enriched_team_cols:
            if col in comps.columns:
                base_cols.append(col)
        
        return comps[base_cols]
    
    def get_salary_bands(self, position: str = None, tier: str = None, source: str = 'both') -> pd.DataFrame:
        """
        Get salary bands (percentiles) grouped by position, tier, and source.
        
        Args:
            position: Filter by position (optional)
            tier: Filter by tier name (optional)
            source: 'signed', 'fa', or 'both'
        
        Returns:
            DataFrame with columns: position, tier, source, count, min, p25, median, p75, max, avg
        """
        # Define tiers - Full OOTP star rating tiers (0.5 to 5.0 in 0.5 increments)
        tiers = [
            ('Elite (5.0★)', 5.0, 5.0),
            ('Star (4.5★)', 4.5, 4.5),
            ('Above Average (4.0★)', 4.0, 4.0),
            ('Solid Average (3.5★)', 3.5, 3.5),
            ('Average (3.0★)', 3.0, 3.0),
            ('Below Average (2.5★)', 2.5, 2.5),
            ('Backup/Depth (2.0★)', 2.0, 2.0),
            ('Fringe (1.5★)', 1.5, 1.5),
            ('Minor League (1.0★)', 1.0, 1.0),
            ('Organizational (0.5★)', 0.5, 0.5),
        ]
        
        # Filter data based on source
        if source == 'signed':
            data = self.all_players[self.all_players['source'] == 'Signed'].copy()
        elif source == 'fa':
            data = self.all_players[self.all_players['source'] == 'Free Agent'].copy()
        else:
            data = self.all_players.copy()
        
        # Apply position filter if specified
        if position:
            data = data[data['position'] == position]
        
        results = []
        
        # Get unique positions or use all if not filtered
        positions = [position] if position else sorted(data['position'].unique())
        
        for pos in positions:
            pos_data = data[data['position'] == pos]
            
            for tier_name, min_ovr, max_ovr in tiers:
                # Skip if tier filter is specified and doesn't match
                if tier and tier != tier_name:
                    continue
                
                tier_data = pos_data[
                    (pos_data['overall'] >= min_ovr) & 
                    (pos_data['overall'] <= max_ovr)
                ]
                
                if source == 'both':
                    # Create separate entries for signed and FA
                    for src in ['Signed', 'Free Agent']:
                        src_data = tier_data[tier_data['source'] == src]
                        if len(src_data) > 0:
                            results.append({
                                'position': pos,
                                'tier': tier_name,
                                'source': src,
                                'count': len(src_data),
                                'min': src_data['salary'].min(),
                                'p25': src_data['salary'].quantile(0.25),
                                'median': src_data['salary'].median(),
                                'p75': src_data['salary'].quantile(0.75),
                                'max': src_data['salary'].max(),
                                'avg': src_data['salary'].mean(),
                            })
                else:
                    # Single entry for the specified source
                    if len(tier_data) > 0:
                        results.append({
                            'position': pos,
                            'tier': tier_name,
                            'source': 'Signed' if source == 'signed' else 'Free Agent',
                            'count': len(tier_data),
                            'min': tier_data['salary'].min(),
                            'p25': tier_data['salary'].quantile(0.25),
                            'median': tier_data['salary'].median(),
                            'p75': tier_data['salary'].quantile(0.75),
                            'max': tier_data['salary'].max(),
                            'avg': tier_data['salary'].mean(),
                        })
        
        return pd.DataFrame(results)
    
    def get_position_tier_matrix(self, metric: str = 'median', source: str = 'both') -> pd.DataFrame:
        """
        Create a matrix of Position (rows) x Tier (columns) with salary values.
        
        Args:
            metric: 'median', 'avg', 'p25', 'p75', 'min', or 'max'
            source: 'signed', 'fa', or 'both'
        
        Returns:
            DataFrame with positions as rows, tiers as columns, salary values as cells
        """
        bands = self.get_salary_bands(source=source)
        
        if len(bands) == 0:
            return pd.DataFrame()
        
        # If source is 'both', aggregate the data
        if source == 'both':
            # Average the metric across signed and FA
            agg_data = bands.groupby(['position', 'tier'])[metric].mean().reset_index()
        else:
            agg_data = bands[['position', 'tier', metric]]
        
        # Pivot to create matrix
        matrix = agg_data.pivot(index='position', columns='tier', values=metric)
        
        # Reorder columns to match tier hierarchy
        tier_order = [
            'Elite (5.0★)', 
            'Star (4.5★)', 
            'Above Average (4.0★)', 
            'Solid Average (3.5★)', 
            'Average (3.0★)', 
            'Below Average (2.5★)', 
            'Backup/Depth (2.0★)', 
            'Fringe (1.5★)', 
            'Minor League (1.0★)', 
            'Organizational (0.5★)'
        ]
        
        # Only include columns that exist
        available_tiers = [t for t in tier_order if t in matrix.columns]
        matrix = matrix[available_tiers]
        
        return matrix
    
    def get_market_gap_analysis(self) -> pd.DataFrame:
        """
        Calculate the gap between FA demands and signed salaries by position and tier.
        
        Returns:
            DataFrame with: position, tier, signed_median, fa_median, gap_amount, gap_percentage
        """
        # Get salary bands for both signed and FA
        signed_bands = self.get_salary_bands(source='signed')
        fa_bands = self.get_salary_bands(source='fa')
        
        results = []
        
        # Iterate through all position/tier combinations
        for _, signed_row in signed_bands.iterrows():
            pos = signed_row['position']
            tier = signed_row['tier']
            
            # Find matching FA data
            fa_row = fa_bands[
                (fa_bands['position'] == pos) & 
                (fa_bands['tier'] == tier)
            ]
            
            if len(fa_row) > 0:
                fa_row = fa_row.iloc[0]
                gap_amount = fa_row['median'] - signed_row['median']
                gap_percentage = (gap_amount / signed_row['median'] * 100) if signed_row['median'] > 0 else 0
                
                results.append({
                    'position': pos,
                    'tier': tier,
                    'signed_median': signed_row['median'],
                    'signed_count': signed_row['count'],
                    'fa_median': fa_row['median'],
                    'fa_count': fa_row['count'],
                    'gap_amount': gap_amount,
                    'gap_percentage': gap_percentage,
                })
        
        return pd.DataFrame(results).sort_values(['position', 'tier'])
    
    def get_player_pricing(self, position: str, overall_min: float, overall_max: float, 
                          age_min: int = None, age_max: int = None) -> Dict:
        """
        Get pricing recommendation for a player based on comparables.
        
        Returns:
            {
                'median': float,
                'p25': float,
                'p75': float,
                'min': float,
                'max': float,
                'avg': float,
                'signed_avg': float,
                'fa_avg': float,
                'comparables': DataFrame,
                'total_comps': int,
                'signed_comps': int,
                'fa_comps': int
            }
        """
        # Filter by position and overall rating
        comps = self.all_players[
            (self.all_players['position'] == position) &
            (self.all_players['overall'] >= overall_min) &
            (self.all_players['overall'] <= overall_max)
        ].copy()
        
        # Apply age filter if specified
        if age_min is not None:
            comps = comps[comps['age'] >= age_min]
        if age_max is not None:
            comps = comps[comps['age'] <= age_max]
        
        # Calculate statistics
        if len(comps) == 0:
            return {
                'median': 0,
                'p25': 0,
                'p75': 0,
                'min': 0,
                'max': 0,
                'avg': 0,
                'signed_avg': 0,
                'fa_avg': 0,
                'comparables': pd.DataFrame(),
                'total_comps': 0,
                'signed_comps': 0,
                'fa_comps': 0
            }
        
        signed_comps = comps[comps['source'] == 'Signed']
        fa_comps = comps[comps['source'] == 'Free Agent']
        
        return {
            'median': comps['salary'].median(),
            'p25': comps['salary'].quantile(0.25),
            'p75': comps['salary'].quantile(0.75),
            'min': comps['salary'].min(),
            'max': comps['salary'].max(),
            'avg': comps['salary'].mean(),
            'signed_avg': signed_comps['salary'].mean() if len(signed_comps) > 0 else 0,
            'fa_avg': fa_comps['salary'].mean() if len(fa_comps) > 0 else 0,
            'comparables': comps.sort_values('salary', ascending=False),
            'total_comps': len(comps),
            'signed_comps': len(signed_comps),
            'fa_comps': len(fa_comps)
        }
    
    def calculate_offer_percentile(self, offer: float, comparables: pd.DataFrame) -> float:
        """
        Calculate what percentile an offer represents among comparables.
        
        Args:
            offer: The proposed salary offer
            comparables: DataFrame of comparable players with 'salary' column
        
        Returns:
            Percentile (0-100) where the offer falls
        """
        if len(comparables) == 0 or 'salary' not in comparables.columns:
            return 50.0  # Default to median if no comparables
        
        salaries = comparables['salary'].values
        # Count how many salaries are below the offer
        below_count = np.sum(salaries < offer)
        percentile = (below_count / len(salaries)) * 100
        
        return percentile
    
    # ========== MARKET EQUILIBRIUM METHODS ==========
    
    def get_market_equilibrium_data(self, current_date: datetime.date = None) -> Dict:
        """Get comprehensive market equilibrium analysis
        
        Args:
            current_date: Current date for desperation decay calculations
                         Defaults to January 1 of current year
        
        Returns:
            Dictionary with all market equilibrium data:
            - liquidity: Market liquidity analysis
            - sentiment: Owner sentiment analysis for all teams
            - fmv: Fair Market Value calculations for all FAs
            - decay: Desperation decay calculations (if date provided)
        """
        # Set default date if not provided
        if current_date is None:
            current_date = datetime.date(datetime.datetime.now().year, 1, 1)
        
        # Calculate owner sentiment for all teams
        sentiment_df = OwnerSentimentEngine.analyze_all_teams(self.teams)
        
        # Calculate market liquidity with sentiment data
        liquidity_analyzer = MarketLiquidityAnalyzer(self.teams)
        liquidity_data = liquidity_analyzer.calculate_market_liquidity(sentiment_df)
        
        # Calculate FMV for all free agents
        fmv_df = PositionalScarcityAdjuster.calculate_fmv_for_all_players(
            self.free_agents, liquidity_data
        )
        
        # Calculate desperation decay
        decay_df = DesperationDecayCalculator.apply_decay_to_all_players(
            fmv_df, current_date, liquidity_data
        )
        
        return {
            'liquidity': liquidity_data,
            'sentiment': sentiment_df,
            'fmv': fmv_df,
            'decay': decay_df,
            'current_date': current_date
        }
    
    def calculate_fmv_for_player(self, position: str, overall: float, war: float,
                                demand: float = 0) -> Dict:
        """Calculate Fair Market Value for a specific player
        
        Args:
            position: Player position code
            overall: Overall rating (0.5 to 5.0 stars)
            war: Projected WAR
            demand: Optional current OOTP demand
        
        Returns:
            Dictionary with FMV calculation breakdown
        """
        # Get sentiment data and liquidity
        sentiment_df = OwnerSentimentEngine.analyze_all_teams(self.teams)
        liquidity_analyzer = MarketLiquidityAnalyzer(self.teams)
        liquidity_data = liquidity_analyzer.calculate_market_liquidity(sentiment_df)
        
        # Calculate league $/WAR
        league_dollars_per_war = PositionalScarcityAdjuster.calculate_league_dollars_per_war(
            self.free_agents
        )
        
        # Build player dict
        player = {
            'position': position,
            'overall': overall,
            'war': war,
            'demand': demand
        }
        
        # Calculate FMV
        fmv_result = PositionalScarcityAdjuster.calculate_fmv(
            player, league_dollars_per_war, liquidity_data
        )
        
        return {
            **fmv_result,
            'league_dollars_per_war': league_dollars_per_war,
            'position': position,
            'overall': overall,
            'war': war
        }


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
    print(top_teams[['team_name', 'payroll', 'budget', 'available_for_fa', 'budget_utilization']].to_string(index=False))
