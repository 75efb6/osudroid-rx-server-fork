-- Migration 001: Add indexes for query performance
-- Run against the PostgreSQL database.

-- ============================================================
-- scores table (heaviest query load)
-- ============================================================

-- playerID is filtered on in 10+ queries (get player scores, top plays, etc.)
CREATE INDEX IF NOT EXISTS scores_playerid_idx ON scores (playerID);

-- md5 is filtered on in 8+ queries (beatmap scores, rank lookups, etc.)
CREATE INDEX IF NOT EXISTS scores_md5_idx ON scores (md5);

-- status is filtered on in 7+ queries (ranked only, etc.)
CREATE INDEX IF NOT EXISTS scores_status_idx ON scores (status);

-- Composite for "get player's best scores on ranked maps" pattern:
--   WHERE playerID = $1 AND status = 2 AND md5 IN (...) ORDER BY pp DESC
CREATE INDEX IF NOT EXISTS scores_playerid_status_idx ON scores (playerID, status);

-- Composite for "get beatmap leaderboard" pattern:
--   WHERE md5 = $1 AND status = 2 ORDER BY pp DESC
CREATE INDEX IF NOT EXISTS scores_md5_status_pp_idx ON scores (md5, status, pp DESC);

-- Composite for "check if player already has score on map":
--   WHERE playerID = $1 AND md5 = $2 AND status = $3
CREATE INDEX IF NOT EXISTS scores_playerid_md5_status_idx ON scores (playerID, md5, status);

-- For beatmap leaderboard global placement queries:
--   WHERE md5 = $1 AND global_placement IS NOT NULL ORDER BY global_placement ASC
CREATE INDEX IF NOT EXISTS scores_md5_global_placement_idx ON scores (md5, global_placement)
    WHERE global_placement IS NOT NULL;

-- For local placement queries:
--   WHERE md5 = $1 AND playerid = $2 ORDER BY local_placement ASC
CREATE INDEX IF NOT EXISTS scores_md5_playerid_local_placement_idx ON scores (md5, playerID, local_placement);

-- ============================================================
-- maps table
-- ============================================================

-- status is filtered on in 4+ queries (get ranked maps, whitelist, etc.)
CREATE INDEX IF NOT EXISTS maps_status_idx ON maps (status);

-- md5 is used for map lookups by hash
CREATE INDEX IF NOT EXISTS maps_md5_idx ON maps (md5);

-- ============================================================
-- users table
-- ============================================================

-- country is used for country leaderboard filtering and DISTINCT country list
CREATE INDEX IF NOT EXISTS users_country_idx ON users (country)
    WHERE country IS NOT NULL;

-- For leaderboard JOINs filtering by country
CREATE INDEX IF NOT EXISTS users_id_country_idx ON users (id, country);

-- ============================================================
-- stats table
-- ============================================================

-- pp is used for global rank counting (COUNT WHERE pp > $1) and ORDER BY pp DESC
CREATE INDEX IF NOT EXISTS stats_pp_idx ON stats (pp DESC);

-- rscore is used for score rank counting (COUNT WHERE rscore > $1)
CREATE INDEX IF NOT EXISTS stats_rscore_idx ON stats (rscore DESC);
