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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Market Overview",
        "💰 Salary Bands",
        "🎯 Player Pricer",
        "📍 Position Analysis",
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
                'Average (3.5★)', 
                'Below Average (3.0★)', 
                'Role Player (<3.0★)'
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
            
            # Market Gap Analysis
            st.subheader("Market Gap: Free Agents vs Signed Players")
            st.markdown("Shows how much more FAs are demanding compared to rostered players")
            
            gap_analysis = analyzer.get_market_gap_analysis()
            
            if len(gap_analysis) > 0:
                # Filter to selected positions and tiers
                gap_filtered = gap_analysis[
                    gap_analysis['position'].isin(selected_positions_bands) &
                    gap_analysis['tier'].isin(selected_tiers)
                ]
                
                if len(gap_filtered) > 0:
                    # Create comparison chart
                    fig = go.Figure()
                    
                    # Group by tier for cleaner visualization
                    for tier in selected_tiers:
                        tier_gap = gap_filtered[gap_filtered['tier'] == tier]
                        
                        if len(tier_gap) > 0:
                            fig.add_trace(go.Bar(
                                name=f'{tier} - Signed',
                                x=tier_gap['position'],
                                y=tier_gap['signed_median'],
                                marker_color='lightblue',
                                showlegend=True if tier == selected_tiers[0] else False,
                                legendgroup='signed',
                                legendgrouptitle_text='Signed'
                            ))
                            
                            fig.add_trace(go.Bar(
                                name=f'{tier} - FA',
                                x=tier_gap['position'],
                                y=tier_gap['fa_median'],
                                marker_color='orange',
                                showlegend=True if tier == selected_tiers[0] else False,
                                legendgroup='fa',
                                legendgrouptitle_text='Free Agent'
                            ))
                    
                    fig.update_layout(
                        barmode='group',
                        title="Median Salary: Signed vs Free Agent by Position",
                        xaxis_title="Position",
                        yaxis_title="Median Salary ($)",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Gap percentage table
                    st.markdown("**FA Premium Table**")
                    gap_display = gap_filtered[['position', 'tier', 'signed_median', 'fa_median', 'gap_amount', 'gap_percentage']].copy()
                    gap_display['signed_median'] = gap_display['signed_median'].apply(lambda x: f"${x/1e6:.2f}M")
                    gap_display['fa_median'] = gap_display['fa_median'].apply(lambda x: f"${x/1e6:.2f}M")
                    gap_display['gap_amount'] = gap_display['gap_amount'].apply(lambda x: f"${x/1e6:.2f}M")
                    gap_display['gap_percentage'] = gap_display['gap_percentage'].apply(lambda x: f"{x:.1f}%")
                    
                    st.dataframe(gap_display, use_container_width=True, height=300)
                    
                    # Download gap analysis
                    csv = gap_filtered.to_csv(index=False)
                    st.download_button(
                        "📥 Download Market Gap Analysis",
                        csv,
                        "market_gap_analysis.csv",
                        "text/csv"
                    )
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
            
            comps_display = comps_df[['name', 'position', 'overall', 'potential', 'age', 'salary', 'source', 'team']].head(20).copy()
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
                ('Star (4.5★)', 4.5, 4.9),
                ('Above Average (4.0★)', 4.0, 4.4),
                ('Average (3.5★)', 3.5, 3.9),
                ('Below Average (3.0★)', 3.0, 3.4),
                ('Role Player (<3.0★)', 0.0, 2.9),
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
        role_tier = tier_stats[tier_stats['tier'].str.contains('Role Player')].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Elite Players (5.0★)", f"{elite_tier['total_players']}")
        col1.metric("Elite Avg Salary", f"${elite_tier['avg_salary']/1e6:.2f}M")
        
        col2.metric("Role Players (<3.0★)", f"{role_tier['total_players']}")
        col2.metric("Role Avg Salary", f"${role_tier['avg_salary']/1e6:.2f}M")
        
        col3.metric("Elite Premium", f"{elite_tier['avg_salary']/role_tier['avg_salary']:.1f}x")
        col3.caption("Elite players earn this multiple of role players")
    
    # ========== TAB 6: TEAM ANALYSIS ==========
    with tab6:
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
