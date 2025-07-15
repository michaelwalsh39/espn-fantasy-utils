from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd

from espn_fantasy.constants.league import ACTIVE_LEAGUE_IDS
from espn_fantasy.tasks.reporting.weekly_data_generator import WeeklyDataGenerator
from espn_fantasy.utils.database import (
    create_engine,
    read_sql_file,
    read_oracle_query
)
from espn_fantasy.utils.email import (
    get_email_list,
    send_email
)
from espn_fantasy.utils.creds import get


class EmailReport:
    def __init__(self, subject: str, sender: str, recipient: str):
        self.msg = MIMEMultipart("alternative")
        self.msg["Subject"] = subject
        self.msg["From"] = sender
        self.msg["To"] = recipient
        self.html_sections = []

    def add_header(self, text: str):
        self.html_sections.append(f"<h1 style='color:#2E86C1;'>{text}</h1>")

    def add_paragraph(self, text: str):
        self.html_sections.append(f"<p>{text}</p>")

    def add_table(self, df: pd.DataFrame):
        table_html = df.to_html(index=False, border=0, classes="dataframe", justify="center")
        self.html_sections.append(table_html)

    def add_matchup_header(self, team_a: str, team_b: str):
        self.html_sections.append(
            f"<h2 style='color:#444;'>{team_a} vs {team_b}</h2>"
        )

    def add_team_output_table(self, df: pd.DataFrame):
        table_html = df.to_html(index=False, border=0, classes="mini-table", justify="center")
        self.html_sections.append(table_html)

    def add_team_performers(self, team_name: str, df_top_performers: pd.DataFrame, df_worst_performers: pd.DataFrame):
        self.html_sections.append(f"<div class='team-header'>{team_name}</div>")

        top_hitters = df_top_performers[(df_top_performers["Team Name"] == team_name) & (df_top_performers["position"] == "hitter")]
        top_pitchers = df_top_performers[(df_top_performers["Team Name"] == team_name) & (df_top_performers["position"] == "pitcher")]
        worst = df_worst_performers[df_worst_performers["Team Name"] == team_name]

        def add_player_row(row):
            return f"{row['player_name']} ({row['point_total']} pts)"

        if not top_hitters.empty:
            hitters_text = "<b>Top Hitters:</b><br>" + "<br>".join(add_player_row(r) for _, r in top_hitters.iterrows())
            self.html_sections.append(f"<p>{hitters_text}</p>")

        if not top_pitchers.empty:
            pitchers_text = "<b>Top Pitchers:</b><br>" + "<br>".join(add_player_row(r) for _, r in top_pitchers.iterrows())
            self.html_sections.append(f"<p>{pitchers_text}</p>")

        if not worst.empty:
            worst_text = "<b>Bum of the Week:</b><br>" + "<br>".join(add_player_row(r) for _, r in worst.iterrows())
            self.html_sections.append(f"<p>{worst_text}</p>")

    def add_matchup_summary(
          self,
          home_team: str,
          away_team: str,
          df_team_scoring: pd.DataFrame,
          df_top_performers: pd.DataFrame,
          df_worst_performers: pd.DataFrame
      ):
        self.add_matchup_header(home_team, away_team)

        df_matchup = df_team_scoring[df_team_scoring["Team Name"].isin([home_team, away_team])]
        self.add_team_output_table(df_matchup)

        self.add_team_performers(home_team, df_top_performers, df_worst_performers)
        self.add_team_performers(away_team, df_top_performers, df_worst_performers)

    def build(self):
        html = f"""
        <html>
          <head>
            <style>
              /* Main table */
              table.dataframe {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 30px;
              }}
              table.dataframe th, table.dataframe td {{
                border: 1px solid #333;
                padding: 10px;
                text-align: center;
              }}
              table.dataframe th {{
                background-color: #f2f2f2;
                font-weight: bold;
              }}

              /* Mini matchup tables */
              table.mini-table {{
                border-collapse: collapse;
                width: 65%;
                margin-bottom: 16px;
              }}
              table.mini-table th, table.mini-table td {{
                border: 1px solid #999;
                padding: 6px;
                text-align: center;
              }}
              table.mini-table th {{
                background-color: #f8f8f8;
                font-weight: bold;
              }}

              /* Headings */
              h2 {{
                font-size: 20px;
                color: #333;
                margin-top: 30px;
              }}
              .team-header {{
                font-size: 16px;
                font-weight: 600;
                margin: 10px 0 5px;
              }}

              /* Mobile responsive */
              @media only screen and (max-width: 600px) {{
                table.dataframe, table.mini-table {{
                  width: 100% !important;
                }}
                table.dataframe th, table.mini-table th,
                table.dataframe td, table.mini-table td {{
                  font-size: 12px;
                  padding: 6px;
                }}
              }}
            </style>
          </head>
          <body>
            {''.join(self.html_sections)}
          </body>
        </html>
        """        
        self.msg.attach(MIMEText(html, "html"))

        return self.msg


def main(league_id: int) :
    engine = create_engine()
    data = WeeklyDataGenerator(league_id).generate()

    email = EmailReport(
        subject=f"Week {data['current_week']} Fantasy Recap",
        sender=get("email_user"),
        recipient=get_email_list(engine, is_test=True)
    )
    email.add_header(f"Week {data['current_week']} Summary 🦆⚾")
    email.add_paragraph("Duck Pond members,")
    email.add_paragraph(f"Below you'll find the updated luck chart and Week {data['current_week']}'s matchup recaps.")
    email.add_table(data["luck_chart"])

    sql = sql = read_sql_file("matchup")
    df_matchup = read_oracle_query(sql, engine, league_id=1, matchup_period_id=data["current_week"])

    # loop through matchups and add summaries
    for i in range(0, len(df_matchup)) :
        email.add_matchup_summary(
            home_team=df_matchup["home_team_name"][i],
            away_team=df_matchup["away_team_name"][i],
            df_team_scoring=data["team_scoring"],
            df_top_performers=data["top_performers"],
            df_worst_performers=data["worst_performers"]
        )

    msg = email.build()
    send_email(msg)


if __name__ == "__main__" :
    # set up to take in multiple league_ids, but just hard-code knowing we only have one right now
    league_id = ACTIVE_LEAGUE_IDS[0]
    main(league_id)
