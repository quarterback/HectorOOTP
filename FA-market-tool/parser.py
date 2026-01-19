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
    
    def __init__(self, html_dir: str = ". "):
        self.html_dir = Path(html_dir)
    
    def parse_team_financials(self, filename: str = "Team Financials.html") -> pd.DataFrame:
        """Extract team budget and payroll data"""
        html_path = self.html_dir / filename
        
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        teams = []
        rows = soup.find_all('tr')[1:]  # Skip header
        
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
                'last_year_wins': int(cols[5].text.strip()) if cols[5].text.strip().isdigit() else 0,
                'last_year_losses': int(cols[6].text.strip()) if cols[6].text.strip().isdigit() else 0,
            }
            teams.append(team_data)
        
        df = pd.DataFrame(teams)
        df['win_pct'] = df['last_year_wins'] / (df['last_year_wins'] + df['last_year_losses'])
        return df
    
    def parse_free_agents(self, filename: str = "free agent financials.html") -> pd.DataFrame:
        """Extract free agent player data"""
        html_path = self.html_dir / filename
        
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        players = []
        rows = soup. find_all('tr')[1:]  # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 24:
                continue
            
            player_data = {
                'position': cols[0].text.strip(),
                'name': cols[2].text.strip(),
                'age': int(cols[6].text.strip()),
                'bats': cols[7].text. strip(),
                'throws': cols[8].text.strip(),
                'overall':  self._parse_stars(cols[9].text),
                'potential': self._parse_stars(cols[10].text),
                'injury_prone': cols[11].text.strip(),
                'war':  float(cols[21].text.strip()) if self._is_number(cols[21].text) else 0.0,
                'rwar': float(cols[22].text.strip()) if self._is_number(cols[22].text) else 0.0,
                'demand': self._parse_money(cols[23].text),
                'jaws':  float(cols[24].text.strip()) if self._is_number(cols[24].text) else 0.0,
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
    parser = OOTPParser()
    
    # Extract data
    teams = parser.parse_team_financials()
    free_agents = parser.parse_free_agents()
    
    # Quick stats
    print(f"📊 Parsed {len(teams)} teams")
    print(f"👥 Parsed {len(free_agents)} free agents")
    print(f"\n💰 Total Market Capacity: ${teams['available_for_fa'].sum() / 1e6:.1f}M")
    print(f"💸 Total FA Demands: ${free_agents['demand']. sum() / 1e6:.1f}M")
    
    # Save to CSV
    teams.to_csv('parsed_teams.csv', index=False)
    free_agents.to_csv('parsed_free_agents.csv', index=False)
