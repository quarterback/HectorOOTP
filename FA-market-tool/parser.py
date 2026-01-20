"""
OOTP Free Agent Market Parser
Extracts data from HTML exports for market analysis
"""

from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
from typing import Dict, List
import re

class OOTPParser:
    """Parse OOTP HTML exports into structured data"""
    
    # Expected column count in TeamFin.html
    TEAMFIN_MIN_COLUMNS = 16
    
    def __init__(self, html_dir: str = "."):
        self.html_dir = Path(html_dir)
    
    def parse_team_financials(self, filename: str = "TeamFin.html") -> pd.DataFrame:
        """Extract team budget and payroll data with all available columns
        
        Column mapping (0-indexed):
        0: ID, 1: Team (city), 2: Team Name (full), 3: Abbr, 4: Pay (Payroll),
        5: Bgt (Budget), 6: Tkt (Ticket Price), 7: BgtSpc (Budget Space),
        8: Int (Fan Interest), 9: Mode (Team Mode), 10: Revenue, 11: Exp (Expenses),
        12: CT (Cash from Trades), 13: lyW (Last Year Wins), 14: lyL (Last Year Losses),
        15: ly% (Last Year Win Percentage)
        """
        html_path = self.html_dir / filename
        
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Find the data table specifically
        data_table = soup.find('table', class_='data sortable')
        if not data_table:
            data_table = soup.find('table', class_='data')
        
        teams = []
        rows = data_table.find_all('tr')[1:] if data_table else []  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            
            # Skip rows that don't have team data
            if len(cols) < self.TEAMFIN_MIN_COLUMNS:  # Need at least 16 columns for full data
                continue
            
            # Parse monetary values
            payroll = self._parse_money(cols[4].text)
            budget = self._parse_money(cols[5].text)
            ticket_price = self._parse_money(cols[6].text)
            budget_space = self._parse_money(cols[7].text)  # Can be negative!
            revenue = self._parse_money(cols[10].text)
            expenses = self._parse_money(cols[11].text)
            cash_from_trades = self._parse_money(cols[12].text) if cols[12].text.strip() else 0.0
            
            # Parse integer values
            team_id = int(cols[0].text.strip()) if cols[0].text.strip().isdigit() else 0
            fan_interest = int(cols[8].text.strip()) if cols[8].text.strip().isdigit() else 50
            last_year_wins = int(cols[13].text.strip()) if cols[13].text.strip().isdigit() else 0
            last_year_losses = int(cols[14].text.strip()) if cols[14].text.strip().isdigit() else 0
            
            # Parse text values
            team_city = cols[1].text.strip()
            team_name = cols[2].text.strip()
            abbr = cols[3].text.strip()
            mode = cols[9].text.strip()  # "Win Now!", "Build a Dynasty!", "Neutral", "Rebuilding"
            
            # Parse win percentage
            win_pct_text = cols[15].text.strip()
            if win_pct_text and win_pct_text.startswith('.'):
                win_pct = float(win_pct_text)
            elif last_year_wins > 0 or last_year_losses > 0:
                win_pct = last_year_wins / (last_year_wins + last_year_losses)
            else:
                win_pct = 0.500
            
            team_data = {
                'team_id': team_id,
                'team_city': team_city,
                'team_name': team_name,
                'abbr': abbr,
                'payroll': payroll,
                'budget': budget,
                'ticket_price': ticket_price,
                'budget_space': budget_space,
                'fan_interest': fan_interest,
                'mode': mode,
                'revenue': revenue,
                'expenses': expenses,
                'cash_from_trades': cash_from_trades,
                'last_year_wins': last_year_wins,
                'last_year_losses': last_year_losses,
                'win_pct': win_pct,
                'available_for_fa': budget - payroll,  # Basic calculation, will be enhanced
            }
            
            teams.append(team_data)
        
        return pd.DataFrame(teams)
    
    def parse_free_agents(self, filename: str = "fafinancials.html") -> pd.DataFrame:
        """Extract free agent player data"""
        html_path = self.html_dir / filename
        
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Find the data table specifically
        data_table = soup.find('table', class_='data sortable')
        if not data_table:
            data_table = soup.find('table', class_='data')
        
        players = []
        rows = data_table.find_all('tr')[1:] if data_table else []  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 24:
                continue
            
            player_data = {
                'position': cols[0].text.strip(),
                'name': cols[2].text.strip(),
                'age': int(cols[6].text.strip()),
                'bats': cols[7].text.strip(),
                'throws': cols[8].text.strip(),
                'overall': self._parse_stars(cols[9].text),
                'potential': self._parse_stars(cols[10].text),
                'injury_prone': cols[11].text.strip(),
                'war': float(cols[21].text.strip()) if self._is_number(cols[21].text) else 0.0,
                'rwar': float(cols[22].text.strip()) if self._is_number(cols[22].text) else 0.0,
                'demand': self._parse_money(cols[23].text),
                'jaws': float(cols[24].text.strip()) if self._is_number(cols[24].text) else 0.0,
            }
            players.append(player_data)
        
        return pd.DataFrame(players)
    
    def parse_signed_players(self, filename: str = "signed.html") -> pd.DataFrame:
        """Parse signed player contracts for market analysis"""
        html_path = self.html_dir / filename
        
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Find the data table specifically
        data_table = soup.find('table', class_='data sortable')
        if not data_table:
            data_table = soup.find('table', class_='data')
        
        players = []
        rows = data_table.find_all('tr')[1:] if data_table else []  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 14:
                continue
            
            player_data = {
                'position': cols[0].text.strip(),
                'name': cols[1].text.strip(),
                'team': cols[2].text.strip(),
                'level': cols[3].text.strip(),
                'league': cols[4].text.strip(),
                'nationality': cols[5].text.strip(),
                'dob': cols[6].text.strip(),
                'age': int(cols[7].text.strip()) if cols[7].text.strip().isdigit() else 0,
                'overall': self._parse_stars(cols[8].text),
                'potential': self._parse_stars(cols[9].text),
                'salary': self._parse_money(cols[10].text),
                'years_left': int(cols[11].text.strip()) if cols[11].text.strip().isdigit() else 0,
                'contract_value': self._parse_money(cols[12].text),
                'total_years': int(cols[13].text.strip()) if cols[13].text.strip().isdigit() else 0,
            }
            players.append(player_data)
        
        return pd.DataFrame(players)
    
    def enrich_signed_players_with_team_data(self, signed_df: pd.DataFrame, teams_df: pd.DataFrame) -> pd.DataFrame:
        """Enrich signed players with full team data from TeamFin.html
        
        Args:
            signed_df: DataFrame of signed players with 'team' column containing team city name
                      (e.g., 'Montreal', 'Toronto', 'Nashville')
            teams_df: DataFrame of teams from parse_team_financials()
        
        Returns:
            DataFrame with enriched team columns added
        
        Note:
            The 'team' column in signed.html corresponds to team_city in TeamFin.html
        """
        # Create a copy to avoid modifying original
        enriched = signed_df.copy()
        
        # Create lookup dictionary: team_city -> team data
        team_lookup = {}
        for _, team_row in teams_df.iterrows():
            team_city = team_row['team_city']
            # Check if team_name already contains team_city
            team_name = team_row['team_name']
            if team_name.startswith(team_city):
                # Team name already includes city (e.g., "Arizona Diamondbacks")
                team_full_name = team_name
            else:
                # Team name doesn't include city (e.g., "Cubs" -> "Chicago Cubs")
                team_full_name = f"{team_city} {team_name}"
            
            team_lookup[team_city] = {
                'team_abbr': team_row['abbr'],
                'team_full_name': team_full_name,
                'team_name': team_row['team_name'],
                'team_city': team_row['team_city'],
                'team_mode': team_row['mode'],
                'team_win_pct': team_row['win_pct'],
                'team_budget': team_row['budget'],
                'team_payroll': team_row['payroll'],
                'team_budget_space': team_row['budget_space'],
                'team_fan_interest': team_row['fan_interest'],
                'team_revenue': team_row['revenue'],
                'team_expenses': team_row['expenses'],
                'team_last_year_wins': team_row['last_year_wins'],
                'team_last_year_losses': team_row['last_year_losses'],
            }
        
        # Add enriched columns
        for col_name in ['team_abbr', 'team_full_name', 'team_name', 'team_city', 'team_mode', 
                        'team_win_pct', 'team_budget', 'team_payroll', 'team_budget_space',
                        'team_fan_interest', 'team_revenue', 'team_expenses', 
                        'team_last_year_wins', 'team_last_year_losses']:
            enriched[col_name] = enriched['team'].map(
                lambda city: team_lookup.get(city, {}).get(col_name, None)
            )
        
        return enriched
    
    @staticmethod
    def _parse_money(text: str) -> float:
        """Convert '$12. 5m' or '$600k' to float"""
        text = text.strip().replace('$', '').replace(',', '')
        if 'm' in text.lower():
            return float(text.lower().replace('m', '')) * 1_000_000
        elif 'k' in text.lower():
            return float(text.lower().replace('k', '')) * 1_000
        elif text == '-' or not text:
            return 0.0
        return float(text)
    
    @staticmethod
    def _parse_stars(text: str) -> float:
        """Convert '4.5 Stars' to 4.5"""
        match = re.search(r'([\d.]+)', text)
        return float(match.group(1)) if match else 0.0
    
    @staticmethod
    def _is_number(text: str) -> bool:
        """Check if text can be converted to float"""
        try:
            float(text.strip())
            return True
        except (ValueError, AttributeError):
            return False


# Usage Example
if __name__ == "__main__": 
    parser = OOTPParser(html_dir=".")
    
    # Extract data
    teams = parser.parse_team_financials(filename="TeamFin.html")
    free_agents = parser.parse_free_agents(filename="fafinancials.html")
    signed = parser.parse_signed_players(filename="signed.html")
    
    # Quick stats
    print(f"📊 Parsed {len(teams)} teams")
    print(f"👥 Parsed {len(free_agents)} free agents")
    print(f"📝 Parsed {len(signed)} signed players")
    print(f"\n💰 Total Market Capacity: ${teams['available_for_fa'].sum() / 1e6:.1f}M")
    print(f"💸 Total FA Demands: ${free_agents['demand'].sum() / 1e6:.1f}M")
    print(f"💵 Total Signed Salaries: ${signed['salary'].sum() / 1e6:.1f}M")
    
    # Save to CSV
    teams.to_csv('parsed_teams.csv', index=False)
    free_agents.to_csv('parsed_free_agents.csv', index=False)
    signed.to_csv('parsed_signed.csv', index=False)
