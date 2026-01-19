"""
OOTP Market Analysis Dashboard
Interactive web UI for analyzing salary market dynamics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from market_engine import MarketAnalyzer
from parser import OOTPParser

st.set_page_config(page_title="OOTP Market Analyzer", layout="wide", page_icon="⚾")

# Load data
@st.cache_data
def load_data():
    parser = OOTPParser(html_dir=".")
    teams = parser.parse_team_financials(filename="TeamFin.html")
    fas = parser.parse_free_agents(filename="fafinancials.html")
    signed = parser.parse_signed_players(filename="signed.html")
    return teams, fas, signed

try:
    teams, free_agents, signed = load_data()
    analyzer = MarketAnalyzer(teams, free_agents, signed)
    overview = analyzer.get_market_overview()
    
    # Main Title
    st.title("⚾ OOTP Salary Market Analyzer")
    st.markdown("### Understanding League-Wide Salary Dynamics")
    
    # Tab Navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Market Overview", 
        "💰 Position Analysis", 
        "⭐ Tier Analysis", 
        "🏢 Team Analysis",
        "🔍 Player Lookup"
    ])
    
    # ========== TAB 1: MARKET OVERVIEW ==========
    with tab1:
        st.header("Market Overview")
        
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Teams", f"{overview['total_teams']}")
        col2.metric("League Payroll", f"${overview['total_league_payroll']/1e6:.1f}M")
        col3.metric("FA Capacity", f"${overview['total_fa_capacity']/1e6:.1f}M")
        col4.metric("Budget Utilization", f"{(overview['total_league_payroll']/overview['total_league_budget'])*100:.1f}%")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Signed Players")
            st.metric("Total Signed", f"{overview['total_signed_players']:,}")
            st.metric("Avg Salary", f"${overview['avg_signed_salary']/1e6:.2f}M")
            st.metric("Median Salary", f"${overview['median_signed_salary']/1e6:.2f}M")
        
        with col2:
            st.subheader("Free Agents")
            st.metric("Total FAs", f"{overview['total_free_agents']:,}")
            st.metric("Avg Demand", f"${overview['avg_fa_demand']/1e6:.2f}M")
            st.metric("Total Demands", f"${overview['total_fa_demands']/1e6:.1f}M")
        
        with col3:
            st.subheader("Market Balance")
            supply_demand_ratio = overview['total_fa_capacity'] / overview['total_fa_demands'] if overview['total_fa_demands'] > 0 else 0
            st.metric("Supply/Demand Ratio", f"{supply_demand_ratio:.2f}x")
            st.caption("Ratio > 1.0 means buyer's market")
            
            market_type = "🟢 Buyer's Market" if supply_demand_ratio > 1.5 else "🟡 Balanced" if supply_demand_ratio > 0.8 else "🔴 Seller's Market"
            st.markdown(f"**Market Condition:** {market_type}")
        
        # Player Distribution
        st.subheader("Player Distribution by Quality")
        tier_stats = analyzer.get_tier_market_summary()
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Signed Players',
            x=tier_stats['tier'],
            y=tier_stats['signed_players'],
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            name='Free Agents',
            x=tier_stats['tier'],
            y=tier_stats['free_agents'],
            marker_color='orange'
        ))
        fig.update_layout(
            barmode='group',
            title="Player Count by Tier",
            xaxis_title="Player Tier",
            yaxis_title="Number of Players",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== TAB 2: POSITION ANALYSIS ==========
    with tab2:
        st.header("Position Market Analysis")
        
        position_stats = analyzer.get_position_market_summary()
        
        # Position selector
        selected_positions = st.multiselect(
            "Filter Positions",
            options=position_stats['position'].tolist(),
            default=position_stats['position'].head(5).tolist()
        )
        
        if selected_positions:
            filtered_pos = position_stats[position_stats['position'].isin(selected_positions)]
        else:
            filtered_pos = position_stats
        
        # Salary comparison chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Average Salary by Position")
            fig = px.bar(
                filtered_pos,
                x='position',
                y='avg_salary',
                color='total_players',
                title="Average Salary by Position",
                labels={'avg_salary': 'Avg Salary ($)', 'position': 'Position'},
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Median Salary by Position")
            fig = px.bar(
                filtered_pos,
                x='position',
                y='median_salary',
                color='total_players',
                title="Median Salary by Position",
                labels={'median_salary': 'Median Salary ($)', 'position': 'Position'},
                color_continuous_scale='Cividis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed position table
        st.subheader("Position Market Details")
        display_cols = ['position', 'total_players', 'signed_players', 'free_agents', 
                       'avg_salary', 'median_salary', 'min_salary', 'max_salary']
        
        # Format currency columns
        pos_display = filtered_pos[display_cols].copy()
        for col in ['avg_salary', 'median_salary', 'min_salary', 'max_salary']:
            pos_display[col] = pos_display[col].apply(lambda x: f"${x/1e6:.2f}M")
        
        st.dataframe(pos_display, use_container_width=True, height=400)
        
        # Export button
        csv = filtered_pos.to_csv(index=False)
        st.download_button(
            "📥 Download Position Analysis",
            csv,
            "position_analysis.csv",
            "text/csv"
        )
    
    # ========== TAB 3: TIER ANALYSIS ==========
    with tab3:
        st.header("Player Tier Market Analysis")
        
        tier_stats = analyzer.get_tier_market_summary()
        
        # Tier salary breakdown
        st.subheader("Salary by Player Tier")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.box(
                analyzer.all_players,
                x='overall',
                y='salary',
                title="Salary Distribution by Overall Rating",
                labels={'salary': 'Salary ($)', 'overall': 'Overall Rating (Stars)'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Tier comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Average Salary',
                x=tier_stats['tier'],
                y=tier_stats['avg_salary'],
                marker_color='lightcoral'
            ))
            fig.add_trace(go.Bar(
                name='Median Salary',
                x=tier_stats['tier'],
                y=tier_stats['median_salary'],
                marker_color='lightskyblue'
            ))
            fig.update_layout(
                barmode='group',
                title="Average vs Median Salary by Tier",
                xaxis_title="Tier",
                yaxis_title="Salary ($)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed tier table
        st.subheader("Tier Market Details")
        display_cols = ['tier', 'total_players', 'signed_players', 'free_agents',
                       'avg_salary', 'median_salary', 'p25_salary', 'p75_salary']
        
        tier_display = tier_stats[display_cols].copy()
        for col in ['avg_salary', 'median_salary', 'p25_salary', 'p75_salary']:
            tier_display[col] = tier_display[col].apply(lambda x: f"${x/1e6:.2f}M")
        
        st.dataframe(tier_display, use_container_width=True, height=300)
        
        # Tier insights
        st.subheader("Tier Insights")
        elite_tier = tier_stats[tier_stats['tier'].str.contains('Elite')].iloc[0]
        role_tier = tier_stats[tier_stats['tier'].str.contains('Role Player')].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Elite Players (5.0★)", f"{elite_tier['total_players']}")
        col1.metric("Elite Avg Salary", f"${elite_tier['avg_salary']/1e6:.2f}M")
        
        col2.metric("Role Players (<3.0★)", f"{role_tier['total_players']}")
        col2.metric("Role Avg Salary", f"${role_tier['avg_salary']/1e6:.2f}M")
        
        col3.metric("Elite Premium", f"{elite_tier['avg_salary']/role_tier['avg_salary']:.1f}x")
        col3.caption("Elite players earn this multiple of role players")
    
    # ========== TAB 4: TEAM ANALYSIS ==========
    with tab4:
        st.header("Team Spending Analysis")
        
        team_stats = analyzer.get_team_market_summary()
        
        # Team filters
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ['payroll', 'available_for_fa', 'budget_utilization', 'elite_players'],
                index=0
            )
        with col2:
            ascending = st.checkbox("Ascending order", value=False)
        
        sorted_teams = team_stats.sort_values(sort_by, ascending=ascending).head(20)
        
        # Top spenders visualization
        st.subheader(f"Teams by {sort_by.replace('_', ' ').title()}")
        
        fig = px.bar(
            sorted_teams.head(15),
            x='team_name',
            y=sort_by,
            color='budget_utilization',
            title=f"Top Teams by {sort_by.replace('_', ' ').title()}",
            labels={sort_by: sort_by.replace('_', ' ').title(), 'team_name': 'Team'},
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Budget utilization scatter
        st.subheader("Budget Utilization vs Payroll")
        fig = px.scatter(
            team_stats,
            x='payroll',
            y='budget_utilization',
            size='roster_size',
            color='elite_players',
            hover_name='team_name',
            title="Team Payroll vs Budget Utilization",
            labels={'payroll': 'Payroll ($)', 'budget_utilization': 'Budget Utilization (%)'},
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Team details table
        st.subheader("Team Financial Details")
        display_cols = ['team_name', 'payroll', 'budget', 'available_for_fa', 
                       'budget_utilization', 'roster_size', 'elite_players']
        
        team_display = sorted_teams[display_cols].copy()
        for col in ['payroll', 'budget', 'available_for_fa']:
            team_display[col] = team_display[col].apply(lambda x: f"${x/1e6:.1f}M")
        team_display['budget_utilization'] = team_display['budget_utilization'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(team_display, use_container_width=True, height=400)
        
        # Export
        csv = sorted_teams.to_csv(index=False)
        st.download_button(
            "📥 Download Team Analysis",
            csv,
            "team_analysis.csv",
            "text/csv"
        )
    
    # ========== TAB 5: PLAYER LOOKUP ==========
    with tab5:
        st.header("Player Comparables Lookup")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lookup_position = st.selectbox(
                "Position",
                options=sorted(analyzer.all_players['position'].unique())
            )
        
        with col2:
            min_overall = st.slider("Min Overall Rating", 0.0, 5.0, 3.0, 0.5)
        
        with col3:
            max_overall = st.slider("Max Overall Rating", 0.0, 5.0, 5.0, 0.5)
        
        # Get comparables
        comps = analyzer.get_comparable_players(lookup_position, min_overall, max_overall, limit=50)
        
        st.subheader(f"Comparable {lookup_position} Players ({min_overall}★ - {max_overall}★)")
        st.write(f"Found {len(comps)} players")
        
        # Format display
        if len(comps) > 0:
            comps_display = comps.copy()
            comps_display['salary'] = comps_display['salary'].apply(lambda x: f"${x/1e6:.2f}M")
            comps_display['overall'] = comps_display['overall'].apply(lambda x: f"{x}★")
            comps_display['potential'] = comps_display['potential'].apply(lambda x: f"{x}★")
            
            st.dataframe(comps_display, use_container_width=True, height=500)
            
            # Stats summary
            col1, col2, col3 = st.columns(3)
            col1.metric("Average Salary", f"${comps['salary'].mean()/1e6:.2f}M")
            col2.metric("Median Salary", f"${comps['salary'].median()/1e6:.2f}M")
            col3.metric("Salary Range", f"${comps['salary'].min()/1e6:.2f}M - ${comps['salary'].max()/1e6:.2f}M")
            
            # Export
            csv = comps.to_csv(index=False)
            st.download_button(
                "📥 Download Comparables",
                csv,
                f"{lookup_position}_comparables.csv",
                "text/csv"
            )
        else:
            st.info("No players found matching your criteria.")
    
    # Footer
    st.markdown("---")
    st.caption("OOTP Market Analyzer | Analyze salary market dynamics across your league")
    
except FileNotFoundError as e:
    st.error(f"❌ Error loading data files: {e}")
    st.info("📁 Please ensure TeamFin.html, fafinancials.html, and signed.html are in the same directory as this app.")
except Exception as e:
    st.error(f"❌ An error occurred: {e}")
    import traceback
    st.code(traceback.format_exc())
