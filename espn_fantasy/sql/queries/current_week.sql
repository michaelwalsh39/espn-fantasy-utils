SELECT MAX(week_num) AS week_num
FROM (
    SELECT
        m.matchup_period_id AS week_num,
        COUNT(DISTINCT mt.scoring_period_id) AS num_days
    FROM matchup_scoring_period_team mt
    JOIN matchup m
        ON mt.matchup_id = m.matchup_id
    WHERE m.league_id = :league_id
    GROUP BY
        m.matchup_period_id
)
WHERE num_days >= 7