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
    
    def __init__(self, html_dir: str = "."):
        self.html_dir = Path(html_dir)
    
    def parse_team_financials(self, filename: str = "TeamFin.html") -> pd.DataFrame:
        """Extract team budget and payroll data"""
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
            if len(cols) < 5:
                continue
                
            team_data = {
                'team_name': cols[1].text.strip(),
                'abbr': cols[2].text.strip(),
                'payroll': self._parse_money(cols[3].text),
                'budget': self._parse_money(cols[4].text),
                'available_for_fa': self._parse_money(cols[4].text) - self._parse_money(cols[3].text),
            }
            
            # Optional: Add win/loss data if available
            if len(cols) >= 7:
                team_data['last_year_wins'] = int(cols[5].text.strip()) if cols[5].text.strip().isdigit() else 0
                team_data['last_year_losses'] = int(cols[6].text.strip()) if cols[6].text.strip().isdigit() else 0
            
            teams.append(team_data)
        
        df = pd.DataFrame(teams)
        if 'last_year_wins' in df.columns and 'last_year_losses' in df.columns:
            df['win_pct'] = df['last_year_wins'] / (df['last_year_wins'] + df['last_year_losses'])
        return df
    
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
    
    @staticmethod
    def _parse_money(text: str) -> float:
        """Convert '$12. 5m' or '$600k' to float"""
        text = text.strip().replace('$', '').replace(',', '')
        if 'm' in text. lower():
            return float(text.lower().replace('m', '')) * 1_000_000
        elif 'k' in text.lower():
            return float(text. lower().replace('k', '')) * 1_000
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
            float(text. strip())
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
