# Capper-Ranks Bot

A Python-based X (Twitter) bot designed to automatically track sports picks from popular sports handicappers ("cappers"). The bot parses tweets for sports picks, stores them, tracks win/loss results using live sports data, and maintains performance statistics for each capper.

## 🎯 Project Overview

Capper-Ranks aims to become an authoritative source for capper performance data, building a community around sports betting analytics with potential for monetization and affiliate partnerships.

## 🚀 Current Functionality

The bot's foundational data pipeline is complete and tested for single MLB bets. It currently supports:

### Core Features
- **Automated Setup**: Programmatically creates and initializes a multi-table SQLite database
- **Intelligent User ID Caching**: Resolves X usernames to IDs and caches them to minimize API calls
- **Efficient Tweet Fetching**: Uses since_id mechanism to fetch only new, unprocessed tweets
- **Robust Pick Detection**: Parses tweets line-by-line to detect various MLB bet types:
  - Team Moneylines
  - Run Lines (Spreads)
  - Totals (Over/Under)
  - Player Props (Total Bases, Hits, Home Runs, RBIs, etc.)
- **Intelligent Entity Recognition**: Uses data maps and real-time API validation to identify MLB teams and players
- **Data Storage & Deduplication**: Stores picks in relational format, preventing duplicates
- **Automated Result Grading**: Fetches game data from MLB-StatsAPI and grades all supported bet types
- **Tested & Verified**: Comprehensive pytest suite with CI/CD pipeline

### Supported Bet Types
- **MLB Team Bets**: Moneyline, Run Line, Totals (Full Game & First 5 Innings)
- **MLB Player Props**: Total Bases, Hits, Home Runs, RBIs, Runs, Strikeouts, Walks, Stolen Bases, and more

## 🏗️ Project Architecture

The project uses a modular, service-based architecture:

```
src/capper_ranks/
├── bot.py              # Main application entry point and orchestrator
├── services/
│   ├── pick_detector.py    # "Brain" of the bot - pick detection logic
│   ├── sports_api.py       # External sports data API communication
│   └── x_client.py         # X (Twitter) API communication
├── database/
│   └── models.py           # SQLite database interactions
├── core/
│   ├── config.py           # Configuration and environment variables
│   └── mappings.py         # Static data maps for teams and players
└── utils/
    └── helpers.py          # Utility functions
```

## 🛠️ Installation & Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Initialize the database: `python -m capper_ranks.database.models`
5. Run the bot: `python -m capper_ranks.bot`

## 🧪 Testing

Run the test suite:
```bash
pytest
```

The project includes comprehensive tests for pick detection, API integration, and edge cases.

## 🗺️ Roadmap

### Immediate Next Steps (Next 1-2 Weeks)

#### 1. **Parlay/Multi-Pick Detection**
- [ ] Refactor `pick_detector.py` to extract all valid picks from a single tweet
- [ ] Update detection logic to return multiple "legs" instead of just the first pick
- [ ] Add comprehensive tests for multi-pick tweets
- [ ] Update database storage to handle parlay bets properly

#### 2. **Bot Autonomy**
- [ ] Implement robust main loop with `while True:` and `time.sleep()`
- [ ] Add comprehensive error handling and logging
- [ ] Create monitoring and alerting for bot health
- [ ] Add graceful shutdown handling

#### 3. **Public X Interaction**
- [ ] Implement retweeting of detected picks
- [ ] Add logic to post WIN/LOSS results as comments
- [ ] Create engagement tracking for bot posts
- [ ] Add rate limiting for X API interactions

### Medium-Term Goals (Next 1-3 Months)

#### 4. **Image-Based Pick Detection (OCR)**
- [ ] Integrate OCR library (Tesseract) for processing bet slip images
- [ ] Build pipeline to extract text from images and run existing detection
- [ ] Add confidence scoring and failure logging
- [ ] Test with various image formats and qualities

#### 5. **Multi-Sport Expansion**
- [ ] Add NFL team and player prop support
- [ ] Add NBA team and player prop support
- [ ] Expand stat type mappings for new sports
- [ ] Update result grading logic for new sports

#### 6. **Data Presentation & Community**
- [ ] Build automated daily/weekly leaderboard generation
- [ ] Create scripts to tweet performance statistics
- [ ] Develop simple web dashboard for public stats
- [ ] Add data export functionality

### Long-Term Vision (3-12 Months)

#### 7. **Infrastructure & Scaling**
- [ ] Plan migration to PostgreSQL for larger datasets
- [ ] Implement caching layer for API responses
- [ ] Add monitoring and analytics dashboard
- [ ] Consider containerization (Docker) for deployment

#### 8. **API & Data Reliability**
- [ ] Monitor MLB-StatsAPI for breaking changes
- [ ] Develop fallback scrapers for critical data
- [ ] Evaluate paid API alternatives for reliability
- [ ] Implement data validation and integrity checks

#### 9. **Community & Monetization**
- [ ] Build Discord/Telegram bot for community engagement
- [ ] Explore affiliate marketing partnerships
- [ ] Develop premium subscription features
- [ ] Plan X API tier upgrade for scaling

#### 10. **Advanced Features**
- [ ] Implement ML-based pick detection for edge cases
- [ ] Add sentiment analysis for capper confidence
- [ ] Build predictive models for pick success rates
- [ ] Create API for third-party integrations

## 🚧 Current Challenges

### Technical Limitations
- **X API Rate Limits**: Basic tier severely constrains scaling
- **Pick Detection Complexity**: Continuous refinement needed for new formats
- **Image-Based Picks**: No OCR capability for bet slip images
- **Dependency on Unofficial APIs**: MLB-StatsAPI wrapper risk

### Strategic Considerations
- **Data Quality**: Ensuring accurate pick detection across diverse formats
- **Scalability**: Balancing feature development with API cost constraints
- **Community Building**: Growing user base while maintaining data quality

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📞 Contact

aakshintala@gmail.com
