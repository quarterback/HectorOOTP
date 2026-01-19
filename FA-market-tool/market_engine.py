"""
Market-Corrected Salary Calculator
Implements dynamic pricing based on supply/demand
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

class MarketEngine:
    """Calculate market-equilibrium salaries for free agents"""
    
    def __init__(self, teams_df: pd.DataFrame, fa_df: pd.DataFrame):
        self.teams = teams_df
        self.free_agents = fa_df
        self.tmc = self._calculate_tmc()
        self.position_comps = self._build_position_comps()
    
    def _calculate_tmc(self) -> float:
        """Total Market Capacity = sum of top 10 teams' FA budgets"""
        top_10 = self.teams.nlargest(10, 'available_for_fa')
        return top_10['available_for_fa'].sum()
    
    def _build_position_comps(self) -> Dict[str, float]:
        """Calculate $/WAR by position from market demands"""
        comps = {}
        
        for pos in self.free_agents['position']. unique():
            pos_players = self.free_agents[
                (self.free_agents['position'] == pos) & 
                (self.free_agents['war'] > 0.5)  # Filter out low-WAR players
            ]
            
            if len(pos_players) > 0:
                # Median $/WAR to avoid outliers
                comps[pos] = (pos_players['demand'] / pos_players['war'].replace(0, 0.1)).median()
            else:
                comps[pos] = 3_000_000  # Default $3M/WAR
        
        return comps
    
    def calculate_market_price(self, player:  pd.Series, 
                               scarcity_multiplier: Dict[str, float] = None) -> Tuple[float, str]:
        """
        Calculate market-equilibrium price for a player
        
        Returns:  (price, reasoning)
        """
        if scarcity_multiplier is None:
            scarcity_multiplier = {
                'C': 1.15,
                'SS': 1.10,
                'CF': 1.05,
                'SP': 0.95,  # Oversupplied
                'RP': 0.85,
            }
        
        # Base calculation:  $/WAR * player WAR
        pos = player['position']
        war = max(player['war'], 0.5)  # Floor at 0.5 WAR
        base_price = self.position_comps. get(pos, 3_000_000) * war
        
        # Apply scarcity multiplier
        multiplier = scarcity_multiplier.get(pos, 1.0)
        base_price *= multiplier
        
        # Tier-based caps
        overall = player['overall']
        avg_top_3_budget = self.teams.nlargest(3, 'available_for_fa')['available_for_fa'].mean()
        
        if overall >= 4.5:  # Elite
            max_price = avg_top_3_budget * 0.25
            tier = "Elite"
        elif overall >= 3.5:  # Star
            max_price = avg_top_3_budget * 0.15
            tier = "Star"
        else:  # Role Player
            max_price = avg_top_3_budget * 0.08
            tier = "Role Player"
        
        # Blend with in-game demand (60/40 split)
        demand = player['demand']
        market_price = (base_price * 0.6) + (demand * 0.4)
        
        # Cap at tier maximum
        final_price = min(market_price, max_price)
        
        # Reasoning
        reasoning = self._generate_reasoning(
            player, base_price, demand, final_price, tier, multiplier
        )
        
        return final_price, reasoning
    
    def _generate_reasoning(self, player, base_price, demand, final_price, 
                           tier, multiplier) -> str:
        """Generate human-readable explanation"""
        lines = []
        
        lines. append(f"**{tier} {player['position']}** | {player['overall']}⭐ OVR | {player['war']:.1f} WAR")
        
        if multiplier != 1.0:
            lines.append(f"• Position scarcity: {(multiplier - 1) * 100:+.0f}%")
        
        if final_price < demand * 0.8:
            lines.append(f"• ⚠️ Market oversaturated - demand ${demand/1e6:.1f}M exceeds liquidity")
        elif final_price > demand * 1.2:
            lines.append(f"• 📈 Undervalued - market comps suggest ${final_price/1e6:.1f}M")
        
        lines.append(f"• Comp: ${base_price/1e6:.1f}M | Demand: ${demand/1e6:.1f}M")
        
        return "\n".join(lines)
    
    def generate_dashboard(self, top_n: int = 20) -> pd.DataFrame:
        """Generate top opportunities for bargain/value"""
        results = []
        
        for _, player in self.free_agents.iterrows():
            price, reasoning = self.calculate_market_price(player)
            
            results.append({
                'name': player['name'],
                'position': player['position'],
                'overall': player['overall'],
                'war': player['war'],
                'demand': player['demand'],
                'market_price': price,
                'value_delta': player['demand'] - price,
                'reasoning': reasoning
            })
        
        df = pd.DataFrame(results)
        df['value_rating'] = df['value_delta'] / df['demand']. replace(0, 1)
        
        return df.sort_values('value_rating', ascending=False).head(top_n)


# Usage Example
if __name__ == "__main__":
    # Load parsed data
    teams = pd.read_csv('parsed_teams.csv')
    fas = pd.read_csv('parsed_free_agents.csv')
    
    # Initialize engine
    engine = MarketEngine(teams, fas)
    
    # Generate top opportunities
    dashboard = engine.generate_dashboard(top_n=30)
    
    print("🎯 TOP FREE AGENT OPPORTUNITIES\n")
    print(dashboard[['name', 'position', 'overall', 'demand', 'market_price', 'value_delta']])
    
    # Export detailed report
    dashboard.to_csv('fa_market_report.csv', index=False)
