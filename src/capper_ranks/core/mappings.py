# src/capper_ranks/core/mappings.py

# This map links various team name aliases, including acronyms, to their official league.
# All keys are lowercase to make lookups case-insensitive.
TEAM_LEAGUE_MAP = {
    # --- Major League Baseball (MLB) ---
    'arizona diamondbacks': 'MLB', 'diamondbacks': 'MLB', 'd-backs': 'MLB', 'ari': 'MLB',
    'atlanta braves': 'MLB', 'braves': 'MLB', 'atl': 'MLB',
    'baltimore orioles': 'MLB', 'orioles': 'MLB', 'bal': 'MLB',
    'boston red sox': 'MLB', 'red sox': 'MLB', 'bos': 'MLB',
    'chicago white sox': 'MLB', 'white sox': 'MLB', 'cws': 'MLB',
    'chicago cubs': 'MLB', 'cubs': 'MLB', 'chc': 'MLB',
    'cincinnati reds': 'MLB', 'reds': 'MLB', 'cin': 'MLB',
    'cleveland guardians': 'MLB', 'guardians': 'MLB', 'cle': 'MLB',
    'colorado rockies': 'MLB', 'rockies': 'MLB', 'col': 'MLB',
    'detroit tigers': 'MLB', 'tigers': 'MLB', 'det': 'MLB',
    'houston astros': 'MLB', 'astros': 'MLB', 'hou': 'MLB',
    'kansas city royals': 'MLB', 'royals': 'MLB', 'kc': 'MLB',
    'los angeles angels': 'MLB', 'angels': 'MLB', 'laa': 'MLB',
    'los angeles dodgers': 'MLB', 'dodgers': 'MLB', 'lad': 'MLB',
    'miami marlins': 'MLB', 'marlins': 'MLB', 'mia': 'MLB',
    'milwaukee brewers': 'MLB', 'brewers': 'MLB', 'mil': 'MLB',
    'minnesota twins': 'MLB', 'twins': 'MLB', 'min': 'MLB',
    'new york yankees': 'MLB', 'yankees': 'MLB', 'nyy': 'MLB',
    'new york mets': 'MLB', 'mets': 'MLB', 'nym': 'MLB',
    'oakland athletics': 'MLB', 'athletics': 'MLB', 'oak': 'MLB',
    'philadelphia phillies': 'MLB', 'phillies': 'MLB', 'phi': 'MLB',
    'pittsburgh pirates': 'MLB', 'pirates': 'MLB', 'pit': 'MLB',
    'san diego padres': 'MLB', 'padres': 'MLB', 'sd': 'MLB',
    'san francisco giants': 'MLB', 'giants': 'MLB', 'sf': 'MLB',
    'seattle mariners': 'MLB', 'mariners': 'MLB', 'sea': 'MLB',
    'st. louis cardinals': 'MLB', 'cardinals': 'MLB', 'stl': 'MLB',
    'tampa bay rays': 'MLB', 'rays': 'MLB', 'tb': 'MLB',
    'texas rangers': 'MLB', 'rangers': 'MLB', 'tex': 'MLB',
    'toronto blue jays': 'MLB', 'blue jays': 'MLB', 'tor': 'MLB',
    'washington nationals': 'MLB', 'nationals': 'MLB', 'wsh': 'MLB', 'was': 'MLB',

    # --- National Football League (NFL) - For Later ---
    # 'chiefs': 'NFL', 'kc': 'NFL',

    # --- National Basketball Association (NBA) - For Later ---
    # 'lakers': 'NBA', 'lal': 'NBA',
}