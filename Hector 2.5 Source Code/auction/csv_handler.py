"""
CSV import/export for auction system.
Handles reading OOTP free agent CSV exports and writing auction results.
"""

import csv
from typing import List, Dict, Optional, Tuple
from pathlib import Path


def import_free_agents_csv(csv_path: str) -> List[Dict]:
    """
    Import free agents from OOTP CSV export.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        List of player dictionaries with all fields from CSV
    """
    players = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean up the data - strip whitespace from keys and values
            player = {k.strip(): v.strip() if isinstance(v, str) else v 
                     for k, v in row.items()}
            players.append(player)
    
    return players


def export_auction_results_csv(results: List[Dict], output_path: str, format_type: str = 'ootp'):
    """
    Export auction results to CSV for OOTP import.
    
    Args:
        results: List of auction result dictionaries with keys:
                 - player: player dict
                 - team: winning team abbreviation
                 - price: auction price
        output_path: Path for output CSV file
        format_type: Format type ('ootp' for OOTP-compatible, 'detailed' for full info)
    """
    if format_type == 'ootp':
        _export_ootp_format(results, output_path)
    else:
        _export_detailed_format(results, output_path)


def _export_ootp_format(results: List[Dict], output_path: str):
    """
    Export in OOTP-compatible format for importing back into game.
    Format: Player Name, Team, Years, AAV (Annual Average Value)
    """
    fieldnames = ['Name', 'Team', 'Years', 'AAV']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            player = result['player']
            team = result['team']
            price = result['price']
            
            # Calculate contract years based on age
            age = _parse_age(player.get('Age', '25'))
            years = _calculate_contract_years(age, price)
            aav = price  # In auction system, price is per year
            
            writer.writerow({
                'Name': player.get('Name', ''),
                'Team': team,
                'Years': years,
                'AAV': f"${aav:.2f}M"
            })


def _export_detailed_format(results: List[Dict], output_path: str):
    """
    Export detailed format with full player info and auction details.
    """
    if not results:
        fieldnames = ['Name', 'Position', 'Age', 'Team', 'Price', 'OVR', 'POT']
    else:
        # Get all possible fieldnames from first player
        sample_player = results[0]['player']
        player_fields = list(sample_player.keys())
        fieldnames = player_fields + ['Winning_Team', 'Auction_Price']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            player = result['player']
            row = player.copy()
            row['Winning_Team'] = result['team']
            row['Auction_Price'] = f"${result['price']:.2f}M"
            writer.writerow(row)


def _parse_age(age_str: str) -> int:
    """Parse age from string, handling various formats"""
    try:
        # Handle cases like "25" or "25.5" or "25 years"
        age_str = age_str.split()[0]  # Take first token
        return int(float(age_str))
    except (ValueError, AttributeError):
        return 25  # Default age


def _calculate_contract_years(age: int, price: float) -> int:
    """
    Calculate appropriate contract years based on age and price.
    Higher prices and younger ages get longer contracts.
    """
    if age <= 26:
        if price >= 20:
            return 7
        elif price >= 10:
            return 6
        else:
            return 5
    elif age <= 29:
        if price >= 20:
            return 6
        elif price >= 10:
            return 5
        else:
            return 4
    elif age <= 32:
        if price >= 15:
            return 4
        elif price >= 8:
            return 3
        else:
            return 2
    elif age <= 35:
        if price >= 10:
            return 2
        else:
            return 1
    else:
        return 1


def validate_csv_format(csv_path: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate that CSV has required fields for auction.
    
    Returns:
        (is_valid, error_message, available_fields)
    """
    required_fields = {'Name', 'POS', 'Age'}
    
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = [field.strip() for field in reader.fieldnames] if reader.fieldnames else []
            
            if not fieldnames:
                return False, "CSV file has no headers", []
            
            missing_fields = required_fields - set(fieldnames)
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}", fieldnames
            
            return True, None, fieldnames
            
    except Exception as e:
        return False, f"Error reading CSV: {str(e)}", []


def create_sample_free_agents_csv(output_path: str):
    """Create a sample free agents CSV for testing"""
    sample_data = [
        {
            'Name': 'John Smith',
            'POS': 'SP',
            'Age': '28',
            'OVR': '65',
            'POT': '70',
            'STU': '60',
            'MOV': '65',
            'CON': '70',
            'WAR': '3.5',
            'ERA+': '115'
        },
        {
            'Name': 'Mike Johnson',
            'POS': 'C',
            'Age': '25',
            'OVR': '60',
            'POT': '75',
            'CON': '55',
            'POW': '65',
            'EYE': '60',
            'WAR': '2.8',
            'wRC+': '105'
        },
        {
            'Name': 'Tom Williams',
            'POS': 'SS',
            'Age': '30',
            'OVR': '70',
            'POT': '70',
            'CON': '70',
            'POW': '60',
            'EYE': '65',
            'WAR': '4.2',
            'wRC+': '120'
        }
    ]
    
    # Get all unique fieldnames from all records
    fieldnames = []
    for record in sample_data:
        for key in record.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
