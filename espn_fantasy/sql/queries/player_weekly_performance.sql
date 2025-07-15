SELECT
    m.matchup_period_id AS week_num,
    t.team_id,
    t.team_name,
    pl.player_id,
    pl.first_name || ' ' || pl.last_name AS player_name,
    CASE
        WHEN mp.lineup_slot_id IN (13,14,15) 
            THEN 'pitcher'
        WHEN mp.lineup_slot_id NOT IN (13,14,15)
            THEN 'hitter'
        ELSE NULL
    END AS position,
    SUM(points) AS point_total
FROM matchup_scoring_period_player mp
JOIN matchup m
    ON mp.matchup_id = m.matchup_id
JOIN team t
    ON mp.team_id = t.team_id
JOIN player pl
    ON mp.player_id = pl.player_id
WHERE mp.agg_type = 'daily'
    AND mp.lineup_slot_id NOT IN (16,17)
    AND m.matchup_period_id = :matchup_period_id
    AND m.league_id = :league_id
GROUP BY
    m.matchup_period_id,
    t.team_id,
    t.team_name,
    pl.player_id,
    pl.first_name || ' ' || pl.last_name,
    CASE
        WHEN mp.lineup_slot_id IN (13,14,15) 
            THEN 'pitcher'
        WHEN mp.lineup_slot_id NOT IN (13,14,15)
            THEN 'hitter'
        ELSE NULL
    END