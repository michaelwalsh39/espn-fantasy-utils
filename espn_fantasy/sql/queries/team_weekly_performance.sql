SELECT
    m.matchup_period_id AS week_num,
    ROW_NUMBER() OVER (PARTITION BY t.team_id ORDER BY mt.scoring_period_id) AS day_of_week,
    t.team_id,
    t.team_name,
    points AS point_total
FROM matchup_scoring_period_team mt
JOIN matchup m
    ON mt.matchup_id = m.matchup_id
JOIN team t
    ON mt.team_id = t.team_id
WHERE mt.agg_type = 'daily'
    AND m.matchup_period_id = :matchup_period_id
    AND m.league_id = :league_id