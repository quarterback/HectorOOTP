"""
OOTP Market Dashboard
Interactive web UI for free agent analysis
"""

import streamlit as st
import pandas as pd
from market_engine import MarketEngine
from parser import OOTPParser

st.set_page_config(page_title="OOTP Free Agent Market", layout="wide")

# Sidebar - Market Settings
st.sidebar.header("⚙️ Market Settings")

market_mode = st.sidebar.selectbox(
    "Market Condition",
    ["Normal", "Contraction (-25%)", "Expansion (+15%)", "Fire Sale (-50%)"]
)

scarcity_overrides = {}
st.sidebar.subheader("Position Scarcity Multipliers")
for pos in ['C', 'SS', 'SP', 'RP']:
    scarcity_overrides[pos] = st. sidebar.slider(
        pos, 0.5, 1.5, 1.0 if pos not in ['C', 'SS'] else 1.15, 0.05
    )

# Main Dashboard
st.title("⚾ OOTP Free Agent Market Analyzer")

# Load data
@st.cache_data
def load_data():
    parser = OOTPParser()
    teams = parser.parse_team_financials()
    fas = parser.parse_free_agents()
    return teams, fas

teams, free_agents = load_data()
engine = MarketEngine(teams, free_agents)

# Metrics Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Market Cap", f"${engine.tmc / 1e6:.1f}M")
col2.metric("Free Agents", len(free_agents))
col3.metric("Total Demands", f"${free_agents['demand'].sum() / 1e6:.1f}M")
col4.metric("Avg Team Budget", f"${teams['available_for_fa'].mean() / 1e6:.1f}M")

# Filters
st.subheader("🔍 Player Filters")
col1, col2, col3 = st.columns(3)

positions = col1.multiselect("Position", free_agents['position']. unique(), default=["SP", "C", "SS"])
min_overall = col2.slider("Min Overall", 0.0, 5.0, 3.0, 0.5)
min_war = col3.slider("Min WAR", 0.0, 10.0, 1.0, 0.5)

filtered = free_agents[
    (free_agents['position'].isin(positions)) &
    (free_agents['overall'] >= min_overall) &
    (free_agents['war'] >= min_war)
]

# Generate Recommendations
st.subheader("💰 Market Recommendations")

results = []
for _, player in filtered.iterrows():
    price, reasoning = engine.calculate_market_price(player, scarcity_overrides)
    results.append({
        'Player': player['name'],
        'Pos': player['position'],
        'OVR': f"{player['overall']}⭐",
        'WAR': player['war'],
        'Demand': f"${player['demand'] / 1e6:.1f}M",
        'Market Price': f"${price / 1e6:.1f}M",
        'Delta': f"${(player['demand'] - price) / 1e6:+.1f}M",
        'Reasoning': reasoning
    })

df = pd.DataFrame(results)
st.dataframe(df, use_container_width=True, height=600)

# Download Button
csv = df.to_csv(index=False)
st.download_button("📥 Download Report", csv, "fa_report.csv", "text/csv")
