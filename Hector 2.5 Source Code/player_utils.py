# Shared utility functions for player analytics
# Common functions used across percentiles, hidden_gems, archetypes, and roster_builder

from trade_value import parse_number


# Rating scale detection threshold
# Values <= this threshold are considered star scale (1-5 or 1-10)
# Values > this threshold are considered 20-80 scale
RATING_SCALE_THRESHOLD = 10

# Star to 20-80 scale conversion factor
# Star ratings (1-5 scale) are converted to approximately 20-80 scale
# by multiplying by 16 (so 5 stars ≈ 80, 1 star ≈ 16)
STAR_TO_RATING_SCALE = 16


def parse_star_rating(val):
    """
    Convert star rating or numeric value to float.
    
    Handles formats:
    - "3.5 Stars" -> 3.5
    - "3.5" -> 3.5
    - "65" -> 65.0
    - "12.5%" -> 12.5 (percentage values)
    - None, "", "-" -> 0.0
    """
    if not val:
        return 0.0
    val = str(val).strip()
    if "Stars" in val:
        try:
            return float(val.split()[0])
        except (ValueError, IndexError):
            return 0.0
    # Handle percentage values like "12.5%"
    if "%" in val:
        try:
            return float(val.replace("%", ""))
        except ValueError:
            return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0


def get_age(player):
    """
    Get player age as integer.
    
    Returns 0 if age cannot be parsed.
    """
    try:
        return int(player.get("Age", 0))
    except (ValueError, TypeError):
        return 0


def get_war(player, player_type="batter"):
    """
    Get WAR value for a player.
    
    Args:
        player: Player dict
        player_type: "batter" or "pitcher"
    
    Returns WAR as float, 0.0 if not available.
    """
    if player_type == "pitcher":
        return parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
    return parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))


def normalize_rating(ovr):
    """
    Normalize OVR rating to 20-80 scale.
    
    If the value is <= RATING_SCALE_THRESHOLD, it's assumed to be a star rating 
    (1-5 or 1-10 scale) and is converted to approximately 20-80 scale.
    
    Args:
        ovr: OVR value (star scale or 20-80 scale)
    
    Returns:
        Rating normalized to 20-80 scale
    """
    if is_star_scale(ovr):
        return ovr * STAR_TO_RATING_SCALE
    return ovr


def is_star_scale(val):
    """
    Determine if a rating value is on star scale (1-5 or 1-10) vs 20-80 scale.
    
    Values <= RATING_SCALE_THRESHOLD are considered star scale.
    """
    return val <= RATING_SCALE_THRESHOLD


def normalize_to_100(value, min_val, max_val):
    """
    Normalize any value to 0-100 scale.
    
    Args:
        value: The value to normalize
        min_val: Minimum expected value
        max_val: Maximum expected value
    
    Returns:
        Value scaled to 0-100 range, clamped to [0, 100]
    """
    if max_val <= min_val:
        return 0.0
    
    normalized = ((value - min_val) / (max_val - min_val)) * 100
    return max(0.0, min(100.0, normalized))


def apply_scouting_uncertainty(player, uncertainty_level=0.1):
    """
    Apply random noise to potential ratings to simulate scouting uncertainty.
    
    High-potential prospects have more variance in their true ability.
    This function returns a modified POT value with noise applied.
    
    Args:
        player: Player dict
        uncertainty_level: Base uncertainty factor (0-1). Default 0.1 = 10% variance.
                          Higher values increase variance.
    
    Returns:
        Modified potential value with noise applied
    """
    import random
    
    pot = parse_star_rating(player.get("POT", "0"))
    ovr = parse_star_rating(player.get("OVR", "0"))
    age = get_age(player)
    
    if pot <= 0:
        return pot
    
    # Younger players and those with larger upside gaps have more uncertainty
    age_factor = max(0.5, (30 - age) / 10) if age < 30 else 0.3
    upside_gap = pot - ovr
    gap_factor = 1.0 + (upside_gap / 20) if upside_gap > 0 else 1.0
    
    # Calculate total uncertainty
    total_uncertainty = uncertainty_level * age_factor * gap_factor
    
    # Apply gaussian noise
    noise = random.gauss(0, total_uncertainty)
    
    # Scale noise to rating scale
    if is_star_scale(pot):
        noise_scaled = noise * 0.5  # 0.5 star variance at base uncertainty
    else:
        noise_scaled = noise * 10  # 10 point variance at base uncertainty on 20-80 scale
    
    return max(0, pot + noise_scaled)


def get_games_played(player, player_type="batter"):
    """
    Get games played for sample size determination.
    
    Args:
        player: Player dict
        player_type: "batter" or "pitcher"
    
    Returns:
        Games played as int, 0 if not available
    """
    if player_type == "pitcher":
        # For pitchers, check G (games) or GS (games started)
        g = parse_number(player.get("G", 0))
        if g > 0:
            return int(g)
        return int(parse_number(player.get("GS", 0)))
    else:
        return int(parse_number(player.get("G", 0)))


def get_innings_pitched(player):
    """
    Get innings pitched for pitcher sample size determination.
    
    Args:
        player: Player dict
    
    Returns:
        IP as float, 0.0 if not available
    """
    return parse_number(player.get("IP", 0))
