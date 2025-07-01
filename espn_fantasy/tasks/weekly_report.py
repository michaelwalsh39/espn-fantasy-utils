"""
Weekly reporting task

Right now, this only sends the updated luck chart out.
"""

import pandas as pd
import sqlalchemy as sa
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from espn_fantasy.constants.league import ACTIVE_LEAGUE_IDS
from espn_fantasy.utils.database import (
    create_engine,
    read_oracle_query
)
from espn_fantasy.utils.email import (
    get_email_list,
    send_email
)
from espn_fantasy.utils.creds import get


def get_most_recent_week(engine: sa.engine, league_id: int) -> str:
    df = read_oracle_query(
        f"""
        SELECT MAX(week_num) AS week_num
        FROM (
            SELECT
                m.matchup_period_id AS week_num,
                COUNT(DISTINCT mt.scoring_period_id) AS num_days
            FROM matchup_scoring_period_team mt
            JOIN matchup m
                ON mt.matchup_id = m.matchup_id
            WHERE m.league_id = {str(league_id)}
            GROUP BY
                m.matchup_period_id
        )
        WHERE num_days >= 7
        """, engine
    )

    return str(df.loc[0, "week_num"])


def generate_luck_chart(engine: sa.engine, league_id: int) -> pd.DataFrame :
    sql = f"""
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
            AND m.league_id = {str(league_id)}
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
    """

    engine = create_engine()
    df = read_oracle_query(
        sql, engine
    )
    df = df.sort_values(by="wins", ascending=False)

    df["Actual Record"] = df["wins"].astype(str) + "-" + df["losses"].astype(str) + "-" + df["ties"].astype(str)
    df["Adjusted Record"] = df["luck_wins"].astype(str) + "-" + df["luck_losses"].astype(str) + "-" + df["luck_ties"].astype(str)
    for i in ["wins", "losses", "luck_wins", "luck_losses", "ties", "luck_ties"] :
        del df[i]

    df = df.rename(columns={
        "team_id": "Team ID",
        "team_name": "Team Name",
        "luck_pts": "Luck Points"
    })

    return df


def main() :
    """
    Runs weekly reports, sets them up in html format, and emails results.
    """
    engine = create_engine()

    for league_id in ACTIVE_LEAGUE_IDS :
        current_week = get_most_recent_week(engine, league_id)
        df_luck = generate_luck_chart(engine, league_id)

        # set up email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Week {current_week} Weekly Report"
        msg["From"] = get("email_user")
        msg["To"] = get_email_list(engine, is_test=False)

        # html components
        table_html = df_luck.to_html(index=False, border=0, classes="dataframe", justify="center")
        header = f"<h1 style='color:#2E86C1;'>Week {current_week} Summary</h1>"
        paragraph = """<p>Duck Pond members,<p>
        <p>Below is the updated luck chart:</p>
        """

        # html body
        html = f"""
        <html>
        <head>
            <style>
            table.dataframe {{
                border-collapse: collapse;
                width: 100%;
            }}
            table.dataframe th, table.dataframe td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            table.dataframe th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            </style>
        </head>
        <body>
            {header}
            {paragraph}
            {table_html}
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))
        send_email(msg)


if __name__ == "__main__" :
    main()
