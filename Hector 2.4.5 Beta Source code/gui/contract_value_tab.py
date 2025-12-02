import tkinter as tk
from tkinter import ttk
from .style import on_treeview_motion, on_leave, sort_treeview
from .widgets import (
    make_treeview_open_link_handler,
    load_player_url_template,
)
from .tooltips import add_button_tooltip
from trade_value import (
    calculate_dollars_per_war,
    calculate_surplus_value,
    get_contract_category,
    calculate_trade_value,
    parse_number,
)

player_url_template = load_player_url_template()


def add_contract_value_tab(notebook, font):
    """
    Contract Value Tab - Evaluate whether players provide good value relative to salary
    
    Features:
    - $/WAR calculation
    - Surplus Value calculation
    - Contract category classification (Surplus, Fair Value, Albatross, Arb Target)
    - Sortable and filterable table
    """
    contract_frame = ttk.Frame(notebook)
    notebook.add(contract_frame, text="Contract Value")
    
    # Data storage
    all_pitchers = []
    all_batters = []
    
    # Main container
    main_container = tk.Frame(contract_frame, bg="#1e1e1e")
    main_container.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Header
    header_frame = tk.Frame(main_container, bg="#1e1e1e")
    header_frame.pack(fill="x", padx=5, pady=5)
    
    tk.Label(
        header_frame,
        text="💵 Contract Value Analysis",
        font=(font[0], font[1] + 2, "bold"),
        bg="#1e1e1e",
        fg="#00ff7f"
    ).pack(side="left")
    
    tk.Label(
        header_frame,
        text="Evaluate contract efficiency and identify value opportunities",
        font=(font[0], font[1] - 1),
        bg="#1e1e1e",
        fg="#888888"
    ).pack(side="left", padx=(10, 0))
    
    # Filter controls
    filter_frame = tk.Frame(main_container, bg="#1e1e1e")
    filter_frame.pack(fill="x", padx=5, pady=5)
    
    # Player type filter
    tk.Label(filter_frame, text="Type:", bg="#1e1e1e", fg="#d4d4d4", font=font).pack(side="left")
    type_var = tk.StringVar(value="All")
    type_combo = ttk.Combobox(
        filter_frame,
        textvariable=type_var,
        values=["All", "Batters", "Pitchers"],
        state="readonly",
        width=10
    )
    type_combo.pack(side="left", padx=5)
    
    # Position filter
    tk.Label(filter_frame, text="Position:", bg="#1e1e1e", fg="#d4d4d4", font=font).pack(side="left", padx=(10, 0))
    pos_var = tk.StringVar(value="All")
    pos_combo = ttk.Combobox(
        filter_frame,
        textvariable=pos_var,
        values=["All", "SP", "RP", "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"],
        state="readonly",
        width=8
    )
    pos_combo.pack(side="left", padx=5)
    
    # Category filter
    tk.Label(filter_frame, text="Category:", bg="#1e1e1e", fg="#d4d4d4", font=font).pack(side="left", padx=(10, 0))
    category_var = tk.StringVar(value="All")
    category_combo = ttk.Combobox(
        filter_frame,
        textvariable=category_var,
        values=["All", "💰 Surplus", "⚠️ Fair Value", "🚨 Albatross", "🎯 Arb Target"],
        state="readonly",
        width=14
    )
    category_combo.pack(side="left", padx=5)
    
    # Min WAR filter
    tk.Label(filter_frame, text="Min WAR:", bg="#1e1e1e", fg="#d4d4d4", font=font).pack(side="left", padx=(10, 0))
    min_war_var = tk.StringVar(value="0")
    min_war_entry = tk.Entry(filter_frame, textvariable=min_war_var, width=5, bg="#000000", fg="#d4d4d4", font=font)
    min_war_entry.pack(side="left", padx=5)
    
    # Update button
    update_btn = ttk.Button(filter_frame, text="Update", command=lambda: update_table())
    update_btn.pack(side="left", padx=10)
    
    # Table frame
    table_frame = tk.Frame(main_container, bg="#1e1e1e")
    table_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    vsb.pack(side="right", fill="y")
    
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    hsb.pack(side="bottom", fill="x")
    
    cols = ("Name", "POS", "Age", "Team", "WAR", "Salary", "YL", "$/WAR", "Surplus", "Category", "Trade Value")
    table = ttk.Treeview(
        table_frame,
        columns=cols,
        show="headings",
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set,
        height=20
    )
    table.pack(side="left", fill="both", expand=True)
    vsb.config(command=table.yview)
    hsb.config(command=table.xview)
    
    col_widths = {
        "Name": 140, "POS": 45, "Age": 40, "Team": 55,
        "WAR": 50, "Salary": 70, "YL": 35, "$/WAR": 70,
        "Surplus": 80, "Category": 100, "Trade Value": 85
    }
    for col in cols:
        table.heading(col, text=col, command=lambda c=col: sort_treeview(table, c, False))
        table.column(col, width=col_widths.get(col, 80), minwidth=30, anchor="center", stretch=True)
    
    # Configure tags for category colors
    table.tag_configure("hover", background="#333")
    table.tag_configure("surplus", background="#2d4a2d")  # Green tint
    table.tag_configure("fair_value", background="#4a4a2d")  # Yellow tint
    table.tag_configure("albatross", background="#4a2d2d")  # Red tint
    table.tag_configure("arb_target", background="#2d3a4a")  # Blue tint
    
    table._prev_hover = None
    table.bind("<Motion>", on_treeview_motion)
    table.bind("<Leave>", on_leave)
    
    id_map = {}
    
    def get_tag_for_category(category):
        """Get row tag based on category"""
        if "Surplus" in category:
            return "surplus"
        elif "Albatross" in category:
            return "albatross"
        elif "Arb Target" in category:
            return "arb_target"
        else:
            return "fair_value"
    
    def get_filtered_players():
        """Get players matching current filters"""
        type_filter = type_var.get()
        pos_filter = pos_var.get()
        category_filter = category_var.get()
        
        try:
            min_war = float(min_war_var.get())
        except ValueError:
            min_war = 0
        
        players = []
        
        # Process batters
        if type_filter in ["All", "Batters"]:
            for b in all_batters:
                pos = b.get("POS", "")
                if pos_filter != "All" and pos != pos_filter:
                    continue
                
                war = parse_number(b.get("WAR (Batter)", b.get("WAR", 0)))
                if war < min_war:
                    continue
                
                category_name, category_icon, category_color = get_contract_category(b, "batter")
                full_category = f"{category_icon} {category_name}"
                
                if category_filter != "All" and category_icon not in category_filter:
                    continue
                
                dollars_per_war, dpw_display = calculate_dollars_per_war(b, "batter")
                surplus, surplus_display = calculate_surplus_value(b, "batter")
                trade_value_data = calculate_trade_value(b, "batter")
                
                players.append({
                    "player": b,
                    "type": "batter",
                    "name": b.get("Name", ""),
                    "pos": pos,
                    "age": b.get("Age", ""),
                    "team": b.get("ORG", ""),
                    "war": war,
                    "salary": parse_number(b.get("SLR", 0)),
                    "yl": parse_number(b.get("YL", 0)),
                    "dpw_display": dpw_display,
                    "dpw_value": dollars_per_war,
                    "surplus_display": surplus_display,
                    "surplus_value": surplus,
                    "category": full_category,
                    "category_name": category_name,
                    "trade_value": trade_value_data["trade_value"],
                    "trade_tier": trade_value_data["tier_icon"]
                })
        
        # Process pitchers
        if type_filter in ["All", "Pitchers"]:
            for p in all_pitchers:
                pos = p.get("POS", "")
                if pos == "CL":
                    pos = "RP"  # Treat CL as RP for filtering
                if pos_filter != "All" and pos != pos_filter:
                    continue
                
                war = parse_number(p.get("WAR (Pitcher)", p.get("WAR", 0)))
                if war < min_war:
                    continue
                
                category_name, category_icon, category_color = get_contract_category(p, "pitcher")
                full_category = f"{category_icon} {category_name}"
                
                if category_filter != "All" and category_icon not in category_filter:
                    continue
                
                dollars_per_war, dpw_display = calculate_dollars_per_war(p, "pitcher")
                surplus, surplus_display = calculate_surplus_value(p, "pitcher")
                trade_value_data = calculate_trade_value(p, "pitcher")
                
                players.append({
                    "player": p,
                    "type": "pitcher",
                    "name": p.get("Name", ""),
                    "pos": p.get("POS", ""),
                    "age": p.get("Age", ""),
                    "team": p.get("ORG", ""),
                    "war": war,
                    "salary": parse_number(p.get("SLR", 0)),
                    "yl": parse_number(p.get("YL", 0)),
                    "dpw_display": dpw_display,
                    "dpw_value": dollars_per_war,
                    "surplus_display": surplus_display,
                    "surplus_value": surplus,
                    "category": full_category,
                    "category_name": category_name,
                    "trade_value": trade_value_data["trade_value"],
                    "trade_tier": trade_value_data["tier_icon"]
                })
        
        # Sort by surplus value descending
        players.sort(key=lambda x: x["surplus_value"], reverse=True)
        return players
    
    def update_table():
        """Update the table with current filter settings"""
        table.delete(*table.get_children())
        id_map.clear()
        
        players = get_filtered_players()
        
        for p in players:
            tag = get_tag_for_category(p["category"])
            
            values = (
                p["name"],
                p["pos"],
                p["age"],
                p["team"],
                round(p["war"], 1),
                f"${p['salary']:.1f}M" if p["salary"] > 0 else "-",
                int(p["yl"]) if p["yl"] > 0 else "-",
                p["dpw_display"],
                p["surplus_display"],
                p["category"],
                f"{p['trade_tier']} {p['trade_value']}"
            )
            
            iid = table.insert("", "end", values=values, tags=(tag,))
            player_id = p["player"].get("ID", "")
            if player_id:
                id_map[iid] = player_id
        
        make_treeview_open_link_handler(table, id_map, lambda pid: player_url_template.format(pid=pid))
    
    # Bind filter changes
    type_combo.bind("<<ComboboxSelected>>", lambda e: update_table())
    pos_combo.bind("<<ComboboxSelected>>", lambda e: update_table())
    category_combo.bind("<<ComboboxSelected>>", lambda e: update_table())
    
    # Legend frame
    legend_frame = tk.Frame(main_container, bg="#1e1e1e")
    legend_frame.pack(fill="x", padx=5, pady=5)
    
    tk.Label(
        legend_frame,
        text="Legend:",
        font=(font[0], font[1], "bold"),
        bg="#1e1e1e",
        fg="#d4d4d4"
    ).pack(side="left")
    
    legend_items = [
        ("💰 Surplus", "#51cf66", "WAR ≥ 2.0 + low salary/YL"),
        ("⚠️ Fair Value", "#ffd43b", "Normal $/WAR range"),
        ("🚨 Albatross", "#ff6b6b", "High salary, low WAR, long term"),
        ("🎯 Arb Target", "#4dabf7", "Age 25-27, good stats, team control"),
    ]
    
    for label, color, desc in legend_items:
        tk.Label(
            legend_frame,
            text=f"  {label}",
            font=font,
            bg="#1e1e1e",
            fg=color
        ).pack(side="left", padx=(10, 0))
        tk.Label(
            legend_frame,
            text=f"({desc})",
            font=(font[0], font[1] - 1),
            bg="#1e1e1e",
            fg="#666666"
        ).pack(side="left")
    
    class ContractValueTab:
        def refresh(self, pitchers, batters):
            all_pitchers.clear()
            all_batters.clear()
            all_pitchers.extend(pitchers)
            all_batters.extend(batters)
            update_table()
    
    return ContractValueTab()
