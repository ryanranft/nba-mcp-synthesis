-- Arbitrage Opportunities Table
-- Stores detected arbitrage opportunities across multiple bookmakers
--
-- This table tracks guaranteed profit opportunities where you can bet on all
-- outcomes at different bookmakers and profit regardless of the result.
--
-- Author: NBA MCP Synthesis Team
-- Date: 2025-01-05

CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    arb_id SERIAL PRIMARY KEY,

    -- Event identification
    event_id VARCHAR(255) NOT NULL,
    game_date DATE NOT NULL,
    matchup VARCHAR(255) NOT NULL,
    market_type VARCHAR(50) NOT NULL DEFAULT 'h2h',

    -- Bookmaker A (best odds for outcome A)
    bookmaker_a VARCHAR(100) NOT NULL,
    side_a VARCHAR(100) NOT NULL,
    odds_a_american DECIMAL(10, 2) NOT NULL,
    odds_a_decimal DECIMAL(10, 4) NOT NULL,

    -- Bookmaker B (best odds for outcome B)
    bookmaker_b VARCHAR(100) NOT NULL,
    side_b VARCHAR(100) NOT NULL,
    odds_b_american DECIMAL(10, 2) NOT NULL,
    odds_b_decimal DECIMAL(10, 4) NOT NULL,

    -- Arbitrage calculations
    arb_percentage DECIMAL(6, 4) NOT NULL,  -- e.g., 0.0180 = 1.8% guaranteed profit
    total_implied_prob DECIMAL(6, 4) NOT NULL,  -- e.g., 0.9820 = 98.2% (< 100% = arb exists)

    -- Recommended stakes (for $1000 total investment)
    stake_a DECIMAL(10, 2),
    stake_b DECIMAL(10, 2),
    guaranteed_profit DECIMAL(10, 2),

    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- When odds likely to change (detected_at + 5 minutes)
    is_valid BOOLEAN DEFAULT TRUE,  -- False if arbitrage closed
    validation_note TEXT,  -- Reason if invalidated

    -- Notification tracking
    email_sent BOOLEAN DEFAULT FALSE,
    sms_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMP,

    -- Indexes
    CONSTRAINT valid_arb_percentage CHECK (arb_percentage > 0),
    CONSTRAINT different_bookmakers CHECK (bookmaker_a != bookmaker_b)
);

-- Indexes for performance
CREATE INDEX idx_arb_game_date ON arbitrage_opportunities(game_date);
CREATE INDEX idx_arb_event_id ON arbitrage_opportunities(event_id);
CREATE INDEX idx_arb_detected_at ON arbitrage_opportunities(detected_at DESC);
CREATE INDEX idx_arb_valid ON arbitrage_opportunities(is_valid) WHERE is_valid = TRUE;
CREATE INDEX idx_arb_percentage ON arbitrage_opportunities(arb_percentage DESC);

-- Comments
COMMENT ON TABLE arbitrage_opportunities IS 'Tracks detected arbitrage betting opportunities across multiple bookmakers';
COMMENT ON COLUMN arbitrage_opportunities.arb_percentage IS 'Guaranteed profit percentage (0.0180 = 1.8% profit)';
COMMENT ON COLUMN arbitrage_opportunities.total_implied_prob IS 'Sum of implied probabilities (< 1.0 indicates arbitrage)';
COMMENT ON COLUMN arbitrage_opportunities.is_valid IS 'FALSE if odds have moved and arbitrage no longer exists';
COMMENT ON COLUMN arbitrage_opportunities.expires_at IS 'Expected expiration time (typically 5 minutes from detection)';

-- Example query: Find all valid arbitrage opportunities for today
-- SELECT
--     matchup,
--     bookmaker_a,
--     side_a,
--     odds_a_american,
--     bookmaker_b,
--     side_b,
--     odds_b_american,
--     arb_percentage,
--     guaranteed_profit
-- FROM arbitrage_opportunities
-- WHERE game_date = CURRENT_DATE
--   AND is_valid = TRUE
--   AND expires_at > NOW()
-- ORDER BY arb_percentage DESC;
