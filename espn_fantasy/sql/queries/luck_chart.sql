WITH scoreboard AS (
    SELECT
        t.team_id,
        t.team_name,
        m.matchup_period_id AS week_num,
        pt.points,
        MEDIAN(pt.points) OVER (PARTITION BY m.matchup_period_id) AS median_points,
        pt.points - (MEDIAN(pt.points) OVER (PARTITION BY m.matchup_period_id)) AS distance_from_median,
        CASE
            WHEN pt.team_id = m.home_team_id
                THEN m.away_team_id
            ELSE m.home_team_id
        END AS opponent_team_id
    FROM matchup_scoring_period_team pt
    JOIN matchup m
        ON pt.league_id = m.league_id
            AND pt.matchup_id = m.matchup_id
    JOIN team t
        ON pt.team_id = t.team_id
    WHERE agg_type = 'weekly'
        AND m.league_id = :league_id
),
luck_scoreboard AS (
    SELECT
        s.team_id,
        s.team_name,
        s.week_num,
        (RANK() OVER (PARTITION BY s.week_num ORDER BY s.distance_from_median)) AS week_rank,
        COUNT(*) OVER (PARTITION BY s.week_num) AS num_teams,
        CASE
            WHEN s.points > opp.points
                THEN 1
            ELSE 0
        END AS wins,
        CASE
            WHEN s.points < opp.points
                THEN 1
            ELSE 0
        END AS losses,
        CASE
            WHEN s.points = opp.points
                THEN 1
            ELSE 0
        END AS ties,
        CASE
            WHEN s.points > s.median_points
                THEN 1
            ELSE 0
        END AS luck_wins,
        CASE
            WHEN s.points < s.median_points
                THEN 1
            ELSE 0
        END AS luck_losses,
        CASE
            WHEN s.points = s.median_points
                THEN 1
            ELSE 0
        END AS luck_ties
    FROM scoreboard s
    JOIN scoreboard opp
        ON s.week_num = opp.week_num
            AND s.opponent_team_id = opp.team_id
)
SELECT
    team_id,
    team_name,
    SUM(wins) AS wins,
    SUM(losses) AS losses,
    SUM(ties) AS ties,
    SUM(luck_wins) AS luck_wins,
    SUM(luck_losses) AS luck_losses,
    SUM(luck_ties) AS luck_ties,
    SUM(
        CASE
            WHEN week_rank <= FLOOR(num_teams / 2.0) AND wins > 0
                THEN (FLOOR(num_teams / 2.0) + 1) - week_rank
            WHEN week_rank > FLOOR(num_teams / 2.0) AND losses > 0
                THEN FLOOR(num_teams / 2.0) - week_rank
            ELSE 0
        END
    ) AS luck_pts
FROM luck_scoreboard
GROUP BY
    team_id,
    team_name