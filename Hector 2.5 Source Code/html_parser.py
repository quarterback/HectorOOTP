"""
HTML Parser for OOTP exports.
Parses Player List.html, Free Agents.html, and other OOTP HTML exports.
"""

from bs4 import BeautifulSoup

# Position constants
PITCHER_POSITIONS = {"P", "SP", "RP", "CL"}
BATTER_POSITIONS = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"}


def parse_players_from_html(html_path):
    """
    Parse players from an OOTP HTML export file.
    
    Args:
        html_path: Path to the HTML file (e.g., "Player List.html" or "Free Agents.html")
    
    Returns:
        List of player dictionaries with all columns from the HTML table
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, "html.parser")
    
    table = soup.find("table", class_="data")
    if not table:
        raise ValueError(f"No table with class 'data' found in {html_path}")
    
    # Header row
    thead = table.find("thead")
    if thead:
        header_row = thead.find("tr")
    else:
        header_row = table.find("tr")
    
    if not header_row:
        raise ValueError(f"No header row found in the table in {html_path}.")
    
    headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
    
    # Handle duplicate header names by checking context
    # WAR appears twice: once for batters (after wRC+) and once for pitchers (after ERA+)
    processed_headers = []
    for i, header in enumerate(headers):
        if header == "WAR":
            # Check previous headers to determine which WAR this is
            if i > 0 and headers[i-1] == "wRC+":
                processed_headers.append("WAR (Batter)")
            elif i > 0 and headers[i-1] == "ERA+":
                processed_headers.append("WAR (Pitcher)")
            else:
                processed_headers.append(header)
        else:
            processed_headers.append(header)
    
    # Data rows
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr")
    else:
        rows = table.find_all("tr")[1:]  # skip header row
    
    players = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) != len(processed_headers):
            continue  # skip junk
        player_data = {processed_headers[i]: cells[i].get_text(strip=True) for i in range(len(processed_headers))}
        players.append(player_data)
    
    return players


def split_players_by_type(players):
    """
    Split a list of players into pitchers and batters based on position.
    
    Args:
        players: List of player dictionaries
    
    Returns:
        Tuple of (pitchers, batters) lists
    """
    pitchers = []
    batters = []
    
    for player in players:
        pos = player.get("POS", "").strip().upper()
        if pos in PITCHER_POSITIONS:
            pitchers.append(player)
        elif pos in BATTER_POSITIONS:
            batters.append(player)
    
    return pitchers, batters
