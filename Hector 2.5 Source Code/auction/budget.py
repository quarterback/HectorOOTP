"""
Budget management for auction system.
Handles budget configuration, tracking, and validation.
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Constants
DEFAULT_RESERVE_PER_PLAYER = 1.0  # Reserve $1M per remaining required player


@dataclass
class BudgetConfig:
    """Configuration for team budgets in auction"""
    team_budgets: Dict[str, float]  # Team abbreviation -> budget in millions
    min_spend_percentage: float = 0.75  # Minimum percentage of budget that must be spent
    min_roster_size: int = 18
    max_roster_size: int = 25
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(**data)
    
    @classmethod
    def default_config(cls, teams: List[str], budget_per_team: float = 100.0):
        """Create default budget config with equal budgets for all teams"""
        team_budgets = {team: budget_per_team for team in teams}
        return cls(team_budgets=team_budgets)
    
    def save(self, filepath: str):
        """Save budget configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: str):
        """Load budget configuration from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class BudgetManager:
    """Manages budget tracking and validation during auction"""
    
    def __init__(self, config: BudgetConfig):
        self.config = config
        self.spent: Dict[str, float] = {team: 0.0 for team in config.team_budgets}
        self.roster_sizes: Dict[str, int] = {team: 0 for team in config.team_budgets}
        self.players_acquired: Dict[str, List[dict]] = {team: [] for team in config.team_budgets}
    
    def get_remaining_budget(self, team: str) -> float:
        """Get remaining budget for a team"""
        return self.config.team_budgets.get(team, 0.0) - self.spent.get(team, 0.0)
    
    def get_roster_spots_remaining(self, team: str) -> int:
        """Get remaining roster spots for a team"""
        return self.config.max_roster_size - self.roster_sizes.get(team, 0)
    
    def can_afford_bid(self, team: str, bid_amount: float) -> bool:
        """Check if team can afford a bid"""
        remaining = self.get_remaining_budget(team)
        # Must leave at least DEFAULT_RESERVE_PER_PLAYER per remaining required roster spot
        roster_remaining = self.config.min_roster_size - self.roster_sizes.get(team, 0)
        min_reserve = max(0, roster_remaining - 1) * DEFAULT_RESERVE_PER_PLAYER
        return bid_amount <= (remaining - min_reserve)
    
    def can_add_player(self, team: str) -> bool:
        """Check if team can add another player"""
        return self.roster_sizes.get(team, 0) < self.config.max_roster_size
    
    def validate_bid(self, team: str, bid_amount: float) -> Tuple[bool, Optional[str]]:
        """
        Validate if a bid is allowed.
        Returns (is_valid, error_message)
        """
        if team not in self.config.team_budgets:
            return False, f"Team {team} not found in budget configuration"
        
        if not self.can_add_player(team):
            return False, f"Team {team} has reached maximum roster size ({self.config.max_roster_size})"
        
        if not self.can_afford_bid(team, bid_amount):
            remaining = self.get_remaining_budget(team)
            roster_remaining = self.config.min_roster_size - self.roster_sizes.get(team, 0)
            return False, f"Team {team} cannot afford ${bid_amount:.1f}M (${remaining:.1f}M available, must reserve for {roster_remaining} more players)"
        
        return True, None
    
    def record_acquisition(self, team: str, player: dict, price: float):
        """Record a player acquisition"""
        self.spent[team] = self.spent.get(team, 0.0) + price
        self.roster_sizes[team] = self.roster_sizes.get(team, 0) + 1
        self.players_acquired[team].append({
            'player': player,
            'price': price
        })
    
    def meets_minimum_spend(self, team: str) -> bool:
        """Check if team has met minimum spend requirement"""
        budget = self.config.team_budgets.get(team, 0.0)
        min_spend = budget * self.config.min_spend_percentage
        return self.spent.get(team, 0.0) >= min_spend
    
    def meets_minimum_roster(self, team: str) -> bool:
        """Check if team has met minimum roster size"""
        return self.roster_sizes.get(team, 0) >= self.config.min_roster_size
    
    def get_team_summary(self, team: str) -> dict:
        """Get summary of team's auction status"""
        budget = self.config.team_budgets.get(team, 0.0)
        spent = self.spent.get(team, 0.0)
        roster_size = self.roster_sizes.get(team, 0)
        
        return {
            'team': team,
            'starting_budget': budget,
            'spent': spent,
            'remaining': budget - spent,
            'roster_size': roster_size,
            'roster_spots_remaining': self.config.max_roster_size - roster_size,
            'meets_min_spend': self.meets_minimum_spend(team),
            'meets_min_roster': self.meets_minimum_roster(team),
            'players_acquired': self.players_acquired.get(team, [])
        }
    
    def get_all_summaries(self) -> List[dict]:
        """Get summaries for all teams"""
        return [self.get_team_summary(team) for team in self.config.team_budgets.keys()]
