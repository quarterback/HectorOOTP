"""
Core auction engine.
Manages auction state and bidding flow.
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Constants
DEFAULT_MIN_BID_INCREMENT = 0.5  # $0.5M minimum increment
DEFAULT_AUTO_ADVANCE_DELAY = 3.0  # Seconds to wait before auto-advancing


class AuctionState(Enum):
    """Auction state"""
    SETUP = "setup"              # Pre-auction setup
    IN_PROGRESS = "in_progress"  # Auction running
    PAUSED = "paused"            # Auction paused
    COMPLETED = "completed"      # Auction finished


class BidType(Enum):
    """Type of bid"""
    HUMAN = "human"
    AI = "ai"


@dataclass
class Bid:
    """Represents a single bid"""
    team: str
    amount: float
    bid_type: BidType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AuctionResult:
    """Result of a player auction"""
    player: Dict
    winning_team: str
    final_price: float
    num_bids: int
    starting_price: float
    bid_history: List[Bid] = field(default_factory=list)


class AuctionEngine:
    """Core auction engine managing bidding flow"""
    
    def __init__(self, budget_manager, ai_bidder_pool):
        self.budget_manager = budget_manager
        self.ai_bidder_pool = ai_bidder_pool
        
        self.state = AuctionState.SETUP
        self.players: List[Dict] = []
        self.current_player_index: int = 0
        self.current_player: Optional[Dict] = None
        self.current_price: float = 0.0
        self.current_high_bidder: Optional[str] = None
        self.current_bid_type: Optional[BidType] = None
        self.bid_history: List[Bid] = []
        
        self.results: List[AuctionResult] = []
        self.unsold_players: List[Dict] = []
        
        # Auction parameters (configurable)
        self.min_bid_increment: float = DEFAULT_MIN_BID_INCREMENT
        self.auto_advance_delay: float = DEFAULT_AUTO_ADVANCE_DELAY
        
        # Callbacks for UI updates
        self.on_bid_callback: Optional[Callable] = None
        self.on_player_sold_callback: Optional[Callable] = None
        self.on_auction_complete_callback: Optional[Callable] = None
    
    def initialize_auction(self, players: List[Dict], starting_prices: Dict[str, float]):
        """
        Initialize auction with players and starting prices.
        
        Args:
            players: List of player dictionaries
            starting_prices: Dictionary mapping player name to starting price
        """
        self.players = players.copy()
        self.current_player_index = 0
        self.results = []
        self.unsold_players = []
        self.starting_prices = starting_prices
        self.state = AuctionState.SETUP
    
    def start_auction(self):
        """Start the auction"""
        if not self.players:
            raise ValueError("No players to auction")
        
        self.state = AuctionState.IN_PROGRESS
        self._advance_to_next_player()
    
    def _advance_to_next_player(self):
        """Move to next player in auction"""
        if self.current_player_index >= len(self.players):
            # Auction complete
            self.state = AuctionState.COMPLETED
            self.current_player = None
            if self.on_auction_complete_callback:
                self.on_auction_complete_callback()
            return
        
        self.current_player = self.players[self.current_player_index]
        player_name = self.current_player.get('Name', '')
        self.current_price = self.starting_prices.get(player_name, 1.0)
        self.current_high_bidder = None
        self.current_bid_type = None
        self.bid_history = []
    
    def place_bid(self, team: str, amount: float, bid_type: BidType = BidType.HUMAN) -> Tuple[bool, Optional[str]]:
        """
        Place a bid for the current player.
        
        Args:
            team: Team placing the bid
            amount: Bid amount
            bid_type: Type of bid (human or AI)
            
        Returns:
            (success, error_message)
        """
        if self.state != AuctionState.IN_PROGRESS:
            return False, "Auction is not in progress"
        
        if not self.current_player:
            return False, "No active player"
        
        # Validate bid amount
        min_next_bid = self.current_price + self.min_bid_increment
        if amount < min_next_bid:
            return False, f"Bid must be at least ${min_next_bid:.2f}M"
        
        # Validate budget
        valid, error = self.budget_manager.validate_bid(team, amount)
        if not valid:
            return False, error
        
        # Record bid
        bid = Bid(team=team, amount=amount, bid_type=bid_type)
        self.bid_history.append(bid)
        self.current_price = amount
        self.current_high_bidder = team
        self.current_bid_type = bid_type
        
        # Notify callback
        if self.on_bid_callback:
            self.on_bid_callback(bid, self.current_player)
        
        return True, None
    
    def process_ai_bids(self) -> List[Bid]:
        """
        Process AI bids for current player.
        Returns list of AI bids that were placed.
        """
        if not self.current_player:
            return []
        
        ai_bids = []
        
        # Get all AI bids
        next_bids = self.ai_bidder_pool.get_next_bids(self.current_player, self.current_price)
        
        # Find highest AI bid
        if next_bids:
            highest_ai_team = max(next_bids.items(), key=lambda x: x[1])
            team, amount = highest_ai_team
            
            # Place the highest AI bid
            success, _ = self.place_bid(team, amount, BidType.AI)
            if success:
                ai_bids.append(self.bid_history[-1])
        
        return ai_bids
    
    def sell_current_player(self) -> Optional[AuctionResult]:
        """
        Sell current player to highest bidder and advance to next player.
        
        Returns:
            AuctionResult if player was sold, None if no bids
        """
        if not self.current_player:
            return None
        
        player_name = self.current_player.get('Name', '')
        starting_price = self.starting_prices.get(player_name, 1.0)
        
        if self.current_high_bidder:
            # Player sold
            result = AuctionResult(
                player=self.current_player,
                winning_team=self.current_high_bidder,
                final_price=self.current_price,
                num_bids=len(self.bid_history),
                starting_price=starting_price,
                bid_history=self.bid_history.copy()
            )
            
            # Record acquisition in budget manager
            self.budget_manager.record_acquisition(
                self.current_high_bidder,
                self.current_player,
                self.current_price
            )
            
            # Update AI bidder if applicable
            ai_bidder = self.ai_bidder_pool.get_bidder(self.current_high_bidder)
            if ai_bidder:
                ai_bidder.record_acquisition(self.current_player, self.current_price)
            
            self.results.append(result)
            
            if self.on_player_sold_callback:
                self.on_player_sold_callback(result)
            
        else:
            # No bids - player unsold
            self.unsold_players.append(self.current_player)
            result = None
        
        # Move to next player
        self.current_player_index += 1
        self._advance_to_next_player()
        
        return result
    
    def pass_on_player(self):
        """Pass on current player (no sale, move to next)"""
        if self.current_player:
            self.unsold_players.append(self.current_player)
        
        self.current_player_index += 1
        self._advance_to_next_player()
    
    def pause_auction(self):
        """Pause the auction"""
        if self.state == AuctionState.IN_PROGRESS:
            self.state = AuctionState.PAUSED
    
    def resume_auction(self):
        """Resume a paused auction"""
        if self.state == AuctionState.PAUSED:
            self.state = AuctionState.IN_PROGRESS
    
    def get_current_player_info(self) -> Optional[Dict]:
        """Get info about current player being auctioned"""
        if not self.current_player:
            return None
        
        return {
            'player': self.current_player,
            'current_price': self.current_price,
            'high_bidder': self.current_high_bidder,
            'bid_type': self.current_bid_type,
            'num_bids': len(self.bid_history),
            'starting_price': self.starting_prices.get(self.current_player.get('Name', ''), 1.0),
            'bid_history': self.bid_history.copy()
        }
    
    def get_progress(self) -> Dict:
        """Get auction progress info"""
        return {
            'state': self.state,
            'current_index': self.current_player_index,
            'total_players': len(self.players),
            'players_sold': len(self.results),
            'players_unsold': len(self.unsold_players),
            'players_remaining': len(self.players) - self.current_player_index
        }
    
    def get_results_summary(self) -> Dict:
        """Get summary of auction results"""
        total_spent = sum(r.final_price for r in self.results)
        avg_price = total_spent / len(self.results) if self.results else 0
        
        return {
            'total_players_sold': len(self.results),
            'total_players_unsold': len(self.unsold_players),
            'total_amount_spent': total_spent,
            'average_price': avg_price,
            'results': self.results,
            'unsold': self.unsold_players
        }
