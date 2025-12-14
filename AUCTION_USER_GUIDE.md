# Auction System User Guide

## Overview

The Auction System allows you to run IPL-style free agency auctions for OOTP players. This feature enables you to simulate a competitive auction environment where teams (human-controlled or AI) bid on free agents, with realistic budget management and player valuations.

## Quick Start Guide

### 1. Prepare Your Data

First, export your free agents from OOTP:

1. In OOTP, navigate to **Free Agents** or the players you want to auction
2. Create a custom view that includes at least these columns:
   - **Name** (Required)
   - **POS** (Required) 
   - **Age** (Required)
   - **OVR**, **POT** (Recommended)
   - **Ratings**: STU, MOV, CON for pitchers; CON, POW, EYE for batters
   - **Stats**: WAR, ERA+ for pitchers; WAR, wRC+ for batters
   - **ORG** or **Team** (for team identification)

3. Export the view as CSV (File → Export → CSV)
4. Save as `free_agents.csv`

### 2. Launch the Auction

1. Open Rosterlytics and navigate to the **Auction** tab
2. Click **📁 Load Free Agents CSV** and select your exported CSV file
3. The system will automatically detect teams and set default budgets ($100M per team)

### 3. Configure Budgets

1. Click **💰 Configure Budgets** to customize team budgets
2. You can:
   - Set all teams to the same budget using "Set all teams to" field
   - Customize individual team budgets
   - Default settings: $100M per team, 75% minimum spend, 18-25 player roster size

### 4. Assign Teams

1. Click **👥 Assign Teams (Human/AI)** to control who participates
2. For each team, choose:
   - **Human**: You will manually place bids for this team
   - **AI**: Computer will automatically bid based on strategy
3. For AI teams, select a bidding strategy:
   - **Aggressive**: Bids up to 110% of valuation, targets stars (score ≥60)
   - **Balanced**: Bids up to 95% of valuation, spreads budget evenly
   - **Conservative**: Bids up to 85% of valuation, focuses on value plays

### 5. Start the Auction

1. Click **🎯 Start Auction** to begin
2. Players will be auctioned one at a time
3. For each player, you'll see:
   - Player info (Name, Position, Age, OVR, POT)
   - Suggested valuation based on Portal's scoring system
   - Current price and high bidder
   - Bid history

### 6. Bidding Process

**For Human Teams:**
1. Enter your bid amount in the "Your Bid" field
2. Select your team from the dropdown (if controlling multiple teams)
3. Click **Place Bid**
4. AI teams will automatically respond if interested

**For AI-Only Auctions:**
1. Click **🤖 Process AI Bids** to have AI teams bid
2. Continue clicking until no more bids are placed

**Moving Forward:**
- Click **✓ Sell Player** when bidding is complete to award player to highest bidder
- Click **→ Pass / Next** to skip a player without selling

### 7. Export Results

1. When auction completes, you'll see a summary of:
   - Total players sold/unsold
   - Total amount spent
   - Average price per player

2. Click **📤 Export Results to CSV** to save auction results
3. The exported CSV is formatted for OOTP import with:
   - Player Name
   - Winning Team
   - Contract Years (age-based)
   - Annual Average Value (AAV)

### 8. Import to OOTP

1. In OOTP, go to the import screen for free agent signings
2. Select your exported `auction_results.csv`
3. OOTP will process the signings based on the auction results

## Features in Detail

### Player Valuation

The system uses Portal's existing scoring systems to calculate player values:

- **Pitchers**: Evaluated using `pitchers.py` scoring (Stuff, Movement, Control, pitches)
- **Batters**: Evaluated using `batters.py` scoring (Contact, Power, Eye, defense, speed)
- **Position Scarcity**: Premium positions (C, SS, CF, SP) get higher valuations
- **Age Adjustments**: Younger players get higher future value multipliers

**Valuation Formula:**
```
Base Value = (Player Score / 100) × (Budget × 0.20)
Position Adjusted = Base Value × Position Scarcity
Age Adjusted = Position Adjusted × Age Multiplier
Suggested Price = Age Adjusted Value
```

### Budget Management

**Budget Constraints:**
- Teams must stay within their allocated budget
- Minimum spend requirement (default 75% of budget)
- Roster size limits (18-25 players)
- Smart reserve: System reserves $1M per remaining required roster spot

**Team Dashboard:**
Real-time tracking shows:
- Starting budget
- Amount spent
- Remaining budget
- Players acquired
- Roster spots remaining

### AI Bidding Strategies

**Aggressive (110% Strategy):**
- Bids up to 110% of player's calculated value
- Prioritizes star players (score ≥60)
- Will pay premium for high-need positions
- Risk: May overpay and exhaust budget early

**Balanced (95% Strategy):**
- Bids up to 95% of player's calculated value
- Spreads budget evenly across roster
- Considers position needs equally
- Best for: Competitive, well-rounded rosters

**Conservative (85% Strategy):**
- Bids up to 85% of player's calculated value
- Focuses on undervalued players
- Avoids spending sprees
- Best for: Budget builds, depth over stars

**AI Bidding Logic:**
- Tracks position needs (5 SP, 7 RP, 1 per position)
- Won't bid if position is filled (unless exceptional value)
- Randomness factor (10% chance to pass even when interested)
- Budget allocation (max 40% of remaining budget on one player)

### Contract Years Calculation

When exporting results, contract years are calculated based on age and price:

| Age | Price | Contract Years |
|-----|-------|----------------|
| ≤26 | ≥$20M | 7 years |
| ≤26 | $10-20M | 6 years |
| ≤26 | <$10M | 5 years |
| 27-29 | ≥$20M | 6 years |
| 27-29 | $10-20M | 5 years |
| 27-29 | <$10M | 4 years |
| 30-32 | ≥$15M | 4 years |
| 30-32 | $8-15M | 3 years |
| 30-32 | <$8M | 2 years |
| 33-35 | ≥$10M | 2 years |
| 33-35 | <$10M | 1 year |
| 36+ | Any | 1 year |

## Tips & Best Practices

### For Human Bidders

1. **Study Valuations**: Pay attention to the "Suggested Value" - it's based on Portal's proven scoring
2. **Position Scarcity**: Premium positions (C, SS, CF) are worth paying a premium for
3. **Don't Overspend Early**: Reserve budget for depth signings
4. **Fill Needs First**: Prioritize positions where you need starters
5. **Value Plays**: Young players with high POT are worth overpaying for

### Setting Up Balanced Auctions

1. **Equal Budgets**: Use same budget for all teams for fairness
2. **Mix Strategies**: Have variety of AI strategies (some aggressive, some conservative)
3. **Human Participation**: Control 1-2 teams manually for engagement
4. **Roster Limits**: Default 18-25 is good, but adjust if running smaller auction

### Testing the System

A sample CSV (`sample_free_agents.csv`) is included with the installation for testing:
- 3 sample players (1 SP, 1 C, 1 SS)
- Mix of ages and ratings
- Good for learning the interface before using real data

## Troubleshooting

### CSV Import Issues

**"Missing required fields" error:**
- Ensure your CSV has at minimum: Name, POS, Age columns
- Check that column headers are spelled exactly as expected
- Open CSV in a text editor to verify format

**"No players loaded" error:**
- Verify CSV is not empty
- Check that CSV is properly formatted (comma-delimited)
- Ensure file is UTF-8 encoded

### Budget Validation Errors

**"Cannot afford bid" error:**
- System reserves $1M per remaining required roster spot
- Check the team's remaining budget in the dashboard
- May need to pass on expensive players to afford rest of roster

**"Maximum roster size reached" error:**
- Team has acquired 25 players (maximum)
- No more players can be added to that team
- Other teams can still bid

### AI Not Bidding

**If AI teams aren't bidding:**
- Check that player meets AI quality threshold (Conservative: 40+, Balanced: 45+, Aggressive: 60+)
- Verify AI teams have budget remaining
- Check if AI team has filled that position already
- AI has 10% random pass rate - try "Process AI Bids" again

## Advanced Features

### Custom Budget Configurations

Save/load budget configurations using the budget system:

```python
# In Python console or custom script
from auction.budget import BudgetConfig

# Create custom config
config = BudgetConfig(
    team_budgets={
        'NYY': 150.0,  # Big market
        'TB': 80.0,    # Small market
        # ... other teams
    },
    min_spend_percentage=0.80,  # 80% minimum spend
    min_roster_size=20,
    max_roster_size=28
)

# Save for later use
config.save('my_league_budgets.json')

# Load previously saved config
config = BudgetConfig.load('my_league_budgets.json')
```

### Export Formats

Two export formats are available:

1. **OOTP Format** (default): Player Name, Team, Years, AAV - ready for OOTP import
2. **Detailed Format**: All player data plus auction price and winning team

Change format in code:
```python
export_auction_results_csv(results, 'output.csv', format_type='detailed')
```

## Integration with Existing Portal Features

The auction system integrates seamlessly with Portal's existing systems:

- **Player Scoring**: Uses same `batters.py` and `pitchers.py` calculations
- **Trade Value**: Leverages position scarcity and age multipliers from `trade_value.py`
- **Percentiles**: Player scores are calculated using league-wide context
- **GUI Theme**: Matches Portal's dark theme and styling

## Workflow Example

**Typical Commissioner-Mode Auction:**

1. **Pre-Season**: 
   - Export all free agents from OOTP to CSV
   - Set league-wide budget cap in Rosterlytics

2. **Auction Day**:
   - Assign all teams as AI with varied strategies
   - Run full AI auction (click "Process AI Bids" repeatedly)
   - Review results

3. **Post-Auction**:
   - Export results CSV
   - Import back into OOTP
   - Players are signed to their new teams

**Typical Mixed Human/AI Auction:**

1. Control 1-2 teams as Human
2. Let AI control the rest
3. Bid manually when interested
4. AI responds automatically after each human bid
5. Creates competitive, realistic auction environment

## Future Enhancements

Potential features for future versions:
- Pause/Resume auction functionality
- Undo last sale
- Mid-auction budget adjustments
- Historical auction statistics
- Keeper league support
- Draft pick trading integration

## Support

For issues or questions:
- Check this guide first
- Review the sample CSV to understand format
- Open an issue on GitHub with:
  - Description of the problem
  - Your CSV file (if import issue)
  - Steps to reproduce

---

**Auction System Version**: 1.0
**Compatible with**: Rosterlytics 2.7+
**Last Updated**: December 2024
