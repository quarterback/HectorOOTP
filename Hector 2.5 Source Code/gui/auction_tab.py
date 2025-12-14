"""
Auction tab GUI for IPL-style free agency auctions.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Import auction modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from auction.engine import AuctionEngine, AuctionState, BidType
from auction.budget import BudgetManager, BudgetConfig
from auction.csv_handler import (
    import_free_agents_csv, 
    import_draft_csv, 
    export_auction_results_csv, 
    validate_csv_format,
    validate_draft_csv_format
)
from auction.valuations import calculate_all_valuations, get_suggested_starting_price, format_price
from auction.bidding_ai import AIBidderPool, BiddingStrategy

from .style import DARK_BG, NEON_GREEN

# Timer update intervals (in milliseconds)
TIMER_UPDATE_INTERVAL_MS = 100  # Update timer display every 100ms
AI_BID_INTERVAL_MS = 2500  # Process AI bids every 2.5 seconds


def add_auction_tab(notebook, font, section_weights, batter_section_weights):
    """Add auction tab to main notebook"""
    
    auction_frame = ttk.Frame(notebook)
    notebook.add(auction_frame, text="Auction")
    
    # Create main container
    main_container = tk.Frame(auction_frame, bg=DARK_BG)
    main_container.pack(fill="both", expand=True, padx=5, pady=5)
    
    # State variables
    class AuctionData:
        players = []
        valuations = {}
        budget_config = None
        budget_manager = None
        ai_bidder_pool = None
        auction_engine = None
        human_teams = set()
        ai_teams = {}
        current_bid_amount = tk.DoubleVar(value=0.0)
        team_id_map = {}  # Team Name → Team ID mapping from draft.csv
        draft_csv_loaded = False
        timer_enabled = tk.BooleanVar(value=True)
        timer_duration = tk.IntVar(value=60)
        timer_update_job = None  # For scheduled timer updates
        ai_bid_job = None  # For scheduled AI bid processing
        
    data = AuctionData()
    
    # ========== Top Section: Setup ==========
    setup_frame = tk.LabelFrame(main_container, text="Auction Setup", bg=DARK_BG, fg=NEON_GREEN, 
                                font=(font[0], font[1]+2, "bold"), padx=10, pady=10)
    setup_frame.pack(fill="x", padx=5, pady=5)
    
    # Row 1: Load CSV and Budget Config
    row1 = tk.Frame(setup_frame, bg=DARK_BG)
    row1.pack(fill="x", pady=5)
    
    load_csv_btn = ttk.Button(row1, text="📁 Load Free Agents CSV", 
                               command=lambda: load_free_agents_csv(data, font))
    load_csv_btn.pack(side="left", padx=5)
    
    csv_status_label = tk.Label(row1, text="No CSV loaded", bg=DARK_BG, fg="#888", font=font)
    csv_status_label.pack(side="left", padx=10)
    
    load_draft_btn = ttk.Button(row1, text="📋 Load Draft CSV", 
                                 command=lambda: load_draft_csv(data, font))
    load_draft_btn.pack(side="left", padx=5)
    
    draft_status_label = tk.Label(row1, text="No draft CSV loaded", bg=DARK_BG, fg="#888", font=font)
    draft_status_label.pack(side="left", padx=10)
    
    # Row 1b: Budget Config (moved to separate row for space)
    row1b = tk.Frame(setup_frame, bg=DARK_BG)
    row1b.pack(fill="x", pady=5)
    
    configure_budget_btn = ttk.Button(row1b, text="💰 Configure Budgets",
                                       command=lambda: open_budget_config_dialog(data, font))
    configure_budget_btn.pack(side="left", padx=5)
    
    budget_status_label = tk.Label(row1b, text="Budgets not configured", bg=DARK_BG, fg="#888", font=font)
    budget_status_label.pack(side="left", padx=10)
    
    # Row 2: Team Assignment
    row2 = tk.Frame(setup_frame, bg=DARK_BG)
    row2.pack(fill="x", pady=5)
    
    assign_teams_btn = ttk.Button(row2, text="👥 Assign Teams (Human/AI)",
                                   command=lambda: open_team_assignment_dialog(data, font))
    assign_teams_btn.pack(side="left", padx=5)
    
    team_status_label = tk.Label(row2, text="Teams not assigned", bg=DARK_BG, fg="#888", font=font)
    team_status_label.pack(side="left", padx=10)
    
    # Row 2b: Timer Configuration
    row2b = tk.Frame(setup_frame, bg=DARK_BG)
    row2b.pack(fill="x", pady=5)
    
    timer_check = tk.Checkbutton(row2b, text="Enable Timer", variable=data.timer_enabled,
                                  bg=DARK_BG, fg="#d4d4d4", selectcolor="#2d2d2d",
                                  activebackground=DARK_BG, font=font)
    timer_check.pack(side="left", padx=5)
    
    tk.Label(row2b, text="Timer Duration:", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left", padx=5)
    timer_scale = tk.Scale(row2b, from_=30, to=120, orient="horizontal", 
                           variable=data.timer_duration, bg=DARK_BG, fg="#d4d4d4",
                           highlightthickness=0, length=150)
    timer_scale.pack(side="left", padx=5)
    tk.Label(row2b, text="seconds", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left")
    
    # Row 3: Start Auction
    row3 = tk.Frame(setup_frame, bg=DARK_BG)
    row3.pack(fill="x", pady=5)
    
    start_auction_btn = ttk.Button(row3, text="🎯 Start Auction",
                                    command=lambda: start_auction(data, auction_display_frame, font, 
                                                                  section_weights, batter_section_weights))
    start_auction_btn.pack(side="left", padx=5)
    
    start_auction_btn.config(state="disabled")
    
    # ========== Middle Section: Auction Display ==========
    auction_display_frame = tk.Frame(main_container, bg=DARK_BG)
    auction_display_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Initially show instructions
    show_auction_instructions(auction_display_frame, font)
    
    # Store UI elements for updates
    data.csv_status_label = csv_status_label
    data.draft_status_label = draft_status_label
    data.budget_status_label = budget_status_label
    data.team_status_label = team_status_label
    data.start_auction_btn = start_auction_btn
    data.auction_display_frame = auction_display_frame
    data.font = font
    data.section_weights = section_weights
    data.batter_section_weights = batter_section_weights


def show_auction_instructions(parent, font):
    """Show initial instructions"""
    for widget in parent.winfo_children():
        widget.destroy()
    
    instructions = tk.Label(parent, text="""
Welcome to the Auction System!

To get started:
1. Load a Free Agents CSV file (draft_eligible_players.csv from OOTP)
2. Load a Draft CSV file (draft.csv from OOTP for team IDs)
3. Configure team budgets
4. Assign teams as Human or AI controlled
5. Start the auction!

The auction will run player-by-player with real-time bidding.
    """, bg=DARK_BG, fg="#d4d4d4", font=font, justify="left")
    instructions.pack(expand=True)


def load_free_agents_csv(data, font):
    """Load free agents from CSV"""
    filepath = filedialog.askopenfilename(
        title="Select Free Agents CSV (draft_eligible_players.csv)",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not filepath:
        return
    
    # Validate CSV
    valid, error, fields = validate_csv_format(filepath)
    if not valid:
        messagebox.showerror("Invalid CSV", f"CSV validation failed:\n{error}")
        return
    
    # Load players
    try:
        data.players = import_free_agents_csv(filepath)
        data.csv_status_label.config(text=f"✓ Loaded {len(data.players)} players", fg=NEON_GREEN)
        
        # If draft CSV not loaded yet, extract teams from player data for now
        if not data.draft_csv_loaded:
            teams = sorted(set(p.get('ORG', p.get('Team', 'FA')) for p in data.players))
            
            # Create default budget config
            data.budget_config = BudgetConfig.default_config(teams, budget_per_team=100.0)
            data.budget_status_label.config(text=f"✓ Default budgets: ${100.0}M per team", fg=NEON_GREEN)
        
        check_ready_to_start(data)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load CSV:\n{str(e)}")


def load_draft_csv(data, font):
    """Load draft CSV to get team IDs"""
    filepath = filedialog.askopenfilename(
        title="Select Draft CSV (draft.csv)",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not filepath:
        return
    
    # Validate CSV
    valid, error, fields = validate_draft_csv_format(filepath)
    if not valid:
        messagebox.showerror("Invalid CSV", f"CSV validation failed:\n{error}")
        return
    
    # Load team ID mapping
    try:
        data.team_id_map = import_draft_csv(filepath)
        data.draft_csv_loaded = True
        data.draft_status_label.config(text=f"✓ Loaded {len(data.team_id_map)} teams", fg=NEON_GREEN)
        
        # Update budget config with teams from draft CSV
        teams = sorted(data.team_id_map.keys())
        data.budget_config = BudgetConfig.default_config(teams, budget_per_team=100.0)
        data.budget_status_label.config(text=f"✓ Default budgets: ${100.0}M per team", fg=NEON_GREEN)
        
        check_ready_to_start(data)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load draft CSV:\n{str(e)}")


def open_budget_config_dialog(data, font):
    """Open dialog to configure budgets"""
    if not data.players:
        messagebox.showwarning("No Data", "Please load Free Agents CSV first")
        return
    
    dialog = tk.Toplevel()
    dialog.title("Configure Team Budgets")
    dialog.geometry("600x550")
    dialog.configure(bg=DARK_BG)
    
    # Instructions
    instr = tk.Label(dialog, text="Set budget for each team (in millions):", 
                     bg=DARK_BG, fg=NEON_GREEN, font=(font[0], font[1]+1, "bold"))
    instr.pack(pady=10)
    
    # League-Wide Budget section (prominent at top)
    league_frame = tk.LabelFrame(dialog, text="League-Wide Budget", bg=DARK_BG, fg=NEON_GREEN,
                                  font=(font[0], font[1]+1, "bold"), padx=10, pady=10)
    league_frame.pack(fill="x", padx=10, pady=5)
    
    tk.Label(league_frame, text="Set budget for all teams:", bg=DARK_BG, fg="#d4d4d4", 
            font=(font[0], font[1]), justify="left").pack(anchor="w", pady=2)
    
    league_budget_frame = tk.Frame(league_frame, bg=DARK_BG)
    league_budget_frame.pack(fill="x", pady=5)
    
    tk.Label(league_budget_frame, text="Budget:", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left")
    league_budget_var = tk.DoubleVar(value=100.0)
    league_entry = ttk.Entry(league_budget_frame, textvariable=league_budget_var, width=10)
    league_entry.pack(side="left", padx=5)
    tk.Label(league_budget_frame, text="M", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left")
    
    # Individual team budgets section
    teams_frame = tk.LabelFrame(dialog, text="Individual Team Budgets (Advanced)", 
                                bg=DARK_BG, fg="#888", font=font, padx=5, pady=5)
    teams_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    # Scroll frame
    scroll_frame = tk.Frame(teams_frame, bg=DARK_BG)
    scroll_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(scroll_frame, bg=DARK_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=DARK_BG)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Create entry for each team
    budget_vars = {}
    teams = sorted(data.budget_config.team_budgets.keys())
    
    for team in teams:
        team_frame = tk.Frame(scrollable_frame, bg=DARK_BG)
        team_frame.pack(fill="x", pady=2)
        
        # Show Team ID if available
        team_id = data.team_id_map.get(team, '')
        team_display = f"{team} ({team_id})" if team_id else team
        
        tk.Label(team_frame, text=f"{team_display}:", bg=DARK_BG, fg="#d4d4d4", 
                font=font, width=25, anchor="w").pack(side="left")
        
        var = tk.DoubleVar(value=data.budget_config.team_budgets[team])
        entry = ttk.Entry(team_frame, textvariable=var, width=10)
        entry.pack(side="left", padx=5)
        tk.Label(team_frame, text="M", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left")
        
        budget_vars[team] = var
    
    def apply_league_budget():
        """Apply league-wide budget to all teams"""
        league_val = league_budget_var.get()
        for var in budget_vars.values():
            var.set(league_val)
    
    league_apply_btn = ttk.Button(league_budget_frame, text="Apply League-Wide Budget to All Teams", 
                                  command=apply_league_budget)
    league_apply_btn.pack(side="left", padx=5)
    
    # Save button
    def save_budgets():
        new_budgets = {team: var.get() for team, var in budget_vars.items()}
        data.budget_config.team_budgets = new_budgets
        data.budget_status_label.config(
            text=f"✓ Budgets configured ({len(new_budgets)} teams)", 
            fg=NEON_GREEN
        )
        check_ready_to_start(data)
        dialog.destroy()
    
    save_btn = ttk.Button(dialog, text="Save Budgets", command=save_budgets)
    save_btn.pack(pady=10)


def open_team_assignment_dialog(data, font):
    """Open dialog to assign teams as Human/AI"""
    if not data.budget_config:
        messagebox.showwarning("No Budgets", "Please configure budgets first")
        return
    
    dialog = tk.Toplevel()
    dialog.title("Assign Teams (Human/AI)")
    dialog.geometry("800x500")
    dialog.configure(bg=DARK_BG)
    
    # Instructions
    instr = tk.Label(dialog, text="Assign each team as Human-controlled or AI-controlled:", 
                     bg=DARK_BG, fg=NEON_GREEN, font=(font[0], font[1]+1, "bold"))
    instr.pack(pady=10)
    
    # Scroll frame
    scroll_frame = tk.Frame(dialog, bg=DARK_BG)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    canvas = tk.Canvas(scroll_frame, bg=DARK_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=DARK_BG)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Team assignments
    team_vars = {}
    strategy_vars = {}
    strategy_labels = {}  # To update strategy display
    teams = sorted(data.budget_config.team_budgets.keys())
    
    for team in teams:
        team_frame = tk.Frame(scrollable_frame, bg=DARK_BG)
        team_frame.pack(fill="x", pady=3)
        
        tk.Label(team_frame, text=f"{team}:", bg=DARK_BG, fg="#d4d4d4", 
                font=font, width=15, anchor="w").pack(side="left")
        
        var = tk.StringVar(value="AI")
        human_rb = tk.Radiobutton(team_frame, text="Human", variable=var, value="Human",
                                   bg=DARK_BG, fg="#d4d4d4", selectcolor="#2d2d2d",
                                   activebackground=DARK_BG, font=font)
        human_rb.pack(side="left", padx=5)
        
        ai_rb = tk.Radiobutton(team_frame, text="AI", variable=var, value="AI",
                               bg=DARK_BG, fg="#d4d4d4", selectcolor="#2d2d2d",
                               activebackground=DARK_BG, font=font)
        ai_rb.pack(side="left", padx=5)
        
        team_vars[team] = var
        
        # AI Strategy dropdown
        tk.Label(team_frame, text="Strategy:", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left", padx=(10, 5))
        strategy_var = tk.StringVar(value="balanced")
        strategy_combo = ttk.Combobox(team_frame, textvariable=strategy_var, 
                                      values=["aggressive", "balanced", "conservative"],
                                      state="readonly", width=12)
        strategy_combo.pack(side="left", padx=5)
        strategy_vars[team] = strategy_var
        
        # Strategy display label - always visible
        strategy_label = tk.Label(team_frame, text="[Balanced]", bg=DARK_BG, 
                                  fg="#FFD700", font=(font[0], font[1], "bold"), width=15, anchor="w")
        strategy_label.pack(side="left", padx=5)
        strategy_labels[team] = strategy_label
        
        # Update strategy label when changed
        def update_strategy_label(team=team):
            strategy = strategy_vars[team].get()
            strategy_labels[team].config(text=f"[{strategy.capitalize()}]")
        
        strategy_combo.bind("<<ComboboxSelected>>", lambda e, t=team: update_strategy_label(t))
        
        # Update strategy label when team type changes
        def update_visibility(team=team):
            team_type = team_vars[team].get()
            if team_type == "Human":
                strategy_labels[team].config(text="[N/A - Human]", fg="#888")
            else:
                update_strategy_label(team)
                strategy_labels[team].config(fg="#FFD700")
        
        var.trace('w', lambda *args, t=team: update_visibility(t))
        update_visibility(team)  # Initial update
    
    # Save button
    def save_assignments():
        data.human_teams = set()
        data.ai_teams = {}
        
        for team in teams:
            if team_vars[team].get() == "Human":
                data.human_teams.add(team)
            else:
                strategy = strategy_vars[team].get()
                data.ai_teams[team] = BiddingStrategy(strategy)
        
        num_human = len(data.human_teams)
        num_ai = len(data.ai_teams)
        data.team_status_label.config(
            text=f"✓ Teams assigned: {num_human} Human, {num_ai} AI", 
            fg=NEON_GREEN
        )
        check_ready_to_start(data)
        dialog.destroy()
    
    save_btn = ttk.Button(dialog, text="Save Assignments", command=save_assignments)
    save_btn.pack(pady=10)


def check_ready_to_start(data):
    """Check if all prerequisites are met to start auction"""
    if (data.players and data.budget_config and 
        (data.human_teams or data.ai_teams)):
        data.start_auction_btn.config(state="normal")


def start_auction(data, display_frame, font, section_weights, batter_section_weights):
    """Initialize and start the auction"""
    # Sort players by OVR (highest first)
    def get_ovr(player):
        ovr_str = str(player.get('OVR', '0')).strip()
        ovr_str = ovr_str.replace(' Stars', '').replace('Stars', '').strip()
        try:
            return float(ovr_str)
        except:
            return 0.0
    
    data.players.sort(key=get_ovr, reverse=True)
    
    # Calculate valuations for all players
    data.valuations = calculate_all_valuations(
        data.players, section_weights, batter_section_weights,
        base_budget=100.0  # Using 100M as base budget
    )
    
    # Calculate starting prices
    starting_prices = {}
    for player in data.players:
        name = player.get('Name', '')
        if name in data.valuations:
            starting_prices[name] = get_suggested_starting_price(data.valuations[name])
        else:
            starting_prices[name] = 1.0
    
    # Initialize budget manager
    data.budget_manager = BudgetManager(data.budget_config)
    
    # Initialize AI bidder pool
    data.ai_bidder_pool = AIBidderPool()
    for team, strategy in data.ai_teams.items():
        data.ai_bidder_pool.add_bidder(team, strategy, data.budget_manager, data.valuations)
    
    # Initialize auction engine with team_id_map
    data.auction_engine = AuctionEngine(data.budget_manager, data.ai_bidder_pool, data.team_id_map)
    data.auction_engine.initialize_auction(data.players, starting_prices)
    
    # Enable timer if configured
    if data.timer_enabled.get():
        data.auction_engine.enable_timer(data.timer_duration.get())
    
    # Set up callbacks
    data.auction_engine.on_bid_callback = lambda bid, player: on_bid_placed(data, bid, player)
    data.auction_engine.on_player_sold_callback = lambda result: on_player_sold(data, result)
    data.auction_engine.on_auction_complete_callback = lambda: on_auction_complete(data)
    data.auction_engine.on_timer_update_callback = lambda: update_timer_display(data)
    
    # Start auction
    data.auction_engine.start_auction()
    
    # Show live auction UI
    show_live_auction_ui(data, display_frame, font)


def show_live_auction_ui(data, parent, font):
    """Show live auction interface"""
    for widget in parent.winfo_children():
        widget.destroy()
    
    # Split into left (current player) and right (dashboard)
    left_frame = tk.Frame(parent, bg=DARK_BG)
    left_frame.pack(side="left", fill="both", expand=True, padx=5)
    
    right_frame = tk.Frame(parent, bg=DARK_BG)
    right_frame.pack(side="right", fill="both", padx=5)
    
    # ===== LEFT: Current Player =====
    
    # Timer display (if enabled)
    if data.auction_engine.timer_enabled:
        timer_frame = tk.Frame(left_frame, bg=DARK_BG)
        timer_frame.pack(fill="x", pady=5)
        
        data.timer_label = tk.Label(timer_frame, text="60", bg=DARK_BG, fg=NEON_GREEN,
                                     font=(font[0], 36, "bold"))
        data.timer_label.pack()
        
        tk.Label(timer_frame, text="seconds remaining", bg=DARK_BG, fg="#888", font=font).pack()
        
        # Pause/Resume button
        data.pause_btn = ttk.Button(timer_frame, text="⏸ Pause Timer",
                                     command=lambda: toggle_pause_timer(data))
        data.pause_btn.pack(pady=5)
    
    player_frame = tk.LabelFrame(left_frame, text="Current Player", bg=DARK_BG, fg=NEON_GREEN,
                                  font=(font[0], font[1]+2, "bold"), padx=10, pady=10)
    player_frame.pack(fill="both", expand=True, pady=5)
    
    data.player_info_label = tk.Label(player_frame, text="", bg=DARK_BG, fg="#d4d4d4", 
                                      font=(font[0], font[1]+2), justify="left")
    data.player_info_label.pack(pady=10)
    
    # Bidding controls
    bid_frame = tk.Frame(player_frame, bg=DARK_BG)
    bid_frame.pack(pady=10)
    
    tk.Label(bid_frame, text="Your Bid ($M):", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left", padx=5)
    
    data.current_bid_amount.set(0.0)
    bid_entry = ttk.Entry(bid_frame, textvariable=data.current_bid_amount, width=10)
    bid_entry.pack(side="left", padx=5)
    
    # Team selector for human teams
    if data.human_teams:
        tk.Label(bid_frame, text="Team:", bg=DARK_BG, fg="#d4d4d4", font=font).pack(side="left", padx=5)
        data.human_team_var = tk.StringVar(value=list(data.human_teams)[0])
        team_combo = ttk.Combobox(bid_frame, textvariable=data.human_team_var,
                                  values=sorted(data.human_teams), state="readonly", width=10)
        team_combo.pack(side="left", padx=5)
        
        place_bid_btn = ttk.Button(bid_frame, text="Place Bid",
                                   command=lambda: place_human_bid(data))
        place_bid_btn.pack(side="left", padx=5)
    
    # Action buttons
    action_frame = tk.Frame(player_frame, bg=DARK_BG)
    action_frame.pack(pady=10)
    
    data.sell_btn = ttk.Button(action_frame, text="✓ Sell Player",
                               command=lambda: sell_player(data))
    data.sell_btn.pack(side="left", padx=5)
    
    data.pass_btn = ttk.Button(action_frame, text="→ Pass / Next",
                               command=lambda: pass_player(data))
    data.pass_btn.pack(side="left", padx=5)
    
    # Bid history
    history_frame = tk.LabelFrame(left_frame, text="Bid History", bg=DARK_BG, fg=NEON_GREEN,
                                   font=font, padx=5, pady=5)
    history_frame.pack(fill="both", expand=True, pady=5)
    
    data.bid_history_text = tk.Text(history_frame, height=15, bg="#1a1a1a", fg="#d4d4d4",
                                    font=font, wrap="word")
    data.bid_history_text.pack(fill="both", expand=True)
    
    # Configure tags for bid history styling
    data.bid_history_text.tag_config("human_bid", foreground="#00bfff")  # Light blue for human
    data.bid_history_text.tag_config("ai_bid", foreground="#ffa500")  # Orange for AI
    data.bid_history_text.tag_config("high_bidder", foreground=NEON_GREEN, font=(font[0], font[1], "bold"))  # Bold green for current winner
    
    # ===== RIGHT: Dashboard =====
    dashboard_frame = tk.LabelFrame(right_frame, text="Team Dashboard", bg=DARK_BG, fg=NEON_GREEN,
                                     font=(font[0], font[1]+2, "bold"), padx=10, pady=10, width=400)
    dashboard_frame.pack(fill="both", expand=True, pady=5)
    dashboard_frame.pack_propagate(False)
    
    # Scrollable dashboard
    canvas = tk.Canvas(dashboard_frame, bg=DARK_BG, highlightthickness=0, width=380)
    scrollbar = ttk.Scrollbar(dashboard_frame, orient="vertical", command=canvas.yview)
    data.dashboard_frame = tk.Frame(canvas, bg=DARK_BG)
    
    data.dashboard_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=data.dashboard_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Enable mouse wheel scrolling (bound to canvas only)
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind("<MouseWheel>", on_mousewheel)
    
    # Progress info
    progress_frame = tk.LabelFrame(right_frame, text="Progress", bg=DARK_BG, fg=NEON_GREEN,
                                    font=font, padx=10, pady=10)
    progress_frame.pack(fill="x", pady=5)
    
    data.progress_label = tk.Label(progress_frame, text="", bg=DARK_BG, fg="#d4d4d4", font=font)
    data.progress_label.pack()
    
    # Export button (initially disabled)
    data.export_btn = ttk.Button(right_frame, text="📤 Export Results CSV",
                                 command=lambda: export_results(data), state="disabled")
    data.export_btn.pack(pady=5)
    
    # Initial update
    update_auction_display(data)
    
    # Start timer updates if enabled
    if data.auction_engine.timer_enabled:
        schedule_timer_update(data)
        schedule_ai_bid_processing(data)


def update_auction_display(data):
    """Update all auction display elements"""
    if not data.auction_engine:
        return
    
    # Update current player info
    player_info = data.auction_engine.get_current_player_info()
    if player_info:
        player = player_info['player']
        name = player.get('Name', 'Unknown')
        pos = player.get('POS', '?')
        age = player.get('Age', '?')
        ovr = player.get('OVR', '?')
        pot = player.get('POT', '?')
        
        valuation = data.valuations.get(name, {})
        suggested = valuation.get('suggested_price', 0)
        
        current_price = player_info['current_price']
        high_bidder = player_info['high_bidder'] or "No bids yet"
        
        # Build stats display based on position
        stats_line = ""
        pos_upper = str(pos).upper().strip()
        if pos_upper in {'SP', 'RP', 'CL', 'P'}:
            # Pitcher stats
            era = player.get('ERA', '-')
            whip = player.get('WHIP', '-')
            k9 = player.get('K/9', '-')
            war = player.get('WAR', '-')
            stats_line = f"Stats: ERA {era} | WHIP {whip} | K/9 {k9} | WAR {war}"
        else:
            # Batter stats
            avg = player.get('AVG', '-')
            obp = player.get('OBP', '-')
            slg = player.get('SLG', '-')
            hr = player.get('HR', '-')
            rbi = player.get('RBI', '-')
            war = player.get('WAR', '-')
            stats_line = f"Stats: AVG {avg} | OBP {obp} | SLG {slg} | HR {hr} | RBI {rbi} | WAR {war}"
        
        info_text = f"""
{name}
Position: {pos}  |  Age: {age}  |  OVR: {ovr}  |  POT: {pot}

{stats_line}

Suggested Value: {format_price(suggested)}
Current Price: {format_price(current_price)}
High Bidder: {high_bidder}
        """
        
        data.player_info_label.config(text=info_text)
        
        # Set default bid amount
        if current_price == 0:
            data.current_bid_amount.set(suggested * 0.35)  # Start at 35% of value
        else:
            data.current_bid_amount.set(current_price + 0.5)
    
    # Update progress
    progress = data.auction_engine.get_progress()
    progress_text = f"Player {progress['current_index'] + 1} of {progress['total_players']}\n"
    progress_text += f"Sold: {progress['players_sold']} | Unsold: {progress['players_unsold']}"
    data.progress_label.config(text=progress_text)
    
    # Update team dashboard
    update_team_dashboard(data)


def update_team_dashboard(data):
    """Update team budget dashboard"""
    if not data.budget_manager or not hasattr(data, 'dashboard_frame'):
        return
    
    # Clear existing
    for widget in data.dashboard_frame.winfo_children():
        widget.destroy()
    
    summaries = data.budget_manager.get_all_summaries()
    
    for summary in summaries:
        team = summary['team']
        remaining = summary['remaining']
        starting = summary['starting_budget']
        roster_size = summary['roster_size']
        
        # Calculate budget health percentage
        budget_percentage = (remaining / starting * 100) if starting > 0 else 0
        
        # Determine color based on budget health
        if budget_percentage > 60:
            budget_color = NEON_GREEN  # Healthy budget
        elif budget_percentage > 30:
            budget_color = "#ffa500"  # Warning (orange)
        else:
            budget_color = "#ff4444"  # Critical (red)
        
        # Team frame - more compact layout
        team_frame = tk.Frame(data.dashboard_frame, bg="#1a1a1a", relief="ridge", bd=1)
        team_frame.pack(fill="x", pady=2, padx=2)
        
        # Top row: Team name and roster
        top_row = tk.Frame(team_frame, bg="#1a1a1a")
        top_row.pack(fill="x", padx=5, pady=2)
        
        is_human = team in data.human_teams
        team_label = tk.Label(top_row, text=f"{team} {'👤' if is_human else '🤖'}", 
                             bg="#1a1a1a", fg=NEON_GREEN, font=(data.font[0], data.font[1], "bold"))
        team_label.pack(side="left")
        
        roster_label = tk.Label(top_row, text=f"({roster_size} players)", 
                               bg="#1a1a1a", fg="#888", font=data.font)
        roster_label.pack(side="right")
        
        # Bottom row: Budget info with color coding
        budget_row = tk.Frame(team_frame, bg="#1a1a1a")
        budget_row.pack(fill="x", padx=5, pady=(0, 3))
        
        budget_text = f"{format_price(remaining)} / {format_price(starting)}"
        budget_label = tk.Label(budget_row, text=budget_text, 
                               bg="#1a1a1a", fg=budget_color, font=data.font)
        budget_label.pack(side="left")
        
        # Budget percentage indicator
        percentage_text = f"({budget_percentage:.0f}%)"
        percentage_label = tk.Label(budget_row, text=percentage_text, 
                                   bg="#1a1a1a", fg=budget_color, font=data.font)
        percentage_label.pack(side="right")


def place_human_bid(data):
    """Place a bid from human team"""
    if not hasattr(data, 'human_team_var'):
        return
    
    team = data.human_team_var.get()
    amount = data.current_bid_amount.get()
    
    success, error = data.auction_engine.place_bid(team, amount, BidType.HUMAN)
    
    if not success:
        messagebox.showerror("Bid Failed", error)
    else:
        # Auto-process AI bids after human bid
        data.auction_engine.process_ai_bids()
        update_auction_display(data)


def process_ai_bids(data):
    """Process AI bids for current player"""
    ai_bids = data.auction_engine.process_ai_bids()
    update_auction_display(data)
    
    if not ai_bids:
        messagebox.showinfo("No Bids", "No AI teams are interested in bidding at current price.")


def sell_player(data):
    """Sell current player to highest bidder"""
    result = data.auction_engine.sell_current_player()
    
    if result:
        msg = f"{result.player.get('Name', '')} sold to {result.winning_team} for {format_price(result.final_price)}"
        data.bid_history_text.insert('1.0', msg + "\n\n")
    
    update_auction_display(data)
    
    # Check if auction complete
    if data.auction_engine.state == AuctionState.COMPLETED:
        on_auction_complete(data)


def pass_player(data):
    """Pass on current player"""
    data.auction_engine.pass_on_player()
    update_auction_display(data)
    
    if data.auction_engine.state == AuctionState.COMPLETED:
        on_auction_complete(data)


def on_bid_placed(data, bid, player):
    """Callback when bid is placed"""
    # Update bid history display with color coding
    bid_type_icon = "👤" if bid.bid_type == BidType.HUMAN else "🤖"
    msg = f"{bid_type_icon} {bid.team} bids {format_price(bid.amount)}"
    
    if hasattr(data, 'bid_history_text'):
        # Determine if this is the current high bidder
        is_high_bidder = (data.auction_engine.current_high_bidder == bid.team)
        
        # Choose tag based on bid type and whether they're the high bidder
        if is_high_bidder:
            tag = "high_bidder"
        elif bid.bid_type == BidType.HUMAN:
            tag = "human_bid"
        else:
            tag = "ai_bid"
        
        # Insert at the top with appropriate tag (message without newline)
        data.bid_history_text.insert('1.0', msg, tag)
        data.bid_history_text.insert('1.0', "\n")


def on_player_sold(data, result):
    """Callback when player is sold"""
    pass  # Handled in sell_player function


def on_auction_complete(data):
    """Callback when auction completes"""
    data.export_btn.config(state="normal")
    messagebox.showinfo("Auction Complete", "The auction has finished!\n\nYou can now export the results.")
    
    # Show results summary
    show_results_summary(data)


def show_results_summary(data):
    """Show auction results summary"""
    if not hasattr(data, 'auction_display_frame'):
        return
    
    parent = data.auction_display_frame
    for widget in parent.winfo_children():
        widget.destroy()
    
    summary_frame = tk.Frame(parent, bg=DARK_BG)
    summary_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    title = tk.Label(summary_frame, text="Auction Complete!", bg=DARK_BG, fg=NEON_GREEN,
                    font=(data.font[0], data.font[1]+4, "bold"))
    title.pack(pady=10)
    
    summary = data.auction_engine.get_results_summary()
    
    summary_text = f"""
Total Players Sold: {summary['total_players_sold']}
Total Players Unsold: {summary['total_players_unsold']}
Total Amount Spent: {format_price(summary['total_amount_spent'])}
Average Price: {format_price(summary['average_price'])}
    """
    
    summary_label = tk.Label(summary_frame, text=summary_text, bg=DARK_BG, fg="#d4d4d4",
                            font=(data.font[0], data.font[1]+1), justify="left")
    summary_label.pack(pady=10)
    
    # Export button
    export_btn = ttk.Button(summary_frame, text="📤 Export Results to CSV",
                           command=lambda: export_results(data))
    export_btn.pack(pady=10)


def export_results(data):
    """Export auction results to CSV"""
    if not data.auction_engine:
        return
    
    summary = data.auction_engine.get_results_summary()
    
    # Prepare results for export with new format
    results = []
    for result in summary['results']:
        results.append({
            'player': result.player,
            'team': result.winning_team,
            'team_name': result.winning_team,  # For OOTP format
            'team_id': result.team_id,
            'player_id': result.player_id,
            'price': result.final_price,
            'order': result.order
        })
    
    # Sort by order to ensure chronological output
    results.sort(key=lambda x: x.get('order', 0))
    
    # Ask for file location
    filepath = filedialog.asksaveasfilename(
        title="Export Auction Results (rename to draft.csv before importing to OOTP)",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="draft_results.csv"
    )
    
    if not filepath:
        return
    
    try:
        export_auction_results_csv(results, filepath, format_type='ootp')
        
        # Show success message with import instructions
        messagebox.showinfo(
            "Export Successful",
            f"Results exported to:\n{filepath}\n\n"
            "📋 Next Steps:\n"
            "1. Rename this file to 'draft.csv'\n"
            "2. Copy it to your OOTP import_export folder\n"
            "3. In OOTP, import the draft.csv file\n"
            "4. Players will be assigned to their winning teams!"
        )
    except Exception as e:
        messagebox.showerror("Export Failed", f"Failed to export results:\n{str(e)}")


# ========== Timer Functions ==========

def schedule_timer_update(data):
    """Schedule periodic timer updates"""
    if not data.auction_engine or not data.auction_engine.timer_enabled:
        return
    
    update_timer_display(data)
    
    # Schedule next update
    if hasattr(data, 'auction_display_frame') and data.auction_display_frame.winfo_exists():
        data.timer_update_job = data.auction_display_frame.after(TIMER_UPDATE_INTERVAL_MS, lambda: schedule_timer_update(data))


def update_timer_display(data):
    """Update the timer display"""
    if not data.auction_engine or not data.auction_engine.timer_enabled:
        return
    
    if not hasattr(data, 'timer_label'):
        return
    
    remaining = data.auction_engine.get_timer_remaining()
    
    # Update display
    data.timer_label.config(text=f"{int(remaining)}")
    
    # Color coding: green > 30s, yellow 15-30s, red < 15s
    if remaining > 30:
        color = NEON_GREEN
    elif remaining > 15:
        color = "#FFD700"  # Yellow
    else:
        color = "#FF4444"  # Red
    
    data.timer_label.config(fg=color)
    
    # Check if timer expired
    if data.auction_engine.is_timer_expired() and data.auction_engine.state == AuctionState.IN_PROGRESS:
        # Auto-sell player
        sell_player(data)


def schedule_ai_bid_processing(data):
    """Schedule periodic AI bid processing (every 2-3 seconds)"""
    if not data.auction_engine or not data.auction_engine.timer_enabled:
        return
    
    if data.auction_engine.state != AuctionState.IN_PROGRESS:
        return
    
    # Process AI bids
    if not data.auction_engine.is_timer_expired():
        data.auction_engine.process_ai_bids()
        update_auction_display(data)
    
    # Schedule next AI bid processing
    if hasattr(data, 'auction_display_frame') and data.auction_display_frame.winfo_exists():
        data.ai_bid_job = data.auction_display_frame.after(AI_BID_INTERVAL_MS, lambda: schedule_ai_bid_processing(data))


def toggle_pause_timer(data):
    """Toggle pause/resume of timer"""
    if not data.auction_engine:
        return
    
    if data.auction_engine.state == AuctionState.IN_PROGRESS:
        data.auction_engine.pause_auction()
        if hasattr(data, 'pause_btn'):
            data.pause_btn.config(text="▶ Resume Timer")
    elif data.auction_engine.state == AuctionState.PAUSED:
        data.auction_engine.resume_auction()
        if hasattr(data, 'pause_btn'):
            data.pause_btn.config(text="⏸ Pause Timer")
