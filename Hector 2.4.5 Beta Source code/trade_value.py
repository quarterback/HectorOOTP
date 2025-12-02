# Trade Value Calculator
# Calculates a composite Trade Value score (1-100) for every player

# Position scarcity multipliers - scarce positions are more valuable
POSITION_SCARCITY = {
    "C": 1.15,
    "SS": 1.12,
    "CF": 1.10,
    "SP": 1.08,
    "2B": 1.05,
    "3B": 1.05,
    "RP": 0.95,
    "CL": 0.95,  # Treat CL same as RP
    "LF": 0.95,
    "RF": 0.95,
    "1B": 0.90,
    "DH": 0.85,
}

# Age multipliers for future value calculation
AGE_MULTIPLIERS = {
    "23_or_younger": 1.3,
    "24_25": 1.15,
    "26_27": 1.0,
    "28_29": 0.85,
    "30_32": 0.6,
    "33_plus": 0.4,
}

# Trade Value Tiers
TRADE_VALUE_TIERS = {
    "Elite": {"min": 80, "max": 100, "icon": "💎", "description": "Franchise cornerstones, untouchable"},
    "Star": {"min": 65, "max": 79, "icon": "⭐", "description": "High-end starters, cost a lot to acquire"},
    "Solid": {"min": 50, "max": 64, "icon": "✅", "description": "Quality regulars, good trade chips"},
    "Average": {"min": 35, "max": 49, "icon": "📊", "description": "Role players, depth pieces"},
    "Below Average": {"min": 20, "max": 34, "icon": "📉", "description": "Marginal value, throw-ins"},
    "Minimal": {"min": 1, "max": 19, "icon": "❌", "description": "Replacement level or worse"},
}

# League average $/WAR (used for surplus value calculation)
LEAGUE_AVG_DOLLAR_PER_WAR = 8.0  # In millions, typical MLB value


def parse_number(value):
    """Parse numeric value, handling '-' and empty strings"""
    if not value or value == "-" or value == "":
        return 0.0
    try:
        val = str(value).replace(",", "").strip()
        # Handle star ratings
        if "Stars" in val:
            return float(val.split()[0])
        return float(val)
    except (ValueError, AttributeError):
        return 0.0


def get_age_multiplier(age):
    """Get age multiplier for future value calculation"""
    try:
        age = int(age)
    except (ValueError, TypeError):
        return 0.5  # Default for invalid age
    
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


def get_position_scarcity(position):
    """Get position scarcity multiplier"""
    pos = str(position).upper()
    return POSITION_SCARCITY.get(pos, 1.0)


def get_trade_value_tier(trade_value):
    """Get the tier information for a given trade value score"""
    for tier_name, tier_info in TRADE_VALUE_TIERS.items():
        if tier_info["min"] <= trade_value <= tier_info["max"]:
            return {
                "name": tier_name,
                "icon": tier_info["icon"],
                "description": tier_info["description"]
            }
    return {"name": "Unknown", "icon": "?", "description": "Unknown tier"}


def calculate_current_production_score(player, player_type="batter"):
    """
    Calculate current production score (0-40 points) based on stat score or WAR
    40% weight in final trade value
    """
    # Get WAR based on player type
    if player_type == "pitcher":
        war = parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
    else:
        war = parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))
    
    # Try to use the existing score system if available
    scores = player.get("Scores", {})
    total_score = scores.get("total", 0)
    
    # Normalize WAR to 0-40 scale
    # WAR range: -2 to 8 for elite players
    war_normalized = max(0, min(40, ((war + 2) / 10) * 40))
    
    # Also consider the calculated score (normalized to 0-40)
    # Typical scores range from 0-200, normalize to 0-40
    score_normalized = min(40, (total_score / 200) * 40)
    
    # Use the average of both for a more balanced view
    return round((war_normalized + score_normalized) / 2, 2)


def calculate_future_value_score(player):
    """
    Calculate future value score (0-30 points) based on POT and age
    30% weight in final trade value
    """
    pot = parse_number(player.get("POT", 0))
    age = player.get("Age", 30)
    
    age_multiplier = get_age_multiplier(age)
    
    # POT is typically on 1-5 star scale or 0-80 scale
    # Normalize to 0-30 scale
    if pot <= 10:  # Likely star rating (1-5 or 1-10)
        pot_normalized = (pot / 10) * 30
    else:  # Likely 0-80 scale
        pot_normalized = (pot / 80) * 30
    
    future_value = pot_normalized * age_multiplier
    return round(min(30, max(0, future_value)), 2)


def calculate_contract_value_score(player):
    """
    Calculate contract value score (0-20 points) based on years left and salary
    20% weight in final trade value
    More years of control at low cost = more value
    """
    yl = parse_number(player.get("YL", 0))
    salary = parse_number(player.get("SLR", 0))
    
    # Years left contribution (0-10 points)
    # More years = more value, capped at 6 years
    yl_score = min(10, yl * 1.67)
    
    # Salary efficiency (0-10 points)
    # Lower salary = more value
    # Typical range: 0-30 million
    if salary <= 0:
        salary_score = 10  # No salary = max value
    elif salary <= 1:
        salary_score = 9
    elif salary <= 5:
        salary_score = 7
    elif salary <= 10:
        salary_score = 5
    elif salary <= 20:
        salary_score = 3
    else:
        salary_score = 1
    
    return round(yl_score + salary_score, 2)


def calculate_position_scarcity_score(player):
    """
    Calculate position scarcity score (0-10 points)
    10% weight in final trade value
    """
    pos = player.get("POS", "")
    scarcity_mult = get_position_scarcity(pos)
    
    # Base score of 5, modified by scarcity
    # Range: 0.85x to 1.15x gives range of ~4.25 to 5.75, then scaled
    base_score = 5 * scarcity_mult
    
    # Scale to 0-10 range
    # Min would be 4.25 (DH), max would be 5.75 (C)
    # Rescale to 0-10
    scaled = ((base_score - 4.25) / (5.75 - 4.25)) * 10
    return round(max(0, min(10, scaled)), 2)


def calculate_trade_value(player, player_type="batter"):
    """
    Calculate composite Trade Value score (1-100) for a player
    
    Components:
    - Current Production: 40% weight (0-40 points)
    - Future Value: 30% weight (0-30 points)  
    - Contract Value: 20% weight (0-20 points)
    - Position Scarcity: 10% weight (0-10 points)
    
    Returns dict with trade value and component breakdown
    """
    current_prod = calculate_current_production_score(player, player_type)
    future_value = calculate_future_value_score(player)
    contract_value = calculate_contract_value_score(player)
    position_scarcity = calculate_position_scarcity_score(player)
    
    # Total trade value (scaled 1-100)
    raw_total = current_prod + future_value + contract_value + position_scarcity
    trade_value = max(1, min(100, round(raw_total)))
    
    tier = get_trade_value_tier(trade_value)
    
    return {
        "trade_value": trade_value,
        "current_production": current_prod,
        "future_value": future_value,
        "contract_value": contract_value,
        "position_scarcity": position_scarcity,
        "tier": tier["name"],
        "tier_icon": tier["icon"],
        "tier_description": tier["description"]
    }


def calculate_dollars_per_war(player, player_type="batter"):
    """
    Calculate $/WAR (dollars per WAR)
    Lower is better
    
    Returns tuple (dollars_per_war, display_string)
    """
    if player_type == "pitcher":
        war = parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
    else:
        war = parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))
    
    salary = parse_number(player.get("SLR", 0))
    
    if war <= 0:
        return float('inf'), "∞" if salary > 0 else "N/A"
    
    dollars_per_war = salary / war
    return dollars_per_war, f"${dollars_per_war:.1f}M"


def calculate_surplus_value(player, player_type="batter"):
    """
    Calculate surplus value: (WAR * league_avg_$/WAR) - salary
    Positive = surplus value (good deal)
    Negative = overpay
    
    Returns tuple (surplus_value, display_string)
    """
    if player_type == "pitcher":
        war = parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
    else:
        war = parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))
    
    salary = parse_number(player.get("SLR", 0))
    
    expected_value = war * LEAGUE_AVG_DOLLAR_PER_WAR
    surplus = expected_value - salary
    
    if surplus >= 0:
        return surplus, f"+${surplus:.1f}M"
    else:
        return surplus, f"-${abs(surplus):.1f}M"


def get_contract_category(player, player_type="batter"):
    """
    Categorize player's contract value
    
    Categories:
    - 💰 Surplus: WAR ≥ 2.0 AND (low salary OR YL ≤ 2)
    - ⚠️ Fair Value: $/WAR within normal range
    - 🚨 Albatross: High salary, low WAR (< 1.0), YL ≥ 2
    - 🎯 Arb Target: Age 25-27, good stats, YL ≤ 3
    
    Returns tuple (category_name, icon, color)
    """
    if player_type == "pitcher":
        war = parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
    else:
        war = parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))
    
    salary = parse_number(player.get("SLR", 0))
    yl = parse_number(player.get("YL", 0))
    
    try:
        age = int(player.get("Age", 0))
    except (ValueError, TypeError):
        age = 0
    
    # Check for Albatross first (high salary, low production)
    if salary >= 10 and war < 1.0 and yl >= 2:
        return ("Albatross", "🚨", "#ff6b6b")
    
    # Check for Arb Target (young with good stats and team control)
    if 25 <= age <= 27 and war >= 1.5 and yl <= 3:
        return ("Arb Target", "🎯", "#4dabf7")
    
    # Check for Surplus value
    if war >= 2.0 and (salary <= 5 or yl <= 2):
        return ("Surplus", "💰", "#51cf66")
    
    # Default to Fair Value
    return ("Fair Value", "⚠️", "#ffd43b")
