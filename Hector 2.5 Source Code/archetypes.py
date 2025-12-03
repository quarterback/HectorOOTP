# Franchise Archetypes
# Filter and find players that fit desired team-building philosophies

from trade_value import parse_number, parse_salary, parse_years_left
from player_utils import parse_star_rating, get_age, get_war, is_star_scale


# Archetype Definitions
ARCHETYPES = {
    "speed_defense": {
        "icon": "🏃",
        "name": "Speed & Defense",
        "description": "High speed, elite defense, contact-oriented",
        "color": "#4dabf7",
        "player_types": ["batter"],
    },
    "mashers": {
        "icon": "💪",
        "name": "Mashers",
        "description": "High power, high ISO, accept higher K%",
        "color": "#ff6b6b",
        "player_types": ["batter"],
    },
    "moneyball": {
        "icon": "👁️",
        "name": "Moneyball (OBP Focus)",
        "description": "High eye, high BB%, value OBP over AVG",
        "color": "#51cf66",
        "player_types": ["batter"],
    },
    "youth_movement": {
        "icon": "🌱",
        "name": "Youth Movement",
        "description": "Age ≤25, high potential, cheap contracts",
        "color": "#9775fa",
        "player_types": ["batter", "pitcher"],
    },
    "win_now": {
        "icon": "🏆",
        "name": "Win Now",
        "description": "High OVR, proven production, prime years",
        "color": "#ffd43b",
        "player_types": ["batter", "pitcher"],
    },
    "budget_build": {
        "icon": "💰",
        "name": "Budget Build",
        "description": "High WAR/$, cheap contracts, good value",
        "color": "#ff922b",
        "player_types": ["batter", "pitcher"],
    },
    "balanced": {
        "icon": "⚖️",
        "name": "Balanced",
        "description": "No glaring weaknesses, all ratings ≥45",
        "color": "#ced4da",
        "player_types": ["batter", "pitcher"],
    },
    "chaos_ball": {
        "icon": "🎲",
        "name": "Chaos Ball",
        "description": "High variance boom-or-bust, high K% + high ISO",
        "color": "#e64980",
        "player_types": ["batter"],
    },
    "small_ball": {
        "icon": "⚾",
        "name": "Small Ball",
        "description": "Contact, bunting, manufacturing runs",
        "color": "#74c0fc",
        "player_types": ["batter"],
    },
    "ace_hunter": {
        "icon": "🎯",
        "name": "Ace Hunter",
        "description": "Build around elite SP (OVR 70+), budget elsewhere",
        "color": "#da77f2",
        "player_types": ["pitcher"],
    },
    "bullpen_first": {
        "icon": "🔥",
        "name": "Bullpen-First",
        "description": "Elite relievers over rotation",
        "color": "#ffa94d",
        "player_types": ["pitcher"],
    },
    "platoon_army": {
        "icon": "🔄",
        "name": "Platoon Army",
        "description": "Maximize L/R platoon advantages",
        "color": "#63e6be",
        "player_types": ["batter"],
    },
    "launch_angle": {
        "icon": "🚀",
        "name": "Launch Angle Era",
        "description": "Three true outcomes - HR, BB, K",
        "color": "#f06595",
        "player_types": ["batter"],
    },
    "defense_wins": {
        "icon": "🛡️",
        "name": "Defense Wins",
        "description": "Elite defense priority, accept weaker bats",
        "color": "#748ffc",
        "player_types": ["batter"],
    },
    "prospect_pipeline": {
        "icon": "🌾",
        "name": "Prospect Pipeline",
        "description": "Perpetual rebuild, age ≤24, high potential",
        "color": "#8ce99a",
        "player_types": ["batter", "pitcher"],
    },
    "veteran_presence": {
        "icon": "👨‍🦳",
        "name": "Veteran Presence",
        "description": "Age 30+, proven track record, high OVR",
        "color": "#ffe066",
        "player_types": ["batter", "pitcher"],
    },
    "innings_eaters": {
        "icon": "🍽️",
        "name": "Innings Eaters",
        "description": "High stamina, durable pitchers",
        "color": "#a9e34b",
        "player_types": ["pitcher"],
    },
}


# Fit score thresholds
FIT_THRESHOLDS = {
    "perfect": {"min": 80, "max": 100, "label": "Perfect Fit", "color": "#51cf66"},
    "good": {"min": 60, "max": 79, "label": "Good Fit", "color": "#4dabf7"},
    "partial": {"min": 40, "max": 59, "label": "Partial Fit", "color": "#ffd43b"},
    "poor": {"min": 0, "max": 39, "label": "Not a Fit", "color": "#ff6b6b"},
}


def get_fit_label(score):
    """Get the fit label for a given score"""
    for key, threshold in FIT_THRESHOLDS.items():
        if threshold["min"] <= score <= threshold["max"]:
            return {
                "key": key,
                "label": threshold["label"],
                "color": threshold["color"],
            }
    return {"key": "poor", "label": "Not a Fit", "color": "#ff6b6b"}


def calculate_speed_defense_fit(player):
    """
    Speed & Defense archetype:
    - Target: High SPE (≥60), high STE (≥60), elite DEF
    - Batting: Prioritize CON over POW
    - Accept: Lower power, contact-oriented
    - Positions: Premium up the middle (C, 2B, SS, CF)
    """
    score = 0
    max_score = 100
    
    pos = player.get("POS", "")
    premium_positions = {"C", "2B", "SS", "CF"}
    
    # Speed (25 points)
    spe = parse_number(player.get("SPE", 0))
    if spe >= 70:
        score += 25
    elif spe >= 60:
        score += 20
    elif spe >= 50:
        score += 10
    
    # Stealing (15 points)
    ste = parse_number(player.get("STE", 0))
    if ste >= 70:
        score += 15
    elif ste >= 60:
        score += 12
    elif ste >= 50:
        score += 6
    
    # Defense (30 points) - check position-appropriate ratings
    if pos == "C":
        c_abi = parse_number(player.get("C ABI", 0))
        c_arm = parse_number(player.get("C ARM", 0))
        def_avg = (c_abi + c_arm) / 2
    elif pos in {"2B", "SS", "3B", "1B"}:
        if_rng = parse_number(player.get("IF RNG", 0))
        if_arm = parse_number(player.get("IF ARM", 0))
        if_err = parse_number(player.get("IF ERR", 0))
        def_avg = (if_rng + if_arm + if_err) / 3
    else:
        of_rng = parse_number(player.get("OF RNG", 0))
        of_arm = parse_number(player.get("OF ARM", 0))
        of_err = parse_number(player.get("OF ERR", 0))
        def_avg = (of_rng + of_arm + of_err) / 3
    
    if def_avg >= 65:
        score += 30
    elif def_avg >= 55:
        score += 22
    elif def_avg >= 45:
        score += 12
    
    # Contact over power (15 points)
    con = parse_number(player.get("CON", 0))
    pow_ = parse_number(player.get("POW", 0))
    if con >= 55 and con > pow_:
        score += 15
    elif con >= 50:
        score += 10
    
    # Position bonus (15 points)
    if pos in premium_positions:
        score += 15
    elif pos in {"3B", "LF", "RF"}:
        score += 5
    
    return min(score, max_score)


def calculate_mashers_fit(player):
    """
    Mashers archetype:
    - Target: High POW (≥60), high ISO (≥.180)
    - Accept: Higher K%, lower AVG
    - Positions: Corner bats (1B, 3B, LF, RF, DH)
    - Bonus: HR totals, SLG
    """
    score = 0
    max_score = 100
    
    pos = player.get("POS", "")
    corner_positions = {"1B", "3B", "LF", "RF", "DH"}
    
    # Power (35 points)
    pow_ = parse_number(player.get("POW", 0))
    if pow_ >= 70:
        score += 35
    elif pow_ >= 60:
        score += 28
    elif pow_ >= 50:
        score += 15
    
    # ISO (20 points)
    iso = parse_number(player.get("ISO", 0))
    if iso >= 0.250:
        score += 20
    elif iso >= 0.200:
        score += 16
    elif iso >= 0.180:
        score += 12
    elif iso >= 0.150:
        score += 6
    
    # SLG (15 points)
    slg = parse_number(player.get("SLG", 0))
    if slg >= 0.550:
        score += 15
    elif slg >= 0.500:
        score += 12
    elif slg >= 0.450:
        score += 8
    
    # Position bonus (15 points)
    if pos in corner_positions:
        score += 15
    elif pos in {"C", "2B"}:
        score += 8  # Some bonus for power at non-premium positions
    
    # Gap power (15 points)
    gap = parse_number(player.get("GAP", 0))
    if gap >= 60:
        score += 15
    elif gap >= 50:
        score += 10
    
    return min(score, max_score)


def calculate_moneyball_fit(player):
    """
    Moneyball (OBP Focus) archetype:
    - Target: High EYE (≥55), high BB% (≥10%), wOBA ≥.340
    - Value: OBP over AVG
    - Accept: Less speed, less power
    - Key stats: OBP, wOBA, BB%
    """
    score = 0
    max_score = 100
    
    # Eye (25 points)
    eye = parse_number(player.get("EYE", 0))
    if eye >= 70:
        score += 25
    elif eye >= 60:
        score += 20
    elif eye >= 55:
        score += 15
    elif eye >= 50:
        score += 8
    
    # BB% (25 points)
    bb_pct = parse_number(player.get("BB%", 0))
    if bb_pct >= 15:
        score += 25
    elif bb_pct >= 12:
        score += 20
    elif bb_pct >= 10:
        score += 15
    elif bb_pct >= 8:
        score += 8
    
    # OBP (25 points)
    obp = parse_number(player.get("OBP", 0))
    if obp >= 0.400:
        score += 25
    elif obp >= 0.370:
        score += 20
    elif obp >= 0.350:
        score += 15
    elif obp >= 0.330:
        score += 10
    
    # wOBA (25 points)
    woba = parse_number(player.get("wOBA", 0))
    if woba >= 0.400:
        score += 25
    elif woba >= 0.370:
        score += 20
    elif woba >= 0.340:
        score += 15
    elif woba >= 0.320:
        score += 10
    
    return min(score, max_score)


def calculate_youth_movement_fit(player, player_type="batter"):
    """
    Youth Movement archetype:
    - Target: Age ≤25
    - High POT (≥60 or 3.5+ stars)
    - POT > OVR by ≥10 (or 1.0+ stars)
    - Cheap contracts (pre-arb, arb)
    - Accept: Lower current production
    """
    score = 0
    max_score = 100
    
    age = get_age(player)
    
    # Age (30 points)
    if age <= 22:
        score += 30
    elif age <= 24:
        score += 25
    elif age <= 25:
        score += 20
    elif age <= 26:
        score += 10
    else:
        return 0  # Not a fit for youth movement
    
    # Potential (30 points)
    pot = parse_star_rating(player.get("POT", "0"))
    ovr = parse_star_rating(player.get("OVR", "0"))
    
    if is_star_scale(pot):  # Star scale
        if pot >= 4.5:
            score += 30
        elif pot >= 4.0:
            score += 24
        elif pot >= 3.5:
            score += 18
        elif pot >= 3.0:
            score += 10
    else:  # 20-80 scale
        if pot >= 70:
            score += 30
        elif pot >= 60:
            score += 24
        elif pot >= 55:
            score += 18
        elif pot >= 50:
            score += 10
    
    # Upside gap (25 points)
    gap = pot - ovr
    if is_star_scale(pot):  # Star scale
        if gap >= 1.5:
            score += 25
        elif gap >= 1.0:
            score += 20
        elif gap >= 0.5:
            score += 12
    else:  # 20-80 scale
        if gap >= 15:
            score += 25
        elif gap >= 10:
            score += 20
        elif gap >= 5:
            score += 12
    
    # Contract (15 points)
    yl_data = parse_years_left(player.get("YL", ""))
    status = yl_data.get("status", "unknown")
    
    if status == "pre_arb":
        score += 15
    elif status == "arbitration":
        score += 12
    else:
        salary = parse_salary(player.get("SLR", 0))
        if salary < 3:
            score += 8
    
    return min(score, max_score)


def calculate_win_now_fit(player, player_type="batter"):
    """
    Win Now archetype:
    - Target: High OVR (≥65 or 4.0+ stars)
    - High current stats (wRC+ ≥120, WAR ≥3)
    - Age 26-32 (prime years)
    - Ignore: Contract cost, future value
    """
    score = 0
    max_score = 100
    
    age = get_age(player)
    
    # Age - prime years (20 points)
    if 26 <= age <= 30:
        score += 20
    elif 24 <= age <= 32:
        score += 15
    elif age <= 33:
        score += 10
    elif age <= 35:
        score += 5
    
    # OVR (35 points)
    ovr = parse_star_rating(player.get("OVR", "0"))
    if is_star_scale(ovr):  # Star scale
        if ovr >= 4.5:
            score += 35
        elif ovr >= 4.0:
            score += 30
        elif ovr >= 3.5:
            score += 25
        elif ovr >= 3.0:
            score += 15
    else:  # 20-80 scale
        if ovr >= 75:
            score += 35
        elif ovr >= 70:
            score += 30
        elif ovr >= 65:
            score += 25
        elif ovr >= 60:
            score += 15
    
    # Current production (45 points)
    if player_type == "batter":
        wrc_plus = parse_number(player.get("wRC+", 0))
        war = parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))
        
        if wrc_plus >= 140:
            score += 25
        elif wrc_plus >= 120:
            score += 20
        elif wrc_plus >= 110:
            score += 12
        elif wrc_plus >= 100:
            score += 6
        
        if war >= 5:
            score += 20
        elif war >= 4:
            score += 16
        elif war >= 3:
            score += 12
        elif war >= 2:
            score += 6
    else:
        era_plus = parse_number(player.get("ERA+", 0))
        war = parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
        
        if era_plus >= 140:
            score += 25
        elif era_plus >= 120:
            score += 20
        elif era_plus >= 110:
            score += 12
        elif era_plus >= 100:
            score += 6
        
        if war >= 4:
            score += 20
        elif war >= 3:
            score += 16
        elif war >= 2:
            score += 12
        elif war >= 1:
            score += 6
    
    return min(score, max_score)


def calculate_budget_build_fit(player, player_type="batter"):
    """
    Budget Build archetype:
    - Target: High WAR/$ ratio
    - Pre-arb or arbitration players
    - AAV < $5M with WAR ≥1.5
    - Expiring deals with production
    """
    score = 0
    max_score = 100
    
    # Get WAR and salary
    war = get_war(player, player_type)
    salary = parse_salary(player.get("SLR", 0))
    
    # WAR/$ ratio (40 points)
    if salary > 0:
        war_per_dollar = war / salary
        if war_per_dollar >= 2.0:
            score += 40
        elif war_per_dollar >= 1.5:
            score += 32
        elif war_per_dollar >= 1.0:
            score += 24
        elif war_per_dollar >= 0.5:
            score += 12
    elif war >= 1.0:
        score += 40  # Free production!
    
    # Contract status (25 points)
    yl_data = parse_years_left(player.get("YL", ""))
    status = yl_data.get("status", "unknown")
    
    if status == "pre_arb":
        score += 25
    elif status == "arbitration":
        score += 20
    else:
        years_left = yl_data.get("years", 99)
        if years_left <= 1:
            score += 15  # Expiring deal
        elif years_left <= 2:
            score += 10
    
    # Low AAV (20 points)
    if salary < 1:
        score += 20
    elif salary < 3:
        score += 16
    elif salary < 5:
        score += 12
    elif salary < 8:
        score += 6
    
    # Minimum production (15 points)
    if war >= 3:
        score += 15
    elif war >= 2:
        score += 12
    elif war >= 1.5:
        score += 9
    elif war >= 1.0:
        score += 5
    
    return min(score, max_score)


def calculate_balanced_fit(player, player_type="batter"):
    """
    Balanced archetype:
    - No glaring weaknesses
    - All ratings ≥45
    - Mix of skills
    - Average or better at everything
    """
    score = 0
    max_score = 100
    
    if player_type == "batter":
        ratings = {
            "CON": parse_number(player.get("CON", 0)),
            "GAP": parse_number(player.get("GAP", 0)),
            "POW": parse_number(player.get("POW", 0)),
            "EYE": parse_number(player.get("EYE", 0)),
            "SPE": parse_number(player.get("SPE", 0)),
        }
        
        # Count ratings at various thresholds
        above_45 = sum(1 for v in ratings.values() if v >= 45)
        above_50 = sum(1 for v in ratings.values() if v >= 50)
        above_55 = sum(1 for v in ratings.values() if v >= 55)
        
        # No weaknesses bonus (40 points)
        min_rating = min(ratings.values()) if ratings else 0
        if min_rating >= 50:
            score += 40
        elif min_rating >= 45:
            score += 30
        elif min_rating >= 40:
            score += 15
        
        # All-around ratings (40 points)
        if above_55 >= 4:
            score += 40
        elif above_50 >= 4:
            score += 32
        elif above_50 >= 3:
            score += 20
        elif above_45 >= 4:
            score += 12
        
        # Average rating bonus (20 points)
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
        if avg_rating >= 55:
            score += 20
        elif avg_rating >= 50:
            score += 15
        elif avg_rating >= 45:
            score += 10
    
    else:  # pitcher
        ratings = {
            "STU": parse_number(player.get("STU", 0)),
            "MOV": parse_number(player.get("MOV", 0)),
            "CON": parse_number(player.get("CON", 0)),
        }
        
        above_45 = sum(1 for v in ratings.values() if v >= 45)
        above_50 = sum(1 for v in ratings.values() if v >= 50)
        above_55 = sum(1 for v in ratings.values() if v >= 55)
        
        min_rating = min(ratings.values()) if ratings else 0
        if min_rating >= 50:
            score += 45
        elif min_rating >= 45:
            score += 35
        elif min_rating >= 40:
            score += 20
        
        if above_55 == 3:
            score += 40
        elif above_50 == 3:
            score += 32
        elif above_50 >= 2:
            score += 20
        elif above_45 == 3:
            score += 12
        
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
        if avg_rating >= 55:
            score += 15
        elif avg_rating >= 50:
            score += 10
        elif avg_rating >= 45:
            score += 5
    
    return min(score, max_score)


def calculate_chaos_ball_fit(player):
    """
    Chaos Ball archetype:
    - Target: High K% + high ISO (boom-or-bust)
    - Streaky players with high variance
    - Accept: Low AVG, high strikeouts
    """
    score = 0
    max_score = 100
    
    # Power (30 points)
    pow_ = parse_number(player.get("POW", 0))
    if pow_ >= 70:
        score += 30
    elif pow_ >= 60:
        score += 25
    elif pow_ >= 50:
        score += 15
    
    # ISO (25 points)
    iso = parse_number(player.get("ISO", 0))
    if iso >= 0.250:
        score += 25
    elif iso >= 0.200:
        score += 20
    elif iso >= 0.180:
        score += 15
    elif iso >= 0.150:
        score += 8
    
    # K% - higher is actually good for this archetype (20 points)
    k_pct = parse_number(player.get("K%", 0))
    if k_pct >= 30:
        score += 20
    elif k_pct >= 25:
        score += 15
    elif k_pct >= 20:
        score += 10
    
    # Low contact is acceptable (15 points if CON < 50)
    con = parse_number(player.get("CON", 0))
    if con < 40:
        score += 15
    elif con < 50:
        score += 10
    elif con < 55:
        score += 5
    
    # HR totals bonus (10 points)
    hr = parse_number(player.get("HR", 0))
    if hr >= 35:
        score += 10
    elif hr >= 25:
        score += 7
    elif hr >= 15:
        score += 3
    
    return min(score, max_score)


def calculate_small_ball_fit(player):
    """
    Small Ball archetype:
    - Target: High contact, bunting, manufacturing runs
    - Low K%, high STE, low POW, high CON
    - Emphasis on getting on base and moving runners
    """
    score = 0
    max_score = 100
    
    # Contact (30 points)
    con = parse_number(player.get("CON", 0))
    if con >= 70:
        score += 30
    elif con >= 60:
        score += 25
    elif con >= 55:
        score += 18
    elif con >= 50:
        score += 10
    
    # Speed (20 points)
    spe = parse_number(player.get("SPE", 0))
    if spe >= 65:
        score += 20
    elif spe >= 55:
        score += 15
    elif spe >= 45:
        score += 8
    
    # Stealing (20 points)
    ste = parse_number(player.get("STE", 0))
    if ste >= 65:
        score += 20
    elif ste >= 55:
        score += 15
    elif ste >= 45:
        score += 8
    
    # Low K% (15 points)
    k_pct = parse_number(player.get("K%", 0))
    if k_pct <= 10:
        score += 15
    elif k_pct <= 15:
        score += 12
    elif k_pct <= 20:
        score += 8
    elif k_pct <= 25:
        score += 4
    
    # Bunting ability (15 points) - use BUN if available, else estimate from CON/SPE
    bun = parse_number(player.get("BUN", 0))
    if bun >= 60:
        score += 15
    elif bun >= 50:
        score += 12
    elif bun >= 40:
        score += 8
    elif bun == 0 and con >= 55 and spe >= 50:
        score += 6  # Estimate based on attributes
    
    return min(score, max_score)


def calculate_ace_hunter_fit(player, player_type="pitcher"):
    """
    Ace Hunter archetype (pitchers only):
    - Target: Elite SP (OVR 70+ or 4.5+ stars)
    - Looking for true aces to build around
    """
    if player_type != "pitcher":
        return 0
    
    score = 0
    max_score = 100
    
    pos = player.get("POS", "")
    if pos != "SP":
        return 0  # Only SP qualify for ace
    
    # OVR (50 points) - needs to be elite
    ovr = parse_star_rating(player.get("OVR", "0"))
    if is_star_scale(ovr):  # Star scale
        if ovr >= 4.5:
            score += 50
        elif ovr >= 4.0:
            score += 40
        elif ovr >= 3.5:
            score += 25
        else:
            return 0  # Not ace material
    else:  # 20-80 scale
        if ovr >= 75:
            score += 50
        elif ovr >= 70:
            score += 40
        elif ovr >= 65:
            score += 25
        else:
            return 0  # Not ace material
    
    # Stuff (25 points)
    stu = parse_number(player.get("STU", 0))
    if stu >= 70:
        score += 25
    elif stu >= 65:
        score += 20
    elif stu >= 60:
        score += 15
    
    # Movement (15 points)
    mov = parse_number(player.get("MOV", 0))
    if mov >= 65:
        score += 15
    elif mov >= 60:
        score += 12
    elif mov >= 55:
        score += 8
    
    # Control (10 points)
    ctrl = parse_number(player.get("CON", 0))
    if ctrl >= 65:
        score += 10
    elif ctrl >= 60:
        score += 8
    elif ctrl >= 55:
        score += 5
    
    return min(score, max_score)


def calculate_bullpen_first_fit(player, player_type="pitcher"):
    """
    Bullpen-First archetype (pitchers only):
    - Target: Elite relievers (RP/CL)
    - High stuff, good late-inning potential
    """
    if player_type != "pitcher":
        return 0
    
    score = 0
    max_score = 100
    
    pos = player.get("POS", "")
    if pos not in ["RP", "CL"]:
        return 0  # Only relievers
    
    # OVR (35 points)
    ovr = parse_star_rating(player.get("OVR", "0"))
    if is_star_scale(ovr):
        if ovr >= 4.0:
            score += 35
        elif ovr >= 3.5:
            score += 28
        elif ovr >= 3.0:
            score += 20
        elif ovr >= 2.5:
            score += 12
    else:
        if ovr >= 70:
            score += 35
        elif ovr >= 65:
            score += 28
        elif ovr >= 60:
            score += 20
        elif ovr >= 55:
            score += 12
    
    # Stuff (30 points) - critical for relievers
    stu = parse_number(player.get("STU", 0))
    if stu >= 70:
        score += 30
    elif stu >= 65:
        score += 25
    elif stu >= 60:
        score += 18
    elif stu >= 55:
        score += 10
    
    # Movement (20 points)
    mov = parse_number(player.get("MOV", 0))
    if mov >= 65:
        score += 20
    elif mov >= 60:
        score += 16
    elif mov >= 55:
        score += 10
    
    # Closer role bonus (15 points)
    if pos == "CL":
        score += 15
    else:
        score += 5  # RP still counts
    
    return min(score, max_score)


def calculate_platoon_army_fit(player):
    """
    Platoon Army archetype:
    - Players with pronounced L/R splits
    - Best as platoon partners (L vs R advantage)
    - Accept: Not everyday players on their own
    """
    score = 0
    max_score = 100
    
    # Check handedness - switch hitters don't fit this archetype
    bats = player.get("B", "").upper()
    if bats == "S":
        return 0  # Switch hitters don't need platoons
    
    # OVR in platoon-friendly range - not stars, not scrubs (25 points)
    ovr = parse_star_rating(player.get("OVR", "0"))
    if is_star_scale(ovr):
        if 2.5 <= ovr <= 3.5:
            score += 25
        elif 2.0 <= ovr <= 4.0:
            score += 15
        elif ovr < 2.0 or ovr > 4.0:
            score += 5
    else:
        if 45 <= ovr <= 60:
            score += 25
        elif 40 <= ovr <= 65:
            score += 15
        else:
            score += 5
    
    # Good batting tool (25 points)
    con = parse_number(player.get("CON", 0))
    pow_ = parse_number(player.get("POW", 0))
    eye = parse_number(player.get("EYE", 0))
    
    best_tool = max(con, pow_, eye)
    if best_tool >= 60:
        score += 25
    elif best_tool >= 55:
        score += 20
    elif best_tool >= 50:
        score += 12
    
    # Check vL and vR splits if available (30 points)
    v_l = parse_number(player.get("vL", 0))
    v_r = parse_number(player.get("vR", 0))
    
    if v_l > 0 and v_r > 0:
        split_diff = abs(v_l - v_r)
        if split_diff >= 15:
            score += 30  # Big platoon advantage
        elif split_diff >= 10:
            score += 22
        elif split_diff >= 5:
            score += 12
    else:
        # No split data - estimate based on handedness
        # Left-handed batters typically have bigger splits
        if bats == "L":
            score += 15
        else:
            score += 10
    
    # Value as part-time player (20 points)
    salary = parse_salary(player.get("SLR", 0))
    if salary < 2:
        score += 20
    elif salary < 5:
        score += 15
    elif salary < 10:
        score += 8
    
    return min(score, max_score)


def calculate_launch_angle_fit(player):
    """
    Launch Angle Era archetype:
    - Three true outcomes only: HR, BB, K
    - High power, high walk rate, accept high K%
    - Don't care about AVG/contact
    """
    score = 0
    max_score = 100
    
    # Power (35 points)
    pow_ = parse_number(player.get("POW", 0))
    if pow_ >= 70:
        score += 35
    elif pow_ >= 60:
        score += 28
    elif pow_ >= 55:
        score += 18
    elif pow_ >= 50:
        score += 10
    
    # Eye/Walk ability (30 points)
    eye = parse_number(player.get("EYE", 0))
    if eye >= 65:
        score += 30
    elif eye >= 55:
        score += 24
    elif eye >= 50:
        score += 16
    elif eye >= 45:
        score += 8
    
    # HR production (20 points)
    hr = parse_number(player.get("HR", 0))
    if hr >= 40:
        score += 20
    elif hr >= 30:
        score += 16
    elif hr >= 20:
        score += 10
    elif hr >= 15:
        score += 5
    
    # BB% (15 points)
    bb_pct = parse_number(player.get("BB%", 0))
    if bb_pct >= 15:
        score += 15
    elif bb_pct >= 12:
        score += 12
    elif bb_pct >= 10:
        score += 8
    elif bb_pct >= 8:
        score += 4
    
    return min(score, max_score)


def calculate_defense_wins_fit(player):
    """
    Defense Wins archetype:
    - Elite defense priority
    - Accept weaker bats for glove
    - Premium positions valued
    """
    score = 0
    max_score = 100
    
    pos = player.get("POS", "")
    premium_positions = {"C", "2B", "SS", "CF"}
    
    # Get defensive ratings based on position
    if pos == "C":
        c_abi = parse_number(player.get("C ABI", 0))
        c_arm = parse_number(player.get("C ARM", 0))
        c_frm = parse_number(player.get("C FRM", 0))
        def_avg = (c_abi + c_arm + c_frm) / 3 if c_frm > 0 else (c_abi + c_arm) / 2
    elif pos in {"2B", "SS", "3B", "1B"}:
        if_rng = parse_number(player.get("IF RNG", 0))
        if_arm = parse_number(player.get("IF ARM", 0))
        if_err = parse_number(player.get("IF ERR", 0))
        def_avg = (if_rng + if_arm + if_err) / 3
    else:  # OF
        of_rng = parse_number(player.get("OF RNG", 0))
        of_arm = parse_number(player.get("OF ARM", 0))
        of_err = parse_number(player.get("OF ERR", 0))
        def_avg = (of_rng + of_arm + of_err) / 3
    
    # Defense (50 points) - most important
    if def_avg >= 70:
        score += 50
    elif def_avg >= 65:
        score += 42
    elif def_avg >= 60:
        score += 32
    elif def_avg >= 55:
        score += 22
    elif def_avg >= 50:
        score += 12
    
    # Position premium (25 points)
    if pos in premium_positions:
        score += 25
    elif pos in {"3B", "LF", "RF"}:
        score += 10
    
    # Speed (15 points) - helps defense
    spe = parse_number(player.get("SPE", 0))
    if spe >= 60:
        score += 15
    elif spe >= 50:
        score += 10
    elif spe >= 40:
        score += 5
    
    # Accept weaker bat bonus (10 points) - low salary despite poor offense
    con = parse_number(player.get("CON", 0))
    pow_ = parse_number(player.get("POW", 0))
    avg_bat = (con + pow_) / 2
    salary = parse_salary(player.get("SLR", 0))
    
    if avg_bat < 45 and def_avg >= 60:
        if salary < 3:
            score += 10
        elif salary < 5:
            score += 6
    
    return min(score, max_score)


def calculate_prospect_pipeline_fit(player, player_type="batter"):
    """
    Prospect Pipeline archetype:
    - Perpetual rebuild, always flipping
    - Age ≤24, high POT, constant churn
    """
    score = 0
    max_score = 100
    
    age = get_age(player)
    
    # Age (35 points) - must be young
    if age <= 21:
        score += 35
    elif age <= 22:
        score += 30
    elif age <= 23:
        score += 24
    elif age <= 24:
        score += 18
    elif age <= 25:
        score += 8
    else:
        return 0  # Too old for prospect pipeline
    
    # High potential (35 points)
    pot = parse_star_rating(player.get("POT", "0"))
    ovr = parse_star_rating(player.get("OVR", "0"))
    
    if is_star_scale(pot):
        if pot >= 4.5:
            score += 35
        elif pot >= 4.0:
            score += 28
        elif pot >= 3.5:
            score += 20
        elif pot >= 3.0:
            score += 12
    else:
        if pot >= 70:
            score += 35
        elif pot >= 65:
            score += 28
        elif pot >= 60:
            score += 20
        elif pot >= 55:
            score += 12
    
    # Upside gap (20 points)
    gap = pot - ovr
    if is_star_scale(pot):
        if gap >= 2.0:
            score += 20
        elif gap >= 1.5:
            score += 16
        elif gap >= 1.0:
            score += 10
        elif gap >= 0.5:
            score += 5
    else:
        if gap >= 20:
            score += 20
        elif gap >= 15:
            score += 16
        elif gap >= 10:
            score += 10
        elif gap >= 5:
            score += 5
    
    # Cheap contract (10 points)
    yl_data = parse_years_left(player.get("YL", ""))
    status = yl_data.get("status", "unknown")
    
    if status == "pre_arb":
        score += 10
    elif status == "arbitration":
        score += 6
    else:
        salary = parse_salary(player.get("SLR", 0))
        if salary < 2:
            score += 4
    
    return min(score, max_score)


def calculate_veteran_presence_fit(player, player_type="batter"):
    """
    Veteran Presence archetype:
    - Experienced leadership roster
    - Age 30+, proven track record, high OVR
    """
    score = 0
    max_score = 100
    
    age = get_age(player)
    
    # Age (25 points) - must be veteran
    if age >= 34:
        score += 25
    elif age >= 32:
        score += 22
    elif age >= 30:
        score += 18
    elif age >= 28:
        score += 10
    else:
        return 0  # Not veteran enough
    
    # High OVR (40 points) - proven track record
    ovr = parse_star_rating(player.get("OVR", "0"))
    if is_star_scale(ovr):
        if ovr >= 4.0:
            score += 40
        elif ovr >= 3.5:
            score += 32
        elif ovr >= 3.0:
            score += 22
        elif ovr >= 2.5:
            score += 12
    else:
        if ovr >= 70:
            score += 40
        elif ovr >= 65:
            score += 32
        elif ovr >= 60:
            score += 22
        elif ovr >= 55:
            score += 12
    
    # Current production (25 points)
    if player_type == "batter":
        war = parse_number(player.get("WAR (Batter)", player.get("WAR", 0)))
        wrc_plus = parse_number(player.get("wRC+", 0))
        
        if war >= 3:
            score += 15
        elif war >= 2:
            score += 10
        elif war >= 1:
            score += 5
        
        if wrc_plus >= 120:
            score += 10
        elif wrc_plus >= 100:
            score += 6
    else:
        war = parse_number(player.get("WAR (Pitcher)", player.get("WAR", 0)))
        era_plus = parse_number(player.get("ERA+", 0))
        
        if war >= 3:
            score += 15
        elif war >= 2:
            score += 10
        elif war >= 1:
            score += 5
        
        if era_plus >= 120:
            score += 10
        elif era_plus >= 100:
            score += 6
    
    # Leadership bonus - years in league (10 points) estimated from age
    if age >= 35:
        score += 10
    elif age >= 32:
        score += 7
    elif age >= 30:
        score += 4
    
    return min(score, max_score)


def calculate_innings_eaters_fit(player, player_type="pitcher"):
    """
    Innings Eaters archetype (pitchers only):
    - High stamina, durable pitchers
    - STM ≥60, low injury prone
    - Can eat innings and save bullpen
    """
    if player_type != "pitcher":
        return 0
    
    score = 0
    max_score = 100
    
    pos = player.get("POS", "")
    if pos != "SP":
        return 0  # Only starters can be innings eaters
    
    # Stamina (40 points) - most important
    stm = parse_number(player.get("STM", 0))
    if stm >= 70:
        score += 40
    elif stm >= 65:
        score += 35
    elif stm >= 60:
        score += 28
    elif stm >= 55:
        score += 18
    elif stm >= 50:
        score += 10
    
    # Durability/Health (25 points)
    # Check injury prone rating (lower is better)
    prone = player.get("Prone", "")
    if prone == "Durable" or prone == "":
        score += 25
    elif prone == "Normal":
        score += 18
    elif prone == "Fragile":
        score += 5
    elif prone == "Wrecked":
        score += 0
    else:
        score += 15  # Unknown, assume average
    
    # IP production (20 points)
    ip = parse_number(player.get("IP", 0))
    if ip >= 200:
        score += 20
    elif ip >= 180:
        score += 16
    elif ip >= 160:
        score += 12
    elif ip >= 140:
        score += 8
    elif ip >= 100:
        score += 4
    
    # Baseline competence (15 points) - needs to be good enough to keep in games
    ovr = parse_star_rating(player.get("OVR", "0"))
    if is_star_scale(ovr):
        if ovr >= 3.0:
            score += 15
        elif ovr >= 2.5:
            score += 10
        elif ovr >= 2.0:
            score += 5
    else:
        if ovr >= 55:
            score += 15
        elif ovr >= 50:
            score += 10
        elif ovr >= 45:
            score += 5
    
    return min(score, max_score)


def calculate_archetype_fit(player, archetype, player_type="batter"):
    """Calculate fit score for a player against an archetype"""
    archetype_funcs = {
        "speed_defense": lambda p: calculate_speed_defense_fit(p) if player_type == "batter" else 0,
        "mashers": lambda p: calculate_mashers_fit(p) if player_type == "batter" else 0,
        "moneyball": lambda p: calculate_moneyball_fit(p) if player_type == "batter" else 0,
        "youth_movement": lambda p: calculate_youth_movement_fit(p, player_type),
        "win_now": lambda p: calculate_win_now_fit(p, player_type),
        "budget_build": lambda p: calculate_budget_build_fit(p, player_type),
        "balanced": lambda p: calculate_balanced_fit(p, player_type),
        "chaos_ball": lambda p: calculate_chaos_ball_fit(p) if player_type == "batter" else 0,
        "small_ball": lambda p: calculate_small_ball_fit(p) if player_type == "batter" else 0,
        "ace_hunter": lambda p: calculate_ace_hunter_fit(p, player_type),
        "bullpen_first": lambda p: calculate_bullpen_first_fit(p, player_type),
        "platoon_army": lambda p: calculate_platoon_army_fit(p) if player_type == "batter" else 0,
        "launch_angle": lambda p: calculate_launch_angle_fit(p) if player_type == "batter" else 0,
        "defense_wins": lambda p: calculate_defense_wins_fit(p) if player_type == "batter" else 0,
        "prospect_pipeline": lambda p: calculate_prospect_pipeline_fit(p, player_type),
        "veteran_presence": lambda p: calculate_veteran_presence_fit(p, player_type),
        "innings_eaters": lambda p: calculate_innings_eaters_fit(p, player_type),
    }
    
    func = archetype_funcs.get(archetype)
    if func:
        return func(player)
    return 0


def find_players_by_archetype(players, archetype, player_type="batter", min_fit=40):
    """
    Find all players that fit a given archetype.
    Returns list of (player, fit_score, fit_label) sorted by fit score.
    """
    results = []
    
    # Check if archetype supports this player type
    archetype_info = ARCHETYPES.get(archetype, {})
    supported_types = archetype_info.get("player_types", [])
    
    if player_type not in supported_types:
        return results
    
    for player in players:
        fit_score = calculate_archetype_fit(player, archetype, player_type)
        
        if fit_score >= min_fit:
            fit_label = get_fit_label(fit_score)
            results.append({
                "player": player,
                "fit_score": fit_score,
                "fit_label": fit_label,
                "name": player.get("Name", ""),
                "team": player.get("ORG", ""),
                "pos": player.get("POS", ""),
                "age": get_age(player),
                "ovr": parse_star_rating(player.get("OVR", "0")),
                "pot": parse_star_rating(player.get("POT", "0")),
            })
    
    # Sort by fit score descending
    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return results


def get_player_archetype_fits(player, player_type="batter"):
    """
    Get all archetype fits for a single player.
    Returns dict of archetype -> fit_score
    """
    results = {}
    for archetype, info in ARCHETYPES.items():
        if player_type in info.get("player_types", []):
            fit_score = calculate_archetype_fit(player, archetype, player_type)
            results[archetype] = {
                "score": fit_score,
                "label": get_fit_label(fit_score),
                "archetype_name": info["name"],
                "archetype_icon": info["icon"],
            }
    return results


def get_best_archetype(player, player_type="batter"):
    """Get the best-fitting archetype for a player"""
    fits = get_player_archetype_fits(player, player_type)
    if not fits:
        return None
    
    best = max(fits.items(), key=lambda x: x[1]["score"])
    return {
        "archetype": best[0],
        "score": best[1]["score"],
        "name": best[1]["archetype_name"],
        "icon": best[1]["archetype_icon"],
        "label": best[1]["label"],
    }
