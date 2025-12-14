"""
Player valuation for auction system.
Uses existing Portal scoring systems to calculate auction values.
"""

from typing import Dict, Optional
import sys
from pathlib import Path

# Import existing Portal modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from batters import calculate_batter_score
from pitchers import calculate_score as calculate_pitcher_score
from trade_value import POSITION_SCARCITY, AGE_MULTIPLIERS


def parse_rating(value) -> float:
    """Parse a rating value from player data"""
    if value is None:
        return 0.0
    val = str(value).strip()
    if val == "-" or val == "" or val == " ":
        return 0.0
    # Remove "Stars" suffix if present
    val = val.replace(" Stars", "").replace("Stars", "").strip()
    try:
        return float(val)
    except ValueError:
        return 0.0


def get_age_multiplier(age: int) -> float:
    """Get age multiplier for valuation"""
    if age <= 23:
        return AGE_MULTIPLIERS["23_or_younger"]
    elif age <= 25:
        return AGE_MULTIPLIERS["24_25"]
    elif age <= 27:
        return AGE_MULTIPLIERS["26_27"]
    elif age <= 29:
        return AGE_MULTIPLIERS["28_29"]
    elif age <= 32:
        return AGE_MULTIPLIERS["30_32"]
    else:
        return AGE_MULTIPLIERS["33_plus"]


def get_position_scarcity(position: str) -> float:
    """Get position scarcity multiplier"""
    pos = position.upper().strip()
    return POSITION_SCARCITY.get(pos, 1.0)


def calculate_player_valuation(player: Dict, section_weights: Dict, 
                                batter_section_weights: Dict,
                                base_budget: float = 100.0) -> Dict:
    """
    Calculate auction valuation for a player.
    
    Args:
        player: Player dictionary with all stats/ratings
        section_weights: Pitcher scoring weights
        batter_section_weights: Batter scoring weights  
        base_budget: Base budget to scale valuations (default 100M)
        
    Returns:
        Dictionary with valuation details:
        - base_value: Base score-based value
        - position_adjusted: After position scarcity adjustment
        - age_adjusted: After age adjustment
        - suggested_price: Final suggested auction price
        - max_price: Maximum reasonable price (suggested * 1.2)
    """
    position = player.get('POS', '').upper().strip()
    age = int(parse_rating(player.get('Age', 25)))
    
    # Determine if pitcher or batter
    is_pitcher = position in {'SP', 'RP', 'CL', 'P'}
    
    # Calculate base score using existing Portal systems
    if is_pitcher:
        base_score = calculate_pitcher_score(player, section_weights)
    else:
        base_score = calculate_batter_score(player, batter_section_weights)
    
    # Normalize score to 0-100 range if needed
    # Assuming scores are already in reasonable range, cap at 100
    normalized_score = min(base_score, 100.0)
    
    # Base value as percentage of budget (score of 100 = 20% of budget)
    base_value = (normalized_score / 100.0) * (base_budget * 0.20)
    
    # Apply position scarcity
    pos_multiplier = get_position_scarcity(position)
    position_adjusted = base_value * pos_multiplier
    
    # Apply age adjustments
    age_multiplier = get_age_multiplier(age)
    age_adjusted = position_adjusted * age_multiplier
    
    # Calculate suggested price (conservative estimate)
    suggested_price = max(0.5, age_adjusted)  # Minimum $0.5M
    
    # Calculate maximum price (aggressive bidding limit)
    max_price = suggested_price * 1.2
    
    return {
        'base_value': round(base_value, 2),
        'position_adjusted': round(position_adjusted, 2),
        'age_adjusted': round(age_adjusted, 2),
        'suggested_price': round(suggested_price, 2),
        'max_price': round(max_price, 2),
        'base_score': round(normalized_score, 2),
        'position_multiplier': pos_multiplier,
        'age_multiplier': age_multiplier,
    }


def calculate_all_valuations(players: list, section_weights: Dict,
                             batter_section_weights: Dict,
                             base_budget: float = 100.0) -> Dict[str, Dict]:
    """
    Calculate valuations for all players.
    
    Returns:
        Dictionary mapping player name to valuation dict
    """
    valuations = {}
    for player in players:
        name = player.get('Name', '')
        if name:
            valuations[name] = calculate_player_valuation(
                player, section_weights, batter_section_weights, base_budget
            )
    return valuations


def get_suggested_starting_price(valuation: Dict) -> float:
    """
    Get suggested starting price for auction (typically 30-40% of suggested price).
    """
    suggested = valuation.get('suggested_price', 1.0)
    return round(max(0.5, suggested * 0.35), 2)


def format_price(price: float) -> str:
    """Format price for display"""
    return f"${price:.2f}M"
