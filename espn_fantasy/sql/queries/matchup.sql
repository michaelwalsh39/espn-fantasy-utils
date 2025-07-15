SELECT
    matchup_period_id,
    matchup_id,
    home_team_id,
    th.team_name AS home_team_name,
    away_team_id,
    ta.team_name AS away_team_name
FROM matchup m
JOIN team th
    ON m.home_team_id = th.team_id
JOIN team ta
    ON m.away_team_id = ta.team_id
WHERE m.league_id = :league_id
    AND m.matchup_period_id = :matchup_period_id