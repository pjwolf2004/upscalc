import json
from collections import defaultdict

# ------------------------------------
# CONFIGURATION
# ------------------------------------
YEAR = 2026
# FILE = "place file name from your folder.json" 
# # and then remove the comment  in front of FILE to get it working 

CAP_IDS = {157, 202, 305}              # CAP players
BASE_CAP_UPS = 6                       # CAP base UPS

# CUSTOM BOOSTERS: pid → UPS bonus
BOOSTERS = {
    157: 3,
}

# ------------------------------------
# BRAND DEALS
# ------------------------------------
# Format: pid : "Brand Name"
# EXAMPLES INCLUDED
PLAYER_BRANDS = {
    157: "Nike",        # CAP example
    412: "Gatorade",    # AI example
}

# Brand definitions
Brands = { 
    # Tier 1 
    "Gatorade":       {"tiers": "Tier 1", "ups": 2},
    "Nike":           {"tiers": "Tier 1", "ups": 4},
    "Adidas":         {"tiers": "Tier 1", "ups": 4},
    "ROLEX":          {"tiers": "Tier 1", "ups": 3},
    "Foot Locker":    {"tiers": "Tier 1", "ups": 3},
    "Converse":       {"tiers": "Tier 1", "ups": 1},

    # Tier 2 
    "OnlyFans":       {"tiers": "Tier 2", "ups": 1},
    "Spalding":       {"tiers": "Tier 2", "ups": 2},
    "McDonalds":      {"tiers": "Tier 2", "ups": 1},
    "Under Armour":   {"tiers": "Tier 2", "ups": 1},
    "KFC":            {"tiers": "Tier 2", "ups": 1},
}

# ------------------------------------
# ALL BBGM AWARDS — unified system
# ------------------------------------
#format: "in-game award name": { "bucket": "bucket name",  "ups": number of ups}
AWARDS = {
    "Most Valuable Player":            {"bucket": "MVP",            "ups": 3},
    "Defensive Player of the Year":    {"bucket": "DPOY",           "ups": 3},
    "Rookie of the Year":              {"bucket": "ROTY",           "ups": 2},
    "Sixth Man of the Year":           {"bucket": "SMOY",           "ups": 2},

    # MIP safety (BBGM sometimes changes text)
    "Most Improved Player":            {"bucket": "MIP",            "ups": 2},
    "Most Improved":                   {"bucket": "MIP",            "ups": 2},

    # Playoffs
    "Finals MVP":                      {"bucket": "FMVP",           "ups": 2},
    "Semifinals MVP":                  {"bucket": "SFMVP",          "ups": 0},
    "Conference Finals MVP":           {"bucket": "SFMVP",          "ups": 0},

    # All-League
    "First Team All-League":           {"bucket": "All-League",     "ups": 3},
    "Second Team All-League":          {"bucket": "All-League",     "ups": 2},
    "Third Team All-League":           {"bucket": "All-League",     "ups": 1},

    # All-Defensive
    "First Team All-Defensive":        {"bucket": "All-Defensive",  "ups": 3},
    "Second Team All-Defensive":       {"bucket": "All-Defensive",  "ups": 2},
    "Third Team All-Defensive":        {"bucket": "All-Defensive",  "ups": 1},

    # All-Star
    "All-Star":                        {"bucket": "All-Star",       "ups": 2},
    "All-Star MVP":                    {"bucket": "All-Star MVP",   "ups": 0},
    "All-Star Game MVP":               {"bucket": "All-Star MVP",   "ups": 0},

    # Rookies
    "All-Rookie Team":                 {"bucket": "All-Rookie",     "ups": 1},

    # Championship
    "Won Championship":                {"bucket": "Champion",       "ups": 3},
}

ALL_BUCKETS = sorted(set(v["bucket"] for v in AWARDS.values()))


# STAT LEADER UPS

LEADER_UPS = {
    "Scoring Leader": 0,
    "Rebounding Leader": 0,
    "Assists Leader": 0,
    "Steals Leader": 0,
    "Blocks Leader": 0,
}

def map_award_type(text):
    text = text.lower()
    best = None
    for key in AWARDS.keys():
        if key.lower() in text:
            if best is None or len(key) > len(best):
                best = key
    return best

# LOAD FILE

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

players = {p["pid"]: p for p in data["players"]}
names = {pid: f"{p['firstName']} {p['lastName']}" for pid, p in players.items()}

award_winners = defaultdict(list)
ups_player = defaultdict(int)

# PLAYER AWARDS

for pid, p in players.items():
    for a in p.get("awards", []):
        if a.get("season") != YEAR:
            continue

        award_key = map_award_type(a.get("type", ""))
        if award_key is None:
            continue

        bucket = AWARDS[award_key]["bucket"]
        ups = AWARDS[award_key]["ups"]

        award_winners[bucket].append(names[pid])
        ups_player[pid] += ups

# BOOSTERS

for pid, bonus in BOOSTERS.items():
    ups_player[pid] += bonus

# BASE CAP UPS (+6)

for pid in CAP_IDS:
    ups_player[pid] += BASE_CAP_UPS

# BRAND DEAL UPS

for pid, brand in PLAYER_BRANDS.items():
    if brand not in Brands:
        print(f"WARNING: Brand '{brand}' not found for PID {pid}")
        continue

    ups_player[pid] += Brands[brand]["ups"]

# STAT LEADERS

leader_stats = {
    "Scoring Leader": "pts",
    "Rebounding Leader": "trb",
    "Assists Leader": "ast",
    "Steals Leader": "stl",
    "Blocks Leader": "blk",
}

totals = {k: defaultdict(int) for k in leader_stats}

for pid, p in players.items():
    for s in p.get("stats", []):
        if s.get("season") == YEAR:
            for label, key in leader_stats.items():
                totals[label][pid] += s.get(key, 0)

for label, t in totals.items():
    if t:
        best_pid = max(t, key=t.get)
        award_winners[label].append(names[best_pid])
        ups_player[best_pid] += LEADER_UPS[label]

# CHAMPION FALLBACK

series = data.get("playoffs", {}).get("series", [])

if not award_winners["Champion"] and series and len(series[-1]) > 0:
    finals = series[-1][0]
    champ_tid = finals.get("won")

    if champ_tid is not None:
        champs = []
        for pid, p in players.items():
            for s in p.get("stats", []):
                if s.get("season") == YEAR and s.get("tid") == champ_tid:
                    champs.append(names[pid])
                    ups_player[pid] += AWARDS["Won Championship"]["ups"]
                    break
        award_winners["Champion"] = champs





# PRINT REPORT

print("\n=== AWARD CHECK REPORT ===")
for bucket in ALL_BUCKETS:
    winners = award_winners.get(bucket, [])
    icon = "✔️" if winners else "❌"
    print(f"{icon} {bucket} — Winners: {winners}")

for label in LEADER_UPS.keys():
    winners = award_winners.get(label, [])
    icon = "✔️" if winners else "❌"
    print(f"{icon} {label} — Winners: {winners}")

print(f"{'✔️' if award_winners['Champion'] else '❌'} Champion — Winners: {award_winners['Champion']}")

# UPS SUMMARY

print("\n==============================")
print("=== UPS SUMMARY: CAP PLAYERS ===")
print("==============================")

cap_total = 0
for pid in CAP_IDS:
    ups = ups_player.get(pid, 0)
    cap_total += ups
    brand = PLAYER_BRANDS.get(pid, "No Brand")
    print(f"{names.get(pid, f'PID {pid}')} — {ups} UPS (CAP) — Brand: {brand}")

print(f"TOTAL CAP UPS: {cap_total}")

print("\n==============================")
print("=== UPS SUMMARY: AI PLAYERS ===")
print("==============================")

ai_total = 0
ai = [(pid, ups) for pid, ups in ups_player.items() if pid not in CAP_IDS]
ai = sorted(ai, key=lambda x: x[1], reverse=True)

for pid, ups in ai:
    brand = PLAYER_BRANDS.get(pid, "No Brand")
    ai_total += ups
    print(f"{names[pid]} — {ups} UPS — Brand: {brand}")

print(f"TOTAL AI UPS: {ai_total}")

print("\n==============================")
print(f"TOTAL LEAGUE UPS: {cap_total + ai_total}")
print("==============================\n")


