# OOTP Salary Market Analyzer

An interactive web dashboard for analyzing salary market dynamics in Out of the Park Baseball (OOTP) 26. This tool helps you understand player salary trends across positions, teams, and player quality tiers by combining data from free agents, signed players, and team budgets.

## Features

### 📊 Market Overview
- League-wide payroll and budget statistics
- Free agent market capacity analysis
- Supply/demand ratio indicators
- Player distribution by quality tier
- Market condition assessment (buyer's vs seller's market)

### 💰 Position Analysis
- Salary statistics by position (average, median, min, max, percentiles)
- Position-specific player counts (signed vs free agents)
- Interactive salary comparison charts
- Filterable position views
- Exportable CSV reports

### ⭐ Tier Analysis
- Salary breakdowns by player quality (5.0★ elite to <3.0★ role players)
- Tier-based salary distributions
- Elite vs role player premium analysis
- Signed player vs free agent comparisons

### 🏢 Team Analysis
- Team spending and budget utilization
- Roster composition analysis
- Elite player counts by team
- Sortable team financials (payroll, available FA budget, etc.)
- Interactive visualizations of team spending patterns

### 🔍 Player Lookup
- Find comparable players by position and overall rating
- Salary range analysis for specific player types
- Source tracking (free agent vs signed)
- Team affiliations
- Exportable player comparables

## Installation

### Requirements
- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. **Clone or navigate to the FA-market-tool directory**
```bash
cd FA-market-tool
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

The tool requires the following packages:
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `streamlit` - Web dashboard framework
- `plotly` - Interactive visualizations

## Usage

### 1. Prepare Your Data Files

Export the following HTML files from OOTP 26:

**TeamFin.html** - Team Financial Report
- Navigate to: League → Reports → Team List
- Export the page as HTML
- Rename to `TeamFin.html`

**fafinancials.html** - Free Agent List
- Navigate to: Players → Free Agents
- Export the page as HTML
- Rename to `fafinancials.html`

**signed.html** - Signed Players List
- Navigate to: Players → Player List (filter to show only signed players)
- Export the page as HTML
- Rename to `signed.html`

Place all three files in the `FA-market-tool` directory.

### 2. Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

### 3. Navigate the Dashboard

The application has 7 main tabs:

#### 📊 Market Overview
View league-wide statistics:
- Total teams, league payroll, FA capacity
- Signed player statistics (count, avg/median salary)
- Free agent statistics (count, demands)
- Supply/demand ratio and market condition
- Player distribution chart by tier

#### 💰 Salary Bands
Understand salary ranges for position/tier combinations:
- **Box plot visualizations** showing salary distributions (min, 25th percentile, median, 75th percentile, max)
- **Side-by-side comparison** of signed players vs free agents
- **Interactive filters** for positions, tiers, and player source
- **Salary band matrix table** showing Position × Tier median salaries
- **Market gap analysis** highlighting where FAs demand more than rostered players
- **Download capability** for salary reference data

#### 🎯 Player Pricer
Get instant market value estimates:
- **Input form** for position, overall rating, and optional age filters
- **Salary range recommendations** based on comparable players (25th-75th percentile)
- **Market value estimate** (median of comparables)
- **Percentile calculator** to evaluate proposed offers
- **Comparable players table** showing 10-20 similar players with salaries
- **Visual salary distribution** with histogram
- **Market context** including signed vs FA breakdown and warnings for extreme offers

#### 📍 Position Analysis
Analyze salaries by position:
- Filter specific positions using the multiselect
- View average and median salary charts
- Examine detailed position market statistics
- Download position analysis as CSV

#### ⭐ Tier Analysis
Understand player quality tiers:
- See salary distributions by overall rating
- Compare average vs median salaries by tier
- **Market gap visualization** with side-by-side bars for signed vs FA salaries
- **FA Premium table** showing percentage differences
- **Salary range boxes** for each tier (25th-75th percentile)
- View elite player premium (how much more elite players earn)
- Analyze tier-specific market details

#### 🏢 Team Analysis
Explore team spending patterns:
- Sort teams by payroll, available FA budget, or elite players
- Visualize top spenders
- Examine budget utilization vs payroll
- Download team analysis as CSV

#### 🔍 Player Lookup
Find comparable players:
- Select position
- Set overall rating range (min/max)
- View comparable players with salaries
- See salary statistics (avg, median, range)
- Download comparables as CSV

## Data Processing

### Parser Module (`parser.py`)

The OOTPParser class handles HTML parsing:

```python
from parser import OOTPParser

parser = OOTPParser(html_dir=".")
teams = parser.parse_team_financials(filename="TeamFin.html")
fas = parser.parse_free_agents(filename="fafinancials.html")
signed = parser.parse_signed_players(filename="signed.html")
```

**Supported formats:**
- Money: `$17,212,221`, `$12.5m`, `$600k`
- Stars: `4.5 Stars` → `4.5`

### Market Engine (`market_engine.py`)

The MarketAnalyzer class provides comprehensive market analysis:

```python
from market_engine import MarketAnalyzer

analyzer = MarketAnalyzer(teams, fas, signed)

# Get market overview
overview = analyzer.get_market_overview()

# Get position-specific stats
position_stats = analyzer.get_position_market_summary()

# Get tier-based stats
tier_stats = analyzer.get_tier_market_summary()

# Get team spending stats
team_stats = analyzer.get_team_market_summary()

# Find comparable players
comps = analyzer.get_comparable_players('SP', 4.0, 4.5, limit=20)

# NEW: Get salary bands by position/tier/source
salary_bands = analyzer.get_salary_bands(position='SP', tier='Elite (5.0★)', source='both')

# NEW: Get position-tier matrix
matrix = analyzer.get_position_tier_matrix(metric='median', source='both')

# NEW: Get market gap analysis
gap_analysis = analyzer.get_market_gap_analysis()

# NEW: Get player pricing recommendation
pricing = analyzer.get_player_pricing(
    position='SP',
    overall_min=4.0,
    overall_max=4.5,
    age_min=25,
    age_max=32
)

# NEW: Calculate offer percentile
percentile = analyzer.calculate_offer_percentile(
    offer=5_000_000,
    comparables=pricing['comparables']
)
```

## File Structure

```
FA-market-tool/
├── TeamFin.html          # Team budget data (export from OOTP)
├── fafinancials.html     # Free agent data (export from OOTP)
├── signed.html           # Signed player data (export from OOTP)
├── parser.py             # HTML parsing module
├── market_engine.py      # Market analysis engine
├── app.py                # Streamlit dashboard
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Key Statistics Explained

### Supply/Demand Ratio
- **> 1.5x**: Buyer's Market (teams have more budget than FA demands)
- **0.8-1.5x**: Balanced Market
- **< 0.8x**: Seller's Market (FA demands exceed available budgets)

### Player Tiers
- **Elite (5.0★)**: Top-tier players, typically franchise cornerstones
- **Star (4.5★)**: High-quality regulars
- **Above Average (4.0★)**: Solid everyday players
- **Average (3.5★)**: Average MLB-caliber players
- **Below Average (3.0★)**: Below-average regulars or platoon players
- **Role Player (<3.0★)**: Bench players, backups, minor leaguers

### Budget Utilization
Percentage of team budget currently spent on payroll. Lower utilization means more capacity for free agent signings.

## Export Capabilities

All analysis tabs include CSV export functionality:
- **Salary Bands** → `salary_band_matrix.csv`, `market_gap_analysis.csv`
- **Player Pricer** → `{position}_{rating}star_comparables.csv`
- **Position Analysis** → `position_analysis.csv`
- **Team Analysis** → `team_analysis.csv`
- **Player Lookup** → `{position}_comparables.csv`

## Troubleshooting

### File Not Found Errors
Ensure all three HTML files are in the same directory as the app and have correct filenames:
- `TeamFin.html` (case-sensitive)
- `fafinancials.html`
- `signed.html`

### Missing Data in Charts
Verify that your HTML exports contain complete data. Some reports require specific filters to be set before exporting.

### Import Errors
Install all required packages:
```bash
pip install -r requirements.txt
```

## Advanced Usage

### Command-Line Analysis

You can use the modules directly in Python scripts:

```python
from parser import OOTPParser
from market_engine import MarketAnalyzer

# Parse data
parser = OOTPParser(html_dir=".")
teams = parser.parse_team_financials()
fas = parser.parse_free_agents()
signed = parser.parse_signed_players()

# Analyze
analyzer = MarketAnalyzer(teams, fas, signed)

# Get specific position analysis
sp_stats = analyzer.get_position_market_summary('SP')
print(f"SP Average Salary: ${sp_stats['avg_salary'].values[0]/1e6:.2f}M")

# Find elite free agent pitchers
elite_sp_fas = fas[(fas['position'] == 'SP') & (fas['overall'] >= 4.5)]
print(f"Elite SP Free Agents: {len(elite_sp_fas)}")
```

## Contributing

This is an open-source tool for the OOTP community. Feel free to modify and enhance it for your league's specific needs.

## License

This tool is provided as-is for use with Out of the Park Baseball. All OOTP-related trademarks are property of Out of the Park Developments.

## Support

For issues or questions, please refer to the OOTP community forums or create an issue in the repository.

---

**Version**: 2.0  
**Compatible with**: OOTP 26  
**Last Updated**: January 2026

## What's New in Version 2.0

### 💰 Salary Bands Tab
- Visualize salary distributions with box plots for any position/tier combination
- Compare signed players vs free agents side-by-side
- View salary band matrix showing median salaries across positions and tiers
- Analyze market gaps to understand FA premium demands
- Download salary reference sheets for quick pricing decisions

### 🎯 Player Pricer Tool
- Instant market value estimates based on comparable players
- Adjustable search parameters (position, overall rating, age)
- Percentile calculator to evaluate proposed offers
- Visual salary distributions with market context
- Warnings for offers that are significantly above or below market value

### ⭐ Enhanced Tier Analysis
- New market gap visualizations comparing signed vs FA salaries
- FA Premium table showing percentage differences by tier
- Salary range boxes displaying 25th-75th percentile ranges
- Better understanding of pricing differences between rostered and free agent players
