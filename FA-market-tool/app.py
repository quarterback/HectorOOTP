"""
OOTP Market Analysis Dashboard
Interactive web UI for analyzing salary market dynamics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import random
import datetime
from market_engine import MarketAnalyzer, OwnerInvestmentCalculator
from parser import OOTPParser
# Note: Theoretical modules kept as files but not imported
# from market_liquidity import MarketLiquidityAnalyzer
# from sentiment_logic import OwnerSentimentEngine
# from positional_scarcity import PositionalScarcityAdjuster
# from desperation_decay import DesperationDecayCalculator

# Win percentage tier bins for heatmap visualization
WIN_PCT_BINS = [0, 0.432, 0.469, 0.506, 0.543, 0.580, 0.617, 1.0]
WIN_PCT_LABELS = ['<70W', '70-76W', '76-82W', '82-88W', '88-94W', '94-100W', '>100W']

st.set_page_config(page_title="OOTP Market Analyzer", layout="wide", page_icon="⚾")

# Load data
@st.cache_data
def load_data():
    parser = OOTPParser(html_dir=".")
    teams = parser.parse_team_financials(filename="TeamFin.html")
    fas = parser.parse_free_agents(filename="fafinancials.html")
    signed = parser.parse_signed_players(filename="signed.html")
    
    # Enrich signed players with full team data
    signed = parser.enrich_signed_players_with_team_data(signed, teams)
    
    return teams, fas, signed

try:
    teams, free_agents, signed = load_data()
    analyzer = MarketAnalyzer(teams, free_agents, signed)
    overview = analyzer.get_market_overview()
    
    # Main Title
    st.title("⚾ OOTP Salary Market Analyzer")
    st.markdown("### Understanding League-Wide Salary Dynamics")
    
    # Tab Navigation
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Market Overview",
        "💰 Salary Bands",
        "🎯 Player Pricer",
        "📍 Position Analysis",
        "⭐ Tier Analysis",
        "🏢 Team Analysis",
        "🔍 Player Lookup",
        "🎯 Budget Scenarios",
        "💡 FA Pricing Guide"
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
    
    # ========== TAB 2: SALARY BANDS ==========
    with tab2:
        st.header("💰 Salary Bands Analysis")
        st.markdown("Understand salary ranges for different position/tier combinations")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            position_stats = analyzer.get_position_market_summary()
            selected_positions_bands = st.multiselect(
                "Select Positions",
                options=sorted(position_stats['position'].tolist()),
                default=sorted(position_stats['position'].tolist())[:3]
            )
        
        with col2:
            tier_options = [
                'Elite (5.0★)', 
                'Star (4.5★)', 
                'Above Average (4.0★)', 
                'Solid Average (3.5★)', 
                'Average (3.0★)', 
                'Below Average (2.5★)', 
                'Backup/Depth (2.0★)', 
                'Fringe (1.5★)', 
                'Minor League (1.0★)', 
                'Organizational (0.5★)'
            ]
            selected_tiers = st.multiselect(
                "Select Tiers",
                options=tier_options,
                default=tier_options[:3]
            )
        
        with col3:
            source_filter = st.selectbox(
                "Show",
                options=['Both', 'Signed Only', 'Free Agents Only'],
                index=0
            )
        
        # Convert source filter to API parameter
        source_param = 'both' if source_filter == 'Both' else ('signed' if source_filter == 'Signed Only' else 'fa')
        
        # Get salary bands data
        if selected_positions_bands and selected_tiers:
            # Box plots for each position/tier combination
            st.subheader("Salary Distribution Box Plots")
            
            for pos in selected_positions_bands:
                bands_data = analyzer.get_salary_bands(position=pos, source='both')
                bands_filtered = bands_data[bands_data['tier'].isin(selected_tiers)]
                
                if len(bands_filtered) > 0:
                    st.markdown(f"**{pos}**")
                    
                    # Create box plot data
                    fig = go.Figure()
                    
                    for tier in selected_tiers:
                        tier_data = bands_filtered[bands_filtered['tier'] == tier]
                        
                        for _, row in tier_data.iterrows():
                            # Create box plot trace
                            if source_filter == 'Both' or \
                               (source_filter == 'Signed Only' and row['source'] == 'Signed') or \
                               (source_filter == 'Free Agents Only' and row['source'] == 'Free Agent'):
                                
                                name = f"{tier} - {row['source']}"
                                fig.add_trace(go.Box(
                                    name=name,
                                    q1=[row['p25']],
                                    median=[row['median']],
                                    q3=[row['p75']],
                                    lowerfence=[row['min']],
                                    upperfence=[row['max']],
                                    mean=[row['avg']],
                                    x=[tier],
                                    marker_color='lightblue' if row['source'] == 'Signed' else 'orange',
                                    showlegend=True
                                ))
                    
                    fig.update_layout(
                        xaxis_title="Tier",
                        yaxis_title="Salary ($)",
                        height=350,
                        showlegend=True,
                        boxmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Salary Band Matrix Table
            st.subheader("Salary Band Matrix (Median Values)")
            st.markdown("Position (rows) × Tier (columns)")
            
            matrix = analyzer.get_position_tier_matrix(metric='median', source=source_param)
            
            if not matrix.empty:
                # Filter to selected positions
                if selected_positions_bands:
                    matrix_filtered = matrix[matrix.index.isin(selected_positions_bands)]
                else:
                    matrix_filtered = matrix
                
                # Format as currency
                matrix_display = matrix_filtered.copy()
                for col in matrix_display.columns:
                    matrix_display[col] = matrix_display[col].apply(lambda x: f"${x/1e6:.2f}M" if pd.notna(x) else "-")
                
                st.dataframe(matrix_display, use_container_width=True, height=400)
                
                # Download button for matrix
                csv = matrix_filtered.to_csv()
                st.download_button(
                    "📥 Download Salary Band Matrix",
                    csv,
                    "salary_band_matrix.csv",
                    "text/csv"
                )
            
            # # Market Gap Analysis
            # st.subheader("Market Gap: Free Agents vs Signed Players")
            # st.markdown("Shows how much more FAs are demanding compared to rostered players")
            # 
            # gap_analysis = analyzer.get_market_gap_analysis()
            # 
            # if len(gap_analysis) > 0:
            #     # Filter to selected positions and tiers
            #     gap_filtered = gap_analysis[
            #         gap_analysis['position'].isin(selected_positions_bands) &
            #         gap_analysis['tier'].isin(selected_tiers)
            #     ]
            #     
            #     if len(gap_filtered) > 0:
            #         # Create comparison chart
            #         fig = go.Figure()
            #         
            #         # Group by tier for cleaner visualization
            #         for tier in selected_tiers:
            #             tier_gap = gap_filtered[gap_filtered['tier'] == tier]
            #             
            #             if len(tier_gap) > 0:
            #                 fig.add_trace(go.Bar(
            #                     name=f'{tier} - Signed',
            #                     x=tier_gap['position'],
            #                     y=tier_gap['signed_median'],
            #                     marker_color='lightblue',
            #                     showlegend=True if tier == selected_tiers[0] else False,
            #                     legendgroup='signed',
            #                     legendgrouptitle_text='Signed'
            #                 ))
            #                 
            #                 fig.add_trace(go.Bar(
            #                     name=f'{tier} - FA',
            #                     x=tier_gap['position'],
            #                     y=tier_gap['fa_median'],
            #                     marker_color='orange',
            #                     showlegend=True if tier == selected_tiers[0] else False,
            #                     legendgroup='fa',
            #                     legendgrouptitle_text='Free Agent'
            #                 ))
            #         
            #         fig.update_layout(
            #             barmode='group',
            #             title="Median Salary: Signed vs Free Agent by Position",
            #             xaxis_title="Position",
            #             yaxis_title="Median Salary ($)",
            #             height=400
            #         )
            #         st.plotly_chart(fig, use_container_width=True)
            #         
            #         # Gap percentage table
            #         st.markdown("**FA Premium Table**")
            #         gap_display = gap_filtered[['position', 'tier', 'signed_median', 'fa_median', 'gap_amount', 'gap_percentage']].copy()
            #         gap_display['signed_median'] = gap_display['signed_median'].apply(lambda x: f"${x/1e6:.2f}M")
            #         gap_display['fa_median'] = gap_display['fa_median'].apply(lambda x: f"${x/1e6:.2f}M")
            #         gap_display['gap_amount'] = gap_display['gap_amount'].apply(lambda x: f"${x/1e6:.2f}M")
            #         gap_display['gap_percentage'] = gap_display['gap_percentage'].apply(lambda x: f"{x:.1f}%")
            #         
            #         st.dataframe(gap_display, use_container_width=True, height=300)
            #         
            #         # Download gap analysis
            #         csv = gap_filtered.to_csv(index=False)
            #         st.download_button(
            #             "📥 Download Market Gap Analysis",
            #             csv,
            #             "market_gap_analysis.csv",
            #             "text/csv"
            #         )
        else:
            st.info("Please select at least one position and one tier to view salary bands.")
    
    # ========== TAB 3: PLAYER PRICER ==========
    with tab3:
        st.header("🎯 Player Pricer Tool")
        st.markdown("Get instant market value estimates for players based on comparables")
        
        # Input form
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pricer_position = st.selectbox(
                "Position",
                options=sorted(analyzer.all_players['position'].unique()),
                key='pricer_position'
            )
        
        with col2:
            overall_rating = st.slider(
                "Overall Rating (Stars)",
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
                key='pricer_overall'
            )
        
        with col3:
            use_age_filter = st.checkbox("Filter by Age", value=False)
        
        # Age filters (optional)
        age_min = None
        age_max = None
        if use_age_filter:
            col1, col2 = st.columns(2)
            with col1:
                age_min = st.number_input("Min Age", min_value=18, max_value=45, value=25, key='pricer_age_min')
            with col2:
                age_max = st.number_input("Max Age", min_value=18, max_value=45, value=32, key='pricer_age_max')
        
        # Search range (allow user to adjust)
        rating_range = st.slider(
            "Rating Search Range (±)",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.5,
            help="Expand or narrow the search for comparable players"
        )
        
        overall_min = max(0.0, overall_rating - rating_range)
        overall_max = min(5.0, overall_rating + rating_range)
        
        # Get pricing data
        pricing = analyzer.get_player_pricing(
            pricer_position, 
            overall_min, 
            overall_max,
            age_min,
            age_max
        )
        
        if pricing['total_comps'] > 0:
            # Display key metrics
            st.subheader("Market Value Estimate")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Fair Value (Median)", f"${pricing['median']/1e6:.2f}M")
            col2.metric("25th Percentile", f"${pricing['p25']/1e6:.2f}M")
            col3.metric("75th Percentile", f"${pricing['p75']/1e6:.2f}M")
            col4.metric("Average", f"${pricing['avg']/1e6:.2f}M")
            
            # Market context
            st.subheader("Market Context")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Comparables", f"{pricing['total_comps']}")
            col2.metric("Signed Players", f"{pricing['signed_comps']}")
            col3.metric("Free Agents", f"{pricing['fa_comps']}")
            
            if pricing['signed_comps'] > 0 and pricing['fa_comps'] > 0:
                fa_premium = ((pricing['fa_avg'] - pricing['signed_avg']) / pricing['signed_avg'] * 100)
                st.info(f"📊 **Market Insight:** Free agents at this level are demanding {fa_premium:.1f}% more than signed players earn")
            
            # Salary distribution visualization
            st.subheader("Salary Distribution")
            
            comps_df = pricing['comparables']
            fig = px.histogram(
                comps_df,
                x='salary',
                color='source',
                nbins=20,
                title=f"Salary Distribution for {pricer_position} ({overall_min}★ - {overall_max}★)",
                labels={'salary': 'Salary ($)', 'source': 'Source'},
                color_discrete_map={'Signed': 'lightblue', 'Free Agent': 'orange'}
            )
            
            # Add median line
            fig.add_vline(
                x=pricing['median'],
                line_dash="dash",
                line_color="red",
                annotation_text=f"Median: ${pricing['median']/1e6:.2f}M"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Percentile calculator
            st.subheader("Offer Percentile Calculator")
            st.markdown("Enter a proposed salary to see where it ranks among comparables")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                proposed_offer = st.number_input(
                    "Proposed Salary ($M)",
                    min_value=0.0,
                    max_value=50.0,
                    value=float(pricing['median']/1e6),
                    step=0.1,
                    key='proposed_offer'
                ) * 1e6
            
            with col2:
                percentile = analyzer.calculate_offer_percentile(proposed_offer, comps_df)
                st.metric("Percentile Rank", f"{percentile:.1f}%")
                
                if percentile < 25:
                    st.warning("⚠️ **Below Market** - This offer is in the bottom 25%")
                elif percentile < 50:
                    st.info("💡 **Fair/Low** - Below median but reasonable")
                elif percentile < 75:
                    st.success("✅ **Fair/High** - Above median, competitive")
                else:
                    st.warning("💰 **Premium Offer** - Top 25% of market")
            
            # Comparable players table
            st.subheader("Comparable Players")
            st.markdown(f"Showing up to 20 most similar players")
            
            # Use team_full_name if available, otherwise fall back to team
            display_cols = ['name', 'position', 'overall', 'potential', 'age', 'salary', 'source']
            if 'team_full_name' in comps_df.columns:
                display_cols.append('team_full_name')
                comps_display = comps_df[display_cols].head(20).copy()
                comps_display.rename(columns={'team_full_name': 'team'}, inplace=True)
            else:
                display_cols.append('team')
                comps_display = comps_df[display_cols].head(20).copy()
            
            comps_display['salary'] = comps_display['salary'].apply(lambda x: f"${x/1e6:.2f}M")
            comps_display['overall'] = comps_display['overall'].apply(lambda x: f"{x}★")
            comps_display['potential'] = comps_display['potential'].apply(lambda x: f"{x}★")
            
            st.dataframe(comps_display, use_container_width=True, height=400)
            
            # Download button
            csv = pricing['comparables'].to_csv(index=False)
            st.download_button(
                "📥 Download Comparables",
                csv,
                f"{pricer_position}_{overall_rating}star_comparables.csv",
                "text/csv"
            )
        else:
            st.warning("⚠️ No comparable players found with these criteria. Try adjusting the rating range or removing age filters.")
    
    # ========== TAB 4: POSITION ANALYSIS ==========
    with tab4:
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
    
    # ========== TAB 5: TIER ANALYSIS ==========
    with tab5:
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
        
        # Market Gap Visualization - NEW ENHANCEMENT
        st.subheader("Market Gap: Signed vs Free Agent Salaries")
        st.markdown("Side-by-side comparison showing the difference between rostered players and free agent demands")
        
        # Get signed and FA stats for each tier
        signed_by_tier = []
        fa_by_tier = []
        tier_names = []
        
        for _, tier_row in tier_stats.iterrows():
            tier_names.append(tier_row['tier'])
            signed_by_tier.append(tier_row.get('avg_signed_salary', 0))
            fa_by_tier.append(tier_row.get('avg_fa_demand', 0))
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Signed Players',
            x=tier_names,
            y=signed_by_tier,
            marker_color='lightblue',
            text=[f"${val/1e6:.2f}M" if val > 0 else "" for val in signed_by_tier],
            textposition='outside'
        ))
        fig.add_trace(go.Bar(
            name='Free Agents',
            x=tier_names,
            y=fa_by_tier,
            marker_color='orange',
            text=[f"${val/1e6:.2f}M" if val > 0 else "" for val in fa_by_tier],
            textposition='outside'
        ))
        
        fig.update_layout(
            barmode='group',
            title="Average Salary: Signed vs Free Agent by Tier",
            xaxis_title="Player Tier",
            yaxis_title="Average Salary ($)",
            height=400,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # FA Premium Table - NEW ENHANCEMENT
        st.subheader("FA Premium by Tier")
        st.markdown("Shows the percentage difference between FA demands and signed player salaries")
        
        fa_premium_data = []
        for _, tier_row in tier_stats.iterrows():
            signed_avg = tier_row.get('avg_signed_salary', 0)
            fa_avg = tier_row.get('avg_fa_demand', 0)
            
            if signed_avg > 0 and fa_avg > 0:
                premium_pct = ((fa_avg - signed_avg) / signed_avg) * 100
                premium_amount = fa_avg - signed_avg
                
                fa_premium_data.append({
                    'Tier': tier_row['tier'],
                    'Signed Avg': signed_avg,
                    'FA Avg': fa_avg,
                    'Premium Amount': premium_amount,
                    'Premium %': premium_pct
                })
        
        if fa_premium_data:
            premium_df = pd.DataFrame(fa_premium_data)
            premium_display = premium_df.copy()
            premium_display['Signed Avg'] = premium_display['Signed Avg'].apply(lambda x: f"${x/1e6:.2f}M")
            premium_display['FA Avg'] = premium_display['FA Avg'].apply(lambda x: f"${x/1e6:.2f}M")
            premium_display['Premium Amount'] = premium_display['Premium Amount'].apply(lambda x: f"${x/1e6:.2f}M")
            premium_display['Premium %'] = premium_display['Premium %'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(premium_display, use_container_width=True, height=250)
        
        # Salary Range Boxes - NEW ENHANCEMENT
        st.subheader("Salary Ranges by Tier (25th-75th Percentile)")
        st.markdown("Shows typical salary ranges for each tier, comparing signed and FA players")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Signed Players**")
            signed_ranges = []
            for _, tier_row in tier_stats.iterrows():
                p25 = tier_row.get('p25_salary', 0)
                p75 = tier_row.get('p75_salary', 0)
                median = tier_row.get('median_salary', 0)
                
                signed_ranges.append({
                    'Tier': tier_row['tier'],
                    '25th %ile': f"${p25/1e6:.2f}M",
                    'Median': f"${median/1e6:.2f}M",
                    '75th %ile': f"${p75/1e6:.2f}M",
                    'Range': f"${p25/1e6:.2f}M - ${p75/1e6:.2f}M"
                })
            
            st.dataframe(pd.DataFrame(signed_ranges), use_container_width=True, height=250)
        
        with col2:
            st.markdown("**Free Agents**")
            # Get FA-specific ranges
            fa_only_players = analyzer.all_players[analyzer.all_players['source'] == 'Free Agent']
            
            fa_ranges = []
            tiers_def = [
                ('Elite (5.0★)', 5.0, 5.0),
                ('Star (4.5★)', 4.5, 4.5),
                ('Above Average (4.0★)', 4.0, 4.0),
                ('Solid Average (3.5★)', 3.5, 3.5),
                ('Average (3.0★)', 3.0, 3.0),
                ('Below Average (2.5★)', 2.5, 2.5),
                ('Backup/Depth (2.0★)', 2.0, 2.0),
                ('Fringe (1.5★)', 1.5, 1.5),
                ('Minor League (1.0★)', 1.0, 1.0),
                ('Organizational (0.5★)', 0.5, 0.5),
            ]
            
            for tier_name, min_ovr, max_ovr in tiers_def:
                tier_fas = fa_only_players[
                    (fa_only_players['overall'] >= min_ovr) & 
                    (fa_only_players['overall'] <= max_ovr)
                ]
                
                if len(tier_fas) > 0:
                    p25 = tier_fas['salary'].quantile(0.25)
                    p75 = tier_fas['salary'].quantile(0.75)
                    median = tier_fas['salary'].median()
                    
                    fa_ranges.append({
                        'Tier': tier_name,
                        '25th %ile': f"${p25/1e6:.2f}M",
                        'Median': f"${median/1e6:.2f}M",
                        '75th %ile': f"${p75/1e6:.2f}M",
                        'Range': f"${p25/1e6:.2f}M - ${p75/1e6:.2f}M"
                    })
                else:
                    fa_ranges.append({
                        'Tier': tier_name,
                        '25th %ile': '-',
                        'Median': '-',
                        '75th %ile': '-',
                        'Range': 'No data'
                    })
            
            st.dataframe(pd.DataFrame(fa_ranges), use_container_width=True, height=250)
        
        # Tier insights
        st.subheader("Tier Insights")
        elite_tier = tier_stats[tier_stats['tier'].str.contains('Elite')].iloc[0]
        org_tier = tier_stats[tier_stats['tier'].str.contains('Organizational')].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Elite Players (5.0★)", f"{elite_tier['total_players']}")
        col1.metric("Elite Avg Salary", f"${elite_tier['avg_salary']/1e6:.2f}M")
        
        col2.metric("Organizational Players (0.5★)", f"{org_tier['total_players']}")
        col2.metric("Org Avg Salary", f"${org_tier['avg_salary']/1e6:.2f}M")
        
        col3.metric("Elite Premium", f"{elite_tier['avg_salary']/org_tier['avg_salary']:.1f}x")
        col3.caption("Elite players earn this multiple of organizational players")
    
    # ========== TAB 6: TEAM ANALYSIS ==========
    with tab6:
        st.header("🏢 Team Spending & Owner Investment Analysis")
        
        team_stats = analyzer.get_team_market_summary()
        
        # Team filters and controls
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox(
                "Sort by",
                ['total_fa_budget', 'owner_investment', 'aggressiveness_score', 'payroll', 
                 'available_for_fa', 'budget_utilization', 'win_pct', 'fan_interest'],
                index=0,
                help="Choose metric to sort teams by"
            )
        with col2:
            ascending = st.checkbox("Ascending order", value=False)
        
        with col3:
            # Configurable slider for number of teams to display
            num_teams = st.slider(
                "Number of teams to display",
                min_value=10,
                max_value=len(team_stats),
                value=min(20, len(team_stats)),
                step=1,
                help="Control how many teams are shown in charts and tables"
            )
        
        sorted_teams = team_stats.sort_values(sort_by, ascending=ascending).head(num_teams)
        
        # Key Metrics Overview
        st.subheader("League Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Teams", f"{len(team_stats)}")
        col2.metric("Total Owner Investment", f"${team_stats['owner_investment'].sum()/1e6:.1f}M")
        col3.metric("Total FA Budget Available", f"${team_stats['total_fa_budget'].sum()/1e6:.1f}M")
        col4.metric("Avg Aggressiveness", f"{team_stats['aggressiveness_score'].mean():.1f}/100")
        
        # Main visualization
        st.subheader(f"Top {num_teams} Teams by {sort_by.replace('_', ' ').title()}")
        
        # Stacked bar chart for Total FA Budget breakdown
        if sort_by == 'total_fa_budget' or sort_by == 'owner_investment':
            st.markdown("**Total FA Budget Breakdown**")
            fig = go.Figure()
            
            # Create stacked bars
            fig.add_trace(go.Bar(
                name='Base Available',
                x=sorted_teams['team_name'],
                y=sorted_teams['base_fa_budget'],
                marker_color='lightblue'
            ))
            fig.add_trace(go.Bar(
                name='OOTP Budget Space',
                x=sorted_teams['team_name'],
                y=sorted_teams['budget_space'],
                marker_color='lightgreen'
            ))
            fig.add_trace(go.Bar(
                name='Trade Cash',
                x=sorted_teams['team_name'],
                y=sorted_teams['cash_from_trades'],
                marker_color='lightyellow'
            ))
            fig.add_trace(go.Bar(
                name='Owner Investment',
                x=sorted_teams['team_name'],
                y=sorted_teams['owner_investment'],
                marker_color='gold'
            ))
            
            fig.update_layout(
                barmode='stack',
                title=f"Total FA Budget Breakdown - Top {num_teams} Teams",
                xaxis_title="Team",
                yaxis_title="Amount ($)",
                height=500,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Regular bar chart for other metrics
            fig = px.bar(
                sorted_teams,
                x='team_name',
                y=sort_by,
                color='aggressiveness_score',
                title=f"Top {num_teams} Teams by {sort_by.replace('_', ' ').title()}",
                labels={sort_by: sort_by.replace('_', ' ').title(), 'team_name': 'Team'},
                color_continuous_scale='RdYlGn',
                hover_data=['mode', 'win_pct', 'fan_interest']
            )
            fig.update_layout(height=500, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plot: Win % vs Owner Investment (colored by mode)
        st.subheader("Win % vs Owner Investment")
        
        # Create mode color mapping
        mode_colors = {
            'Win Now!': '#FFD700',  # Gold
            'Build a Dynasty!': '#4169E1',  # Royal Blue
            'Neutral': '#808080',  # Gray
            'Rebuilding': '#A9A9A9'  # Dark Gray
        }
        
        fig = px.scatter(
            sorted_teams,
            x='win_pct',
            y='owner_investment',
            color='mode',
            size='fan_interest',
            hover_data=['team_name', 'aggressiveness_score', 'total_fa_budget'],
            title=f"Win % vs Owner Investment (Top {num_teams} Teams)",
            labels={'win_pct': 'Win %', 'owner_investment': 'Owner Investment ($)', 'fan_interest': 'Fan Interest'},
            color_discrete_map=mode_colors
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap: Performance Factor × Mode Factor
        st.subheader("Team Strategy Heatmap")
        st.markdown("Shows relationship between performance (win %) and team mode")
        
        # Create pivot table for heatmap
        heatmap_data = sorted_teams.pivot_table(
            values='aggressiveness_score',
            index='mode',
            columns=pd.cut(sorted_teams['win_pct'], bins=WIN_PCT_BINS, labels=WIN_PCT_LABELS),
            aggfunc='mean'
        )
        
        if not heatmap_data.empty:
            fig = px.imshow(
                heatmap_data,
                labels=dict(x="Win Tier", y="Team Mode", color="Avg Aggressiveness"),
                title="Average Aggressiveness Score by Mode and Performance",
                color_continuous_scale='RdYlGn',
                aspect='auto'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        # Team details table with all new columns
        st.subheader("Team Financial Details")
        
        # Select columns to display
        display_cols = [
            'team_name', 'mode', 'last_year_wins', 'last_year_losses', 'win_pct',
            'fan_interest', 'payroll', 'budget', 'budget_space', 'cash_from_trades',
            'performance_factor', 'mode_factor', 'interest_factor',
            'owner_investment', 'base_fa_budget', 'total_fa_budget', 'aggressiveness_score'
        ]
        
        team_display = sorted_teams[display_cols].copy()
        
        # Format columns
        team_display['last_year_record'] = team_display.apply(
            lambda x: f"{x['last_year_wins']}-{x['last_year_losses']}", axis=1
        )
        team_display['win_pct'] = team_display['win_pct'].apply(lambda x: f"{x:.3f}")
        team_display['performance_factor'] = team_display['performance_factor'].apply(lambda x: f"{x:.0%}")
        team_display['mode_factor'] = team_display['mode_factor'].apply(lambda x: f"{x:.0%}")
        team_display['interest_factor'] = team_display['interest_factor'].apply(lambda x: f"{x:.0%}")
        
        for col in ['payroll', 'budget', 'budget_space', 'cash_from_trades', 'owner_investment', 'base_fa_budget', 'total_fa_budget']:
            team_display[col] = team_display[col].apply(lambda x: f"${x/1e6:.1f}M")
        
        team_display['aggressiveness_score'] = team_display['aggressiveness_score'].apply(lambda x: f"{x:.1f}")
        
        # Reorder columns for display
        final_display = team_display[[
            'team_name', 'mode', 'last_year_record', 'win_pct', 'fan_interest',
            'performance_factor', 'mode_factor', 'interest_factor',
            'payroll', 'budget', 'budget_space', 'cash_from_trades',
            'owner_investment', 'total_fa_budget', 'aggressiveness_score'
        ]]
        
        # Add visual indicators using color styling
        def color_aggressiveness(val):
            """Color code aggressiveness scores"""
            if isinstance(val, str):
                try:
                    num_val = float(val)
                    if num_val >= 80:
                        return 'background-color: #90EE90'  # Light green
                    elif num_val >= 50:
                        return 'background-color: #FFFFE0'  # Light yellow
                    elif num_val >= 20:
                        return 'background-color: #FFE4B5'  # Moccasin
                    else:
                        return 'background-color: #FFB6C1'  # Light pink
                except:
                    pass
            return ''
        
        def color_budget_space(val):
            """Highlight negative budget space"""
            if isinstance(val, str) and '-' in val:
                return 'background-color: #FFB6C1; font-weight: bold'  # Light pink
            return ''
        
        # Apply styling
        styled_display = final_display.style.applymap(
            color_aggressiveness, subset=['aggressiveness_score']
        ).applymap(
            color_budget_space, subset=['budget_space']
        )
        
        st.dataframe(styled_display, use_container_width=True, height=500)
        
        # Add explanatory notes
        with st.expander("📖 Column Explanations"):
            st.markdown("""
            - **Mode**: Team strategy (Win Now!, Dynasty, Neutral, Rebuilding)
            - **Performance Factor**: Based on last year's win % (5%-50%)
            - **Mode Factor**: Multiplier based on team strategy (10%-100%)
            - **Interest Factor**: Based on fan interest (80%-120%)
            - **Owner Investment**: Budget × Performance × Mode × Interest
            - **Budget Space**: OOTP-calculated space (can be negative if over budget!)
            - **Total FA Budget**: Base + Budget Space + Trade Cash + Owner Investment
            - **Aggressiveness Score**: 0-100 score combining all factors
            
            **Color Coding:**
            - 🟢 Green (80-100): Very aggressive owners
            - 🟡 Yellow (50-79): Moderately aggressive
            - 🟠 Orange (20-49): Conservative
            - 🔴 Pink (<20): Very conservative
            - ⚠️ Pink budget space: Team is over budget!
            """)
        
        # Export
        csv = sorted_teams.to_csv(index=False)
        st.download_button(
            "📥 Download Team Analysis",
            csv,
            "team_analysis.csv",
            "text/csv"
        )
    
    # ========== TAB 7: PLAYER LOOKUP ==========
    with tab7:
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
            
            # Use team_full_name if available
            if 'team_full_name' in comps_display.columns:
                # Replace 'team' column with team_full_name for display
                comps_display['team'] = comps_display['team_full_name']
                comps_display = comps_display.drop(columns=['team_full_name'])
            
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
    
    # ========== TAB 8: BUDGET SCENARIOS ==========
    with tab8:
        st.header("🎯 Budget Scenario Calculator")
        st.markdown("Model different scenarios and calculate owner investment under various conditions")
        
        # Team Selection Panel
        st.subheader("Team Selection")
        
        team_list = sorted(team_stats['team_name'].tolist())
        selected_team_name = st.selectbox(
            "Select Team",
            team_list,
            help="Choose a team to analyze"
        )
        
        # Get selected team data
        selected_team = team_stats[team_stats['team_name'] == selected_team_name].iloc[0]
        
        # Display current team stats
        st.markdown(f"**Current Team Stats for {selected_team_name}:**")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Payroll", f"${selected_team['payroll']/1e6:.1f}M")
        col2.metric("Budget", f"${selected_team['budget']/1e6:.1f}M")
        col3.metric("Mode", selected_team['mode'])
        col4.metric("Fan Interest", f"{selected_team['fan_interest']}/100")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Last Year Record", f"{selected_team['last_year_wins']}-{selected_team['last_year_losses']}")
        col2.metric("Win %", f"{selected_team['win_pct']:.3f}")
        col3.metric("Current Owner Investment", f"${selected_team['owner_investment']/1e6:.1f}M")
        
        st.markdown("---")
        
        # Scenario Configuration
        st.subheader("Scenario Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Last Season Performance**")
            scenario_wins = st.number_input(
                "Wins",
                min_value=0,
                max_value=162,
                value=int(selected_team['last_year_wins']),
                help="Number of wins in the scenario"
            )
            scenario_losses = st.number_input(
                "Losses",
                min_value=0,
                max_value=162,
                value=int(selected_team['last_year_losses']),
                help="Number of losses in the scenario"
            )
            
            scenario_win_pct = scenario_wins / (scenario_wins + scenario_losses) if (scenario_wins + scenario_losses) > 0 else 0.500
            st.metric("Win %", f"{scenario_win_pct:.3f}")
        
        with col2:
            st.markdown("**Postseason Result**")
            postseason_options = {
                "No Playoffs": 0.0,
                "Wild Card Team": 0.15,
                "Division Champion": 0.25,
                "Pennant Winner": 0.35,
                "World Series Champion": 0.50,
                "🔥 FIRE SALE": -1.0  # Special flag
            }
            
            postseason_result = st.radio(
                "Select postseason outcome",
                list(postseason_options.keys()),
                index=0,
                help="Postseason success adds bonus to owner investment"
            )
            
            postseason_bonus = postseason_options[postseason_result]
            
            # Fire sale configuration
            if postseason_result == "🔥 FIRE SALE":
                st.warning("⚠️ Fire Sale Mode: Owner will pocket significant funds")
                fire_sale_enabled = True
                
                # Allow regeneration of fire sale percentage
                if 'fire_sale_pct' not in st.session_state or st.button("🎲 Re-randomize Fire Sale %"):
                    st.session_state.fire_sale_pct = random.uniform(
                        OwnerInvestmentCalculator.FIRE_SALE_MIN,
                        OwnerInvestmentCalculator.FIRE_SALE_MAX
                    )
                    st.rerun()  # Force UI update when fire sale % changes
                
                fire_sale_pct = st.session_state.fire_sale_pct
                st.error(f"Owner Reduction: {fire_sale_pct:.1%} (Random: 51-77%)")
            else:
                fire_sale_enabled = False
                fire_sale_pct = 0.0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Team Strategy**")
            scenario_mode = st.selectbox(
                "Team Mode",
                ["Win Now!", "Build a Dynasty!", "Neutral", "Rebuilding"],
                index=["Win Now!", "Build a Dynasty!", "Neutral", "Rebuilding"].index(selected_team['mode']) if selected_team['mode'] in ["Win Now!", "Build a Dynasty!", "Neutral", "Rebuilding"] else 2,
                help="Team's strategic approach"
            )
        
        with col2:
            st.markdown("**Fan Engagement**")
            scenario_interest = st.slider(
                "Fan Interest",
                min_value=0,
                max_value=100,
                value=int(selected_team['fan_interest']),
                help="Fan interest rating (0-100)"
            )
        
        st.markdown("**Additional Adjustments**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            scenario_budget_space = st.number_input(
                "OOTP Budget Space ($M)",
                min_value=-1000.0,
                max_value=10000.0,
                value=float(selected_team['budget_space']/1e6),
                step=0.1,
                help="Can be negative if over budget"
            ) * 1e6
        
        with col2:
            scenario_trade_cash = st.number_input(
                "Cash from Trades ($M)",
                min_value=-1000.0,
                max_value=10000.0,
                value=float(selected_team['cash_from_trades']/1e6),
                step=0.1,
                help="Cash received in trades"
            ) * 1e6
        
        with col3:
            scenario_custom_bonus = st.number_input(
                "Custom Bonus ($M)",
                min_value=-1000.0,
                max_value=10000.0,
                value=0.0,
                step=0.1,
                help="Additional custom adjustment"
            ) * 1e6
        
        st.markdown("---")
        
        # New section for Playoff Bonuses & Obligations
        st.markdown("**📊 Playoff Bonuses & Other Adjustments**")
        col1, col2 = st.columns(2)
        
        with col1:
            scenario_playoff_bonus = st.number_input(
                "Playoff Bonus Revenue ($M)",
                min_value=0.0,
                max_value=10000.0,
                value=0.0,
                step=0.1,
                help="Extra money from postseason ticket sales, merchandise, etc."
            ) * 1e6
        
        with col2:
            scenario_obligations = st.number_input(
                "Other Obligations ($M)",
                min_value=0.0,
                max_value=10000.0,
                value=0.0,
                step=0.1,
                help="Subtract money for commitments not in OOTP (facility debt, deferred payments, etc.)"
            ) * 1e6
        
        if scenario_playoff_bonus > 0 or scenario_obligations > 0:
            net_adjustment = scenario_playoff_bonus - scenario_obligations
            st.info(f"Net Adjustment: ${net_adjustment/1e6:+.1f}M")
        
        st.markdown("---")
        
        # Calculate scenario investment
        from market_engine import OwnerInvestmentCalculator
        
        scenario_calc = OwnerInvestmentCalculator.calculate_owner_investment(
            budget=selected_team['budget'],
            win_pct=scenario_win_pct,
            mode=scenario_mode,
            fan_interest=scenario_interest,
            postseason_bonus=postseason_bonus if not fire_sale_enabled else 0.0,
            fire_sale=fire_sale_enabled
        )
        
        # Extract factors for convenience
        perf_factor = scenario_calc['performance_factor']
        mode_factor = scenario_calc['mode_factor']
        interest_factor = scenario_calc['interest_factor']
        
        # ========== FINAL BUDGET SUMMARY (MOVED TO TOP) ==========
        st.subheader("💵 Final Budget Summary")
        
        # Calculate total
        base_available = selected_team['budget'] - selected_team['payroll']
        total_budget = (base_available + scenario_budget_space + scenario_trade_cash + 
                       scenario_calc['final_investment'] + scenario_playoff_bonus - 
                       scenario_obligations + scenario_custom_bonus)
        
        # Large display
        col1, col2, col3 = st.columns(3)
        col1.metric("Owner Investment", f"${scenario_calc['final_investment']/1e6:.1f}M")
        col2.metric("Total FA Budget", f"${total_budget/1e6:.1f}M", delta=f"{(total_budget - selected_team['total_fa_budget'])/1e6:.1f}M vs current")
        col3.metric("Aggressiveness", f"{OwnerInvestmentCalculator.calculate_aggressiveness_score(perf_factor, mode_factor, interest_factor):.1f}/100")
        
        # Breakdown table
        breakdown_data = {
            'Source': ['Base Available', 'OOTP Budget Space', 'Cash from Trades', 
                      'Owner Investment', 'Playoff Bonus', 'Obligations', 
                      'Custom Bonus', '**TOTAL**'],
            'Amount': [
                f"${base_available/1e6:.1f}M",
                f"${scenario_budget_space/1e6:.1f}M",
                f"${scenario_trade_cash/1e6:.1f}M",
                f"${scenario_calc['final_investment']/1e6:.1f}M",
                f"${scenario_playoff_bonus/1e6:.1f}M",
                f"-${scenario_obligations/1e6:.1f}M",
                f"${scenario_custom_bonus/1e6:.1f}M",
                f"**${total_budget/1e6:.1f}M**"
            ]
        }
        
        st.table(pd.DataFrame(breakdown_data))
        
        # ========== QUICK SUMMARY BAR ==========
        st.markdown("---")
        st.markdown("**Quick Summary**")
        st.info(f"Performance: {perf_factor:.0%} • Mode: {mode_factor:.0%} • Interest: {interest_factor:.0%} → Owner Investment: ${scenario_calc['final_investment']/1e6:.1f}M")
        
        # ========== DETAILED CALCULATION BREAKDOWN (COLLAPSIBLE) ==========
        st.markdown("---")
        
        with st.expander("📊 View Detailed Calculation Breakdown", expanded=False):
            st.markdown("### Step-by-Step Calculation")
            
            # Step 1: Performance Factor
            st.markdown("#### 📊 Step 1: Performance Factor")
            
            # Visual tier chart
            tiers = [
                (">100 wins (>0.617)", 0.617, 1.0, 0.50),
                ("94-100 wins (0.580-0.617)", 0.580, 0.617, 0.40),
                ("88-94 wins (0.543-0.580)", 0.543, 0.580, 0.30),
                ("82-88 wins (0.506-0.543)", 0.506, 0.543, 0.20),
                ("76-82 wins (0.469-0.506)", 0.469, 0.506, 0.15),
                ("70-76 wins (0.432-0.469)", 0.432, 0.469, 0.10),
                ("<70 wins (<0.432)", 0.0, 0.432, 0.05)
            ]
            
            tier_df = pd.DataFrame(tiers, columns=['Tier', 'Min', 'Max', 'Factor'])
            tier_df['Current'] = tier_df.apply(
                lambda x: '⭐' if x['Min'] <= scenario_win_pct < x['Max'] or (scenario_win_pct >= 0.617 and x['Max'] == 1.0) else '',
                axis=1
            )
            tier_df['Factor_Display'] = tier_df['Factor'].apply(lambda x: f"{x:.0%}")
            
            st.dataframe(
                tier_df[['Current', 'Tier', 'Factor_Display']].rename(columns={'Factor_Display': 'Factor'}),
                use_container_width=True,
                hide_index=True
            )
            
            st.success(f"**Performance Factor: {perf_factor:.0%}** (Win % = {scenario_win_pct:.3f})")
            
            st.markdown("---")
            
            # Step 2: Mode Factor
            st.markdown("#### 🎯 Step 2: Mode Factor")
            
            mode_table = pd.DataFrame([
                {'Mode': 'Win Now!', 'Factor': '100%', 'Description': 'Full investment'},
                {'Mode': 'Build a Dynasty!', 'Factor': '75%', 'Description': 'Aggressive but strategic'},
                {'Mode': 'Neutral', 'Factor': '50%', 'Description': 'Moderate'},
                {'Mode': 'Rebuilding', 'Factor': '10%', 'Description': 'Minimal - development focus'}
            ])
            
            mode_table['Current'] = mode_table['Mode'].apply(lambda x: '⭐' if x == scenario_mode else '')
            
            st.dataframe(mode_table[['Current', 'Mode', 'Factor', 'Description']], use_container_width=True, hide_index=True)
            st.success(f"**Mode Factor: {mode_factor:.0%}** ({scenario_mode})")
            
            st.markdown("---")
            
            # Step 3: Interest Factor
            st.markdown("#### ❤️ Step 3: Interest Factor")
            
            interest_table = pd.DataFrame([
                {'Range': '90-100', 'Factor': '120%', 'Mindset': 'Capitalize on passionate fanbase'},
                {'Range': '75-89', 'Factor': '110%', 'Mindset': 'Strong support'},
                {'Range': '60-74', 'Factor': '100%', 'Mindset': 'Solid baseline'},
                {'Range': '45-59', 'Factor': '90%', 'Mindset': 'Fans cooling off'},
                {'Range': '30-44', 'Factor': '85%', 'Mindset': 'Low interest'},
                {'Range': '<30', 'Factor': '80%', 'Mindset': 'Apathetic fanbase'}
            ])
            
            # Mark current range
            def is_in_range(row, interest):
                if '-' in row['Range']:
                    low, high = map(int, row['Range'].split('-'))
                    return low <= interest <= high
                elif '<' in row['Range']:
                    return interest < 30
                else:
                    return interest >= 90
            
            interest_table['Current'] = interest_table.apply(lambda x: '⭐' if is_in_range(x, scenario_interest) else '', axis=1)
            
            st.dataframe(interest_table[['Current', 'Range', 'Factor', 'Mindset']], use_container_width=True, hide_index=True)
            st.success(f"**Interest Factor: {interest_factor:.0%}** (Fan Interest = {scenario_interest})")
            
            st.markdown("---")
            
            # Step 4: Base Owner Investment
            st.markdown("#### 💰 Step 4: Base Owner Investment")
            st.markdown(f"""
            **Formula:**
            ```
            Base Investment = Budget × Performance Factor × Mode Factor × Interest Factor
            Base Investment = ${selected_team['budget']/1e6:.1f}M × {perf_factor:.0%} × {mode_factor:.0%} × {interest_factor:.0%}
            Base Investment = ${scenario_calc['base_investment']/1e6:.2f}M
            ```
            """)
            st.info(f"**Base Investment: ${scenario_calc['base_investment']/1e6:.2f}M**")
            
            st.markdown("---")
            
            # Step 5: Scenario Bonus/Penalty
            st.markdown("#### 🎖️ Step 5: Scenario Bonus/Penalty")
            if fire_sale_enabled:
                st.error(f"""
                **🔥 FIRE SALE MODE 🔥**
                
                Owner is pocketing funds instead of investing!
                
                - Base Investment: ${scenario_calc['base_investment']/1e6:.2f}M
                - Fire Sale Reduction: {fire_sale_pct:.1%}
                - Owner Pocketed: ${scenario_calc['owner_pocketed']/1e6:.2f}M
                - Final Investment: ${scenario_calc['final_investment']/1e6:.2f}M
                
                ⚠️ **Warning: Owner pocketed ${scenario_calc['owner_pocketed']/1e6:.2f}M ({fire_sale_pct:.1%}) - forcing teardown**
                """)
            elif postseason_bonus > 0:
                st.success(f"""
                **Postseason Success Bonus!**
                
                - Base Investment: ${scenario_calc['base_investment']/1e6:.2f}M
                - Postseason Bonus: +{postseason_bonus:.0%}
                - Final Investment: ${scenario_calc['final_investment']/1e6:.2f}M
                
                Bonus from: {postseason_result}
                """)
            else:
                st.info(f"No postseason bonus applied. Final Investment = Base Investment = ${scenario_calc['final_investment']/1e6:.2f}M")
        
        st.markdown("---")
        
        # Comparison bar chart showing budget under all playoff scenarios
        st.subheader("Budget Comparison Across Playoff Scenarios")
        
        scenario_comparisons = []
        for scenario_name, bonus in postseason_options.items():
            if scenario_name == "🔥 FIRE SALE":
                calc = OwnerInvestmentCalculator.calculate_owner_investment(
                    budget=selected_team['budget'],
                    win_pct=scenario_win_pct,
                    mode=scenario_mode,
                    fan_interest=scenario_interest,
                    postseason_bonus=0.0,
                    fire_sale=True
                )
            else:
                calc = OwnerInvestmentCalculator.calculate_owner_investment(
                    budget=selected_team['budget'],
                    win_pct=scenario_win_pct,
                    mode=scenario_mode,
                    fan_interest=scenario_interest,
                    postseason_bonus=bonus,
                    fire_sale=False
                )
            
            total = (base_available + scenario_budget_space + scenario_trade_cash + 
                    calc['final_investment'] + scenario_playoff_bonus - 
                    scenario_obligations + scenario_custom_bonus)
            
            scenario_comparisons.append({
                'Scenario': scenario_name,
                'Owner Investment': calc['final_investment'],
                'Total Budget': total,
                'Current': '⭐' if scenario_name == postseason_result else ''
            })
        
        comparison_df = pd.DataFrame(scenario_comparisons)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Total FA Budget',
            x=comparison_df['Scenario'],
            y=comparison_df['Total Budget'],
            marker_color=['gold' if x == '⭐' else 'lightblue' for x in comparison_df['Current']],
            text=comparison_df['Total Budget'].apply(lambda x: f"${x/1e6:.1f}M"),
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Total FA Budget by Scenario",
            xaxis_title="Playoff Scenario",
            yaxis_title="Total Budget ($)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Multi-Team Comparison
        st.markdown("---")
        st.subheader("Multi-Team Comparison")
        
        # Initialize session state for comparison teams
        if 'comparison_teams' not in st.session_state:
            st.session_state.comparison_teams = []
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("➕ Add Current Scenario to Comparison"):
                comparison_entry = {
                    'Team': selected_team_name,
                    'Scenario': postseason_result,
                    'Win %': scenario_win_pct,
                    'Mode': scenario_mode,
                    'Interest': scenario_interest,
                    'Owner Investment': scenario_calc['final_investment'],
                    'Total Budget': total_budget
                }
                st.session_state.comparison_teams.append(comparison_entry)
                st.success(f"Added {selected_team_name} to comparison!")
        
        with col2:
            if st.button("🗑️ Clear Comparison"):
                st.session_state.comparison_teams = []
                st.success("Cleared comparison!")
        
        if len(st.session_state.comparison_teams) > 0:
            comp_df = pd.DataFrame(st.session_state.comparison_teams)
            
            # Format for display
            comp_display = comp_df.copy()
            comp_display['Win %'] = comp_display['Win %'].apply(lambda x: f"{x:.3f}")
            comp_display['Owner Investment'] = comp_display['Owner Investment'].apply(lambda x: f"${x/1e6:.1f}M")
            comp_display['Total Budget'] = comp_display['Total Budget'].apply(lambda x: f"${x/1e6:.1f}M")
            
            # Add league rank
            comp_df_sorted = comp_df.sort_values('Total Budget', ascending=False).reset_index(drop=True)
            comp_df_sorted['Rank'] = range(1, len(comp_df_sorted) + 1)
            
            st.dataframe(comp_display, use_container_width=True)
            
            # Export comparison
            csv = comp_df.to_csv(index=False)
            st.download_button(
                "📥 Download Comparison",
                csv,
                "budget_scenario_comparison.csv",
                "text/csv"
            )
        else:
            st.info("No teams in comparison yet. Configure a scenario and click 'Add to Comparison' above.")
        
        # Save/Load Configuration
        st.markdown("---")
        st.subheader("Save/Load Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Current Scenario"):
                import json
                config = {
                    'team': selected_team_name,
                    'wins': scenario_wins,
                    'losses': scenario_losses,
                    'postseason': postseason_result,
                    'mode': scenario_mode,
                    'interest': scenario_interest,
                    'budget_space': scenario_budget_space,
                    'trade_cash': scenario_trade_cash,
                    'custom_bonus': scenario_custom_bonus
                }
                
                config_json = json.dumps(config, indent=2)
                st.download_button(
                    "📥 Download Configuration",
                    config_json,
                    f"{selected_team_name.replace(' ', '_')}_scenario.json",
                    "application/json"
                )
        
        with col2:
            uploaded_config = st.file_uploader("📁 Load Scenario Configuration", type=['json'])
            if uploaded_config is not None:
                import json
                try:
                    loaded_config = json.load(uploaded_config)
                    st.success(f"Loaded scenario for {loaded_config.get('team', 'Unknown')}")
                    st.json(loaded_config)
                except Exception as e:
                    st.error(f"Error loading configuration: {e}")
    
    # ========== TAB 9: FREE AGENT PRICING GUIDE ==========
    with tab9:
        st.header("💡 Free Agent Pricing Guide")
        st.markdown("**Simple, practical tool:** What should this free agent actually sign for based on what similar players got?")
        
        # Calculate FMV for all FAs (cache this calculation)
        # Note: Cache is cleared on app reload or when underlying data changes
        @st.cache_data
        def get_all_fa_fmv():
            return analyzer.calculate_market_fmv_for_all_fas()
        
        fmv_df = get_all_fa_fmv()
        
        # ========== SECTION 1: ALL FREE AGENTS WITH FMV ==========
        st.subheader("📊 All Free Agents with Market Values")
        
        # Filters
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            position_filter = st.multiselect(
                "Position",
                options=['All'] + sorted(fmv_df['position'].unique().tolist()),
                default=['All']
            )
        
        with col2:
            min_overall = st.slider("Min Overall", 0.5, 5.0, 0.5, 0.5, key="fmv_min_overall")
        
        with col3:
            max_overall = st.slider("Max Overall", 0.5, 5.0, 5.0, 0.5, key="fmv_max_overall")
        
        with col4:
            min_age = st.slider("Min Age", 18, 45, 18, key="fmv_min_age")
        
        with col5:
            max_age = st.slider("Max Age", 18, 45, 45, key="fmv_max_age")
        
        # Apply filters
        filtered_fmv = fmv_df.copy()
        if 'All' not in position_filter and len(position_filter) > 0:
            filtered_fmv = filtered_fmv[filtered_fmv['position'].isin(position_filter)]
        filtered_fmv = filtered_fmv[
            (filtered_fmv['overall'] >= min_overall) &
            (filtered_fmv['overall'] <= max_overall) &
            (filtered_fmv['age'] >= min_age) &
            (filtered_fmv['age'] <= max_age)
        ]
        
        # Display table with color coding
        display_df = filtered_fmv.copy()
        
        # Add color coding column
        def get_status_color(row):
            if row['comparable_count'] == 0:
                return "⚪ No comparables"
            diff_pct = row['difference_pct']
            if abs(diff_pct) <= 10:
                return "🟢 Fair ask"
            elif diff_pct > 25:
                return "🔴 >25% high"
            elif diff_pct > 10:
                return "🟡 10-25% high"
            else:
                return "🔵 Discount ask"
        
        display_df['Status'] = display_df.apply(get_status_color, axis=1)
        
        # Format currency columns
        display_df['Demand'] = display_df['demand'].apply(lambda x: f"${x/1e6:.2f}M")
        display_df['Comparable FMV'] = display_df['comparable_median'].apply(
            lambda x: f"${x/1e6:.2f}M" if x > 0 else "N/A"
        )
        display_df['Difference'] = display_df.apply(
            lambda row: f"${row['difference_amount']/1e6:.2f}M ({row['difference_pct']:+.0f}%)" 
            if row['comparable_median'] > 0 else "N/A",
            axis=1
        )
        
        # Select and rename columns for display
        table_cols = {
            'name': 'Player',
            'position': 'Pos',
            'overall': 'OVR',
            'age': 'Age',
            'Demand': 'FA Demand',
            'Comparable FMV': 'Comparable FMV',
            'Difference': 'Difference',
            'comparable_count': '# Comps',
            'Status': 'Status',
            'recommendation': 'Recommendation'
        }
        
        display_table = display_df.rename(columns=table_cols)[list(table_cols.values())]
        
        # Sort options
        sort_by = st.selectbox(
            "Sort by",
            options=['OVR', 'Age', 'FA Demand', '# Comps', 'Player'],
            index=0
        )
        
        if sort_by in display_table.columns:
            if sort_by in ['OVR', 'Age', '# Comps']:
                display_table = display_table.sort_values(sort_by, ascending=False)
            else:
                display_table = display_table.sort_values(sort_by)
        
        st.dataframe(
            display_table,
            use_container_width=True,
            height=400
        )
        
        st.caption(f"Showing {len(display_table)} players | 🟢 Fair (±10%) | 🟡 High (10-25%) | 🔴 Very High (>25%) | 🔵 Below Market | ⚪ No Data")
        
        # ========== SECTION 2: INDIVIDUAL PLAYER DEEP DIVE ==========
        st.markdown("---")
        st.subheader("🔍 Individual Player Analysis")
        
        # Player selection
        selected_fa = st.selectbox(
            "Select a Free Agent",
            options=sorted(fmv_df['name'].unique()),
            index=0
        )
        
        if selected_fa:
            # Get detailed analysis
            analysis = analyzer.get_fa_detailed_analysis(selected_fa, max_comparables=20)
            
            if 'error' not in analysis:
                fa_details = analysis['fa_details']
                stats = analysis['stats']
                recommendation = analysis['recommendation']
                comparables = analysis['comparables']
                
                # Player details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Position", fa_details['position'])
                    st.metric("Overall", f"{fa_details['overall']:.1f}★")
                
                with col2:
                    st.metric("Age", fa_details['age'])
                    st.metric("FA Demand", f"${fa_details['demand']/1e6:.2f}M")
                
                with col3:
                    if stats['count'] > 0:
                        st.metric("Comparables Found", stats['count'])
                        st.metric("FMV (Median)", f"${stats['median']/1e6:.2f}M")
                
                # Comparables table
                if len(comparables) > 0:
                    st.markdown("**Comparable Players:**")
                    
                    comp_display = comparables.copy()
                    comp_display['Salary'] = comp_display['salary'].apply(lambda x: f"${x/1e6:.2f}M")
                    comp_display['Overall'] = comp_display['overall'].apply(lambda x: f"{x:.1f}★")
                    comp_display['Similarity'] = comp_display['similarity_score'].apply(lambda x: f"{x:.0f}")
                    
                    comp_cols = ['name', 'Overall', 'age', 'Salary', 'Similarity']
                    if 'team' in comp_display.columns:
                        comp_cols.insert(4, 'team')
                    if 'total_years' in comp_display.columns:
                        comp_display['Years'] = comp_display['total_years']
                        comp_cols.insert(5, 'Years')
                    
                    comp_table = comp_display[comp_cols].rename(columns={
                        'name': 'Player',
                        'age': 'Age',
                        'team': 'Team'
                    })
                    
                    st.dataframe(comp_table, use_container_width=True, height=300)
                    
                    # Charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Salary distribution histogram
                        fig = go.Figure()
                        
                        fig.add_trace(go.Histogram(
                            x=comparables['salary'],
                            nbinsx=10,
                            name='Comparables',
                            marker_color='lightblue'
                        ))
                        
                        # Add FA demand line
                        fig.add_vline(
                            x=fa_details['demand'],
                            line_dash="dash",
                            line_color="red",
                            annotation_text=f"FA Demand: ${fa_details['demand']/1e6:.1f}M",
                            annotation_position="top"
                        )
                        
                        # Add median line
                        fig.add_vline(
                            x=stats['median'],
                            line_dash="dash",
                            line_color="green",
                            annotation_text=f"Median: ${stats['median']/1e6:.1f}M",
                            annotation_position="bottom"
                        )
                        
                        fig.update_layout(
                            title="Salary Distribution of Comparables",
                            xaxis_title="Salary",
                            yaxis_title="Count",
                            showlegend=False,
                            height=350
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Percentile indicator
                        st.markdown("**Market Position:**")
                        
                        percentile = recommendation['demand_percentile']
                        st.progress(percentile / 100)
                        st.caption(f"FA demand is at the {percentile:.0f}th percentile")
                        
                        if percentile > 75:
                            st.warning(f"⚠️ Asking price is in top 25% of comparables")
                        elif percentile < 25:
                            st.info(f"💡 Asking price is in bottom 25% of comparables")
                        else:
                            st.success(f"✅ Asking price is in middle 50% of comparables")
                        
                        # Recommended signing range
                        st.markdown("**Recommended Signing Range:**")
                        st.markdown(f"**25th-75th Percentile:** ${stats['p25']/1e6:.2f}M - ${stats['p75']/1e6:.2f}M")
                        st.markdown(f"**Fair Market Value:** ${stats['median']/1e6:.2f}M")
                        
                        if recommendation['difference_pct'] > 25:
                            st.error(f"❌ FA asking {recommendation['difference_pct']:.0f}% above market")
                        elif recommendation['difference_pct'] > 10:
                            st.warning(f"⚠️ FA asking {recommendation['difference_pct']:.0f}% above market")
                        elif abs(recommendation['difference_pct']) <= 10:
                            st.success(f"✅ FA asking within 10% of market")
                        else:
                            st.info(f"💰 FA asking {abs(recommendation['difference_pct']):.0f}% below market - good value!")
                    
                    # Summary box
                    st.info(f"""
                    **Summary for {selected_fa}:**
                    - Comparables Found: {stats['count']} signed players
                    - Overall Range: {stats['overall_range']}
                    - Age Range: {stats['age_range']}
                    - Salary Range: ${stats['min']/1e6:.2f}M - ${stats['max']/1e6:.2f}M
                    - Median Salary: ${stats['median']/1e6:.2f}M
                    - 25th-75th Percentile: ${stats['p25']/1e6:.2f}M - ${stats['p75']/1e6:.2f}M
                    
                    **Recommendation:** Sign between ${stats['p25']/1e6:.1f}M and ${stats['p75']/1e6:.1f}M
                    """)
                else:
                    st.warning(f"⚠️ No comparable players found for {selected_fa}. Try a broader search or use manual evaluation.")
        
        # ========== SECTION 3: EXPORT FOR GOD MODE ==========
        st.markdown("---")
        st.subheader("📥 Export for God Mode")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Export Options:**")
            export_min_overall = st.slider(
                "Minimum Overall for Export",
                0.5, 5.0, 3.0, 0.5,
                help="Only export players above this overall rating",
                key="export_min_overall"
            )
            
            export_positions = st.multiselect(
                "Positions to Include",
                options=sorted(fmv_df['position'].unique()),
                default=sorted(fmv_df['position'].unique()),
                help="Select which positions to include in export"
            )
        
        with col2:
            st.markdown("**Generate Export:**")
            
            if st.button("📥 Generate CSV Export", type="primary"):
                # Prepare export data
                export_df = fmv_df[
                    (fmv_df['overall'] >= export_min_overall) &
                    (fmv_df['position'].isin(export_positions))
                ].copy()
                
                # Calculate discount % (positive = FA asking too much, negative = discount)
                export_df['discount_pct'] = export_df.apply(
                    lambda row: ((row['demand'] - row['comparable_median']) / row['comparable_median'] * 100)
                    if row['comparable_median'] > 0 else 0,
                    axis=1
                )
                
                # Select columns for export
                export_cols = [
                    'name', 'position', 'overall', 'age', 
                    'demand', 'comparable_median', 'comparable_p25', 'comparable_p75',
                    'discount_pct', 'comparable_count', 'recommendation'
                ]
                
                export_final = export_df[export_cols].copy()
                
                # Rename for clarity
                export_final = export_final.rename(columns={
                    'name': 'Player Name',
                    'position': 'Position',
                    'overall': 'Overall',
                    'age': 'Age',
                    'demand': 'FA Demand',
                    'comparable_median': 'Recommended FMV',
                    'comparable_p25': 'FMV Low Range',
                    'comparable_p75': 'FMV High Range',
                    'discount_pct': 'Discount %',
                    'comparable_count': 'Comparable Count',
                    'recommendation': 'Recommendation'
                })
                
                # Sort by overall descending
                export_final = export_final.sort_values('Overall', ascending=False)
                
                csv = export_final.to_csv(index=False)
                st.download_button(
                    "📥 Download God Mode Pricing CSV",
                    csv,
                    f"fa_pricing_guide_{datetime.date.today().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    help=f"Export {len(export_final)} players with FMV recommendations"
                )
                
                st.success(f"✅ Generated export for {len(export_final)} players!")
                
                # Show preview
                st.markdown("**Preview of Export:**")
                st.dataframe(export_final.head(10), use_container_width=True)
    
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
