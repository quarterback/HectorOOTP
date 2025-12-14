"""
AI bidding strategies for auction system.
"""

from enum import Enum
from typing import Dict, List, Optional
import random


class BiddingStrategy(Enum):
    """AI bidding strategy types"""
    AGGRESSIVE = "aggressive"  # Bids up to 110% of valuation, prioritizes stars
    BALANCED = "balanced"      # Bids up to 95% of valuation, spreads budget evenly
    CONSERVATIVE = "conservative"  # Bids up to 85% of valuation, focuses on value


class AIBidder:
    """AI bidder with configurable strategy"""
    
    def __init__(self, team: str, strategy: BiddingStrategy, budget_manager, valuations: Dict):
        self.team = team
        self.strategy = strategy
        self.budget_manager = budget_manager
        self.valuations = valuations
        
        # Strategy parameters
        if strategy == BiddingStrategy.AGGRESSIVE:
            self.max_valuation_pct = 1.10
            self.star_priority = True
            self.value_threshold = 60  # Only bids on players with score >= 60
        elif strategy == BiddingStrategy.BALANCED:
            self.max_valuation_pct = 0.95
            self.star_priority = False
            self.value_threshold = 45
        else:  # CONSERVATIVE
            self.max_valuation_pct = 0.85
            self.star_priority = False
            self.value_threshold = 40
        
        # Position needs tracking
        self.position_needs: Dict[str, int] = self._initialize_position_needs()
    
    def _initialize_position_needs(self) -> Dict[str, int]:
        """Initialize position needs based on typical roster"""
        return {
            'SP': 5,
            'RP': 7,
            'CL': 0,  # Treat as RP
            'C': 2,
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'LF': 1,
            'CF': 1,
            'RF': 1,
            'DH': 1,
        }
    
    def _get_position_need(self, position: str) -> int:
        """Get current need for a position"""
        pos = position.upper().strip()
        if pos == 'CL':
            pos = 'RP'
        return self.position_needs.get(pos, 0)
    
    def _update_position_need(self, position: str):
        """Update position needs after acquiring a player"""
        pos = position.upper().strip()
        if pos == 'CL':
            pos = 'RP'
        if pos in self.position_needs and self.position_needs[pos] > 0:
            self.position_needs[pos] -= 1
    
    def should_bid(self, player: Dict, current_price: float) -> bool:
        """
        Determine if AI should bid on this player at current price.
        
        Args:
            player: Player dictionary
            current_price: Current highest bid
            
        Returns:
            True if AI should bid, False otherwise
        """
        player_name = player.get('Name', '')
        position = player.get('POS', '').upper().strip()
        
        # Check if we have valuation for this player
        if player_name not in self.valuations:
            return False
        
        valuation = self.valuations[player_name]
        base_score = valuation.get('base_score', 0)
        suggested_price = valuation.get('suggested_price', 0)
        
        # Check if player meets quality threshold
        if base_score < self.value_threshold:
            return False
        
        # Check position need
        position_need = self._get_position_need(position)
        if position_need <= 0:
            # Only bid if exceptional value
            if current_price > suggested_price * 0.5:
                return False
        
        # Calculate our max bid for this player
        max_bid = suggested_price * self.max_valuation_pct
        
        # Position need multiplier
        if position_need > 0:
            need_multiplier = 1.0 + (position_need * 0.05)  # Up to 1.25x for high need
            max_bid *= min(need_multiplier, 1.25)
        
        # Star priority for aggressive strategy
        if self.star_priority and base_score >= 75:
            max_bid *= 1.1
        
        # Check if we can afford to bid
        next_bid = current_price + 0.5  # Minimum bid increment
        
        # Don't bid if price already exceeds our max
        if next_bid > max_bid:
            return False
        
        # Check budget constraints
        valid, _ = self.budget_manager.validate_bid(self.team, next_bid)
        if not valid:
            return False
        
        # Add some randomness (10% chance to pass even if conditions met)
        if random.random() < 0.10:
            return False
        
        return True
    
    def calculate_max_bid(self, player: Dict) -> float:
        """
        Calculate maximum bid for a player.
        
        Returns:
            Maximum amount willing to bid
        """
        player_name = player.get('Name', '')
        position = player.get('POS', '').upper().strip()
        
        if player_name not in self.valuations:
            return 0.0
        
        valuation = self.valuations[player_name]
        suggested_price = valuation.get('suggested_price', 0)
        base_score = valuation.get('base_score', 0)
        
        # Base max bid
        max_bid = suggested_price * self.max_valuation_pct
        
        # Position need adjustment
        position_need = self._get_position_need(position)
        if position_need > 0:
            need_multiplier = 1.0 + (position_need * 0.05)
            max_bid *= min(need_multiplier, 1.25)
        
        # Star priority
        if self.star_priority and base_score >= 75:
            max_bid *= 1.1
        
        # Ensure we can afford it
        remaining = self.budget_manager.get_remaining_budget(self.team)
        max_bid = min(max_bid, remaining * 0.4)  # Don't spend more than 40% of remaining on one player
        
        return round(max_bid, 2)
    
    def get_next_bid(self, player: Dict, current_price: float) -> Optional[float]:
        """
        Get next bid amount for a player.
        
        Returns:
            Bid amount or None if not bidding
        """
        if not self.should_bid(player, current_price):
            return None
        
        max_bid = self.calculate_max_bid(player)
        next_bid = current_price + 0.5  # Minimum increment
        
        if next_bid > max_bid:
            return None
        
        # Check if we can afford it
        valid, _ = self.budget_manager.validate_bid(self.team, next_bid)
        if not valid:
            return None
        
        return round(next_bid, 2)
    
    def record_acquisition(self, player: Dict, price: float):
        """Record that we acquired a player"""
        position = player.get('POS', '').upper().strip()
        self._update_position_need(position)
        self.budget_manager.record_acquisition(self.team, player, price)


class AIBidderPool:
    """Manages multiple AI bidders"""
    
    def __init__(self):
        self.bidders: Dict[str, AIBidder] = {}
    
    def add_bidder(self, team: str, strategy: BiddingStrategy, budget_manager, valuations: Dict):
        """Add an AI bidder to the pool"""
        self.bidders[team] = AIBidder(team, strategy, budget_manager, valuations)
    
    def get_bidder(self, team: str) -> Optional[AIBidder]:
        """Get bidder for a team"""
        return self.bidders.get(team)
    
    def get_interested_bidders(self, player: Dict, current_price: float) -> List[str]:
        """Get list of AI teams interested in bidding"""
        interested = []
        for team, bidder in self.bidders.items():
            if bidder.should_bid(player, current_price):
                interested.append(team)
        return interested
    
    def get_next_bids(self, player: Dict, current_price: float) -> Dict[str, float]:
        """Get next bid from each interested AI bidder"""
        bids = {}
        for team, bidder in self.bidders.items():
            next_bid = bidder.get_next_bid(player, current_price)
            if next_bid is not None:
                bids[team] = next_bid
        return bids
