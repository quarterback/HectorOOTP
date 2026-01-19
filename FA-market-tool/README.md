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
- Salary breakdowns by player quality (10 half-star tiers: 5.0★ Elite to 0.5★ Organizational)
- Granular tier system: Elite, Star, Above Average, Solid Average, Average, Below Average, Backup/Depth, Fringe, Minor League, Organizational
- Tier-based salary distributions
- Elite vs organizational player premium analysis
- Signed player vs free agent comparisons by tier

### 🏢 Team Analysis (Enhanced!)
- **Owner Investment Calculator**: Analyze owner capital injections based on performance, team mode, and fan interest
- **Comprehensive Team Data**: 17+ columns including last year's record, fan interest, OOTP budget space, and trade cash
- **Total FA Budget**: Complete calculation including base budget, OOTP space, trade cash, and owner investment
- **Configurable Display**: Slider to show 10 to all teams
- **Advanced Visualizations**:
  - Stacked bar chart: FA budget breakdown by source
  - Scatter plot: Win % vs Owner Investment (colored by team mode)
  - Heatmap: Performance × Team Mode aggressiveness scores
- **Color-Coded Insights**: Aggressiveness scores (0-100), mode badges, negative budget warnings
- **Enhanced Sorting**: Sort by total FA budget, owner investment, aggressiveness score, and more
- Exportable CSV reports

### 🎯 Budget Scenarios
- **Interactive Scenario Modeling**: Model "what-if" scenarios for any team
- **Configurable Inputs**: Adjust wins/losses, postseason results, team mode, and fan interest
- **Prominent Final Budget Summary**: Key results displayed at top for immediate visibility
- **Quick Summary Bar**: One-line overview of all calculation factors
- **Collapsible Detailed Breakdown**: 5-step expandable calculation (collapsed by default):
  1. Performance Factor (5-50% based on win %)
  2. Mode Factor (Win Now 100%, Dynasty 75%, Neutral 50%, Rebuilding 10%)
  3. Interest Factor (80-120% based on fan engagement)
  4. Base Owner Investment calculation
  5. Scenario bonus/penalty application
- **Postseason Bonuses**: Calculate impact of playoff success (Wild Card +15%, Division +25%, Pennant +35%, World Series +50%)
- **Fire Sale Mode**: Simulate owner teardown scenarios (random 51-77% reduction with re-randomize)
- **Budget Comparison Chart**: Visualize total FA budget under all playoff scenarios
- **Multi-Team Comparison**: Add multiple scenarios to compare teams side-by-side
- **Save/Load Configurations**: Export and import scenario configurations as JSON
- **Real-time Updates**: All calculations update immediately when inputs change

### 🔍 Player Lookup
- Find comparable players by position and overall rating
- Salary range analysis for specific player types
- Source tracking (free agent vs signed)
- Team affiliations
- Exportable player comparables

### 🎯 Market Equilibrium (NEW!)
The **Market Equilibrium Engine** brings realistic baseball economics to your league by modeling owner behavior, positional scarcity, and demand decay.

#### 📊 Market Liquidity Overview
- **Total Market Liquidity**: Sum of all teams' real buying power (not just available cash)
- **Top-Tier Liquidity**: What the top 10 richest teams can actually spend
- **Star Liquidity**: Money available from competitive teams (Win Now + Dynasty modes)
- **League $/WAR**: Real-time calculation of market value per win

#### 💼 Owner Sentiment Analysis
Analyzes how much teams will *actually* spend based on their situation:
- **Team Archetypes**: Dynasty (100-200%), Win Now (56-95%), Competitive (26-55%), Rebuild (10-25%)
- **Sentiment Multipliers**: Applied to available cash to get real buying power
- **Special Cases**: Over-budget teams (5% desperation mode), recent champions (+25% bonus)
- **Color-coded table**: Shows all teams with archetype, multiplier, real buying power, and max player spend
- **Smart calculations**: Accounts for win%, team mode, fan interest, and budget situation

#### 🧮 Fair Market Value (FMV) Calculator
Prevents overpaying by calculating realistic player values:
- **Position Weights**: Premium positions (SP, SS, CF) get 100%, relievers capped at 50-60%
- **Market Caps**: Elite players (5.0★) capped at top 5 teams' average, 4.0-4.5★ at top 15
- **Interactive calculator**: Input position, overall, WAR, and OOTP demand
- **Real-time feedback**: Shows if OOTP demand is too high/low vs. FMV
- **God Mode recommendations**: Suggests realistic signing values

#### ⏰ Desperation Decay Tracker
Simulates the "Boras Correction" - players lowering demands as spring training approaches:
- **Date slider**: Model any point in the offseason
- **Automatic decay**: 2% per day after January 15th for players demanding above market cap
- **Smart filtering**: View all players, decay applied, no decay yet, or high demand only
- **Position filters**: Focus on specific positions
- **Action recommendations**: ✅ Fair / ⚠️ Still High / 🔥 Force Sign
- **Reason tracking**: Explains why decay was/wasn't applied

#### 📥 Export for God Mode
Generate CSV reports for manual signing in Commissioner Mode:
- **Customizable exports**: Set minimum overall rating, include/exclude FMV and decay analysis
- **Complete data**: Player name, position, overall, WAR, original demand, FMV, adjusted demand, recommended action
- **Ready for God Mode**: Use FMV values to force-sign players at realistic prices

#### 📈 Market Summary Statistics
- Players with decay applied
- Average decay percentage
- Players above FMV
- Avg FMV vs Demand ratio

**Use Case Example**: 
A 5.0★ SP demands $40M, but only 2 teams have >$30M to spend. The engine calculates:
1. League $/WAR = $0.61M → Base value = $3.05M (5.0 WAR × $0.61M)
2. Position weight = 100% (SP) → Position-adjusted = $3.05M
3. Market cap = Top 5 teams avg = $33.85M → FMV = $3.05M (below cap)
4. January 15 passes, demand exceeds top 3 teams → Decay applies 2%/day
5. By February 1st: -34% decay → Adjusted demand = $26.4M
6. Recommendation: Sign at $3-4M (FMV range) in God Mode

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

The application has **9 main tabs**:

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

#### 🎯 Budget Scenarios (New!)
Model different financial scenarios for teams:
- **Select any team** to analyze
- **Configure scenario** - adjust wins/losses, postseason results, team mode, fan interest
- **View calculation breakdown** - see step-by-step how owner investment is calculated
- **Compare scenarios** - add multiple teams/scenarios to comparison table
- **Export configurations** - save and load scenario settings as JSON
- **Playoff bonus modeling** - see impact of postseason success on owner investment
- **Fire Sale mode** - simulate teardown scenarios with randomized owner reduction

#### 🎯 Market Equilibrium (New!)
Analyze realistic market dynamics with advanced economic modeling:
- **Market Liquidity Overview** - see real buying power across the league (total, top-tier, star liquidity)
- **Owner Sentiment Analysis** - table of all teams with archetype, sentiment multiplier, and real buying power
- **FMV Calculator** - calculate Fair Market Value for any player with position weights and market caps
- **Desperation Decay Tracker** - model demand reduction over time (2%/day after Jan 15)
- **Export for God Mode** - generate CSV with FMV recommendations for manual signings
- **Market Summary Statistics** - overview of decay applied, players above FMV, and market health

## Owner Investment System

The tool includes a sophisticated owner investment calculator that models how team owners inject capital based on three key factors:

### Formula
```
Owner Investment = Base Budget × Performance Factor × Mode Factor × Interest Factor
```

### Performance Factor (5-50%)
Based on last year's win percentage:
- **>100 wins (>.617)**: 50% - Championship window
- **94-100 wins (.580-.617)**: 40% - Contender
- **88-94 wins (.543-.580)**: 30% - Playoff team
- **82-88 wins (.506-.543)**: 20% - Bubble team
- **76-82 wins (.469-.506)**: 15% - Below average
- **70-76 wins (.432-.469)**: 10% - Struggling
- **<70 wins (<.432)**: 5% - Poor performance

### Mode Factor (10-100%)
Based on team strategy:
- **Win Now!**: 100% - Full investment to compete now
- **Build a Dynasty!**: 75% - Aggressive but strategic
- **Neutral**: 50% - Moderate approach
- **Rebuilding**: 10% - Minimal investment, focus on development

### Interest Factor (80-120%)
Based on fan interest (0-100 scale):
- **90-100**: 120% - Capitalize on passionate fanbase
- **75-89**: 110% - Strong support
- **60-74**: 100% - Solid baseline
- **45-59**: 90% - Fans cooling off
- **30-44**: 85% - Low interest
- **<30**: 80% - Apathetic fanbase

### Total FA Budget
```
Total FA Budget = (Budget - Payroll) + OOTP Budget Space + Cash from Trades + Owner Investment
```

### Example Calculations

**Chicago Cubs** (Win Now!, 103-59, Interest 100):
- Performance: 50% (>100 wins)
- Mode: 100% (Win Now!)
- Interest: 120% (100)
- Owner Investment: $100M × 0.50 × 1.00 × 1.20 = **$60M**
- Total FA Budget: $31.5M + $0 + $0 + $60M = **$91.5M**

**Nashville White Sox** (Win Now!, 97-65, Interest 97, OVER BUDGET):
- Performance: 40% (94-100 wins)
- Mode: 100% (Win Now!)
- Interest: 120% (97)
- Owner Investment: $100M × 0.40 × 1.00 × 1.20 = **$48M**
- Total: $20.9M + (-$19M) + $0 + $48M = **$49.9M** (owner bails them out!)

**St. Louis Cardinals** (Rebuilding, 65-97, Interest 68):
- Performance: 5% (<70 wins)
- Mode: 10% (Rebuilding)
- Interest: 100% (68)
- Owner Investment: $100M × 0.05 × 0.10 × 1.00 = **$0.5M**
- Total: $86.7M + $28M + $0 + $0.5M = **$115.2M** (but won't use it in rebuild)

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
