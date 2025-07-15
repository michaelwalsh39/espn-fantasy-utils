import pandas as pd
import sqlalchemy as sa
from espn_fantasy.utils.database import (
    create_engine,
    read_oracle_query,
    read_sql_file
)


class WeeklyDataGenerator:
    def __init__(self, league_id: int) :
        self.league_id = league_id

        self.engine = create_engine()
        self.current_week = self._get_current_week()
    
    def _get_current_week(self) :
        sql = read_sql_file("current_week")
        df = read_oracle_query(
            sql, self.engine, league_id=self.league_id
        )

        return str(df.loc[0, "week_num"])

    def _generate_luck_chart(self) :
        sql = read_sql_file("luck_chart")
        df = read_oracle_query(
            sql, self.engine, league_id=self.league_id
        )
        df = df.sort_values(by="wins", ascending=False)

        df["Actual Record"] = df["wins"].astype(str) + "-" + df["losses"].astype(str) + "-" + df["ties"].astype(str)
        df["Adjusted Record"] = df["luck_wins"].astype(str) + "-" + df["luck_losses"].astype(str) + "-" + df["luck_ties"].astype(str)
        for i in ["wins", "losses", "luck_wins", "luck_losses", "ties", "luck_ties", "team_id"] :
            del df[i]

        self.df_luck = df.rename(columns={
            "team_name": "Team Name",
            "luck_pts": "Luck Points"
        })
        self.df_luck = self.df_luck[["Team Name", "Actual Record", "Adjusted Record", "Luck Points"]]

    def _generate_player_data(self) :
        sql = read_sql_file("player_weekly_performance")
        df_player = read_oracle_query(
            sql, self.engine, league_id=self.league_id, matchup_period_id=self.current_week
        )

        self.df_top_performers = (
            df_player.groupby(["team_id", "position"], group_keys=False)
            .apply(lambda g: g.nlargest(3, "point_total"))
        )
        del self.df_top_performers["team_id"]
        self.df_top_performers = self.df_top_performers.rename(columns={
            "team_name": "Team Name"
        })

        self.df_worst_performers = (
            df_player.groupby("team_id", group_keys=False)
            .apply(lambda g: g.nsmallest(1, "point_total"))
        )
        del self.df_worst_performers["team_id"]
        self.df_worst_performers = self.df_worst_performers.rename(columns={
            "team_name": "Team Name"
        })

        # initialize dfs we'll need to use later
        self.df_team_totals = df_player.groupby("team_id")["point_total"].sum().reset_index()
        self.df_position_aggs = df_player.groupby(["team_id", "position"])["point_total"].sum().reset_index()
    
    def _generate_team_data(self) :
        sql = read_sql_file("team_weekly_performance")
        df_team = read_oracle_query(
            sql, self.engine, league_id=self.league_id, matchup_period_id=self.current_week
        )

        df_pivot = df_team.pivot(index=["team_id", "team_name", "week_num"], columns="day_of_week", values="point_total")
        df_pivot.columns = [f"Day {int(col)}" for col in df_pivot.columns]
        df_pivot = df_pivot.reset_index()

        df_team_scoring = pd.merge(df_pivot, self.df_team_totals, on="team_id").rename(columns={"point_total": "Total"})
        df_team_scoring = pd.merge(df_team_scoring, self.df_position_aggs[self.df_position_aggs["position"] == "hitter"], on="team_id").rename(columns={"point_total": "Offense"}).drop(columns=["position"])

        self.df_team_scoring = pd.merge(df_team_scoring, self.df_position_aggs[self.df_position_aggs["position"] == "pitcher"], on="team_id").rename(columns={"point_total": "Pitching"}).drop(columns=["position"])
        for i in ["team_id", "week_num"] :
            del self.df_team_scoring[i]
        self.df_team_scoring = self.df_team_scoring.rename(columns={
            "team_name": "Team Name"
        })

    def generate(self) :
        self._generate_luck_chart()
        self._generate_player_data()
        self._generate_team_data()

        return {
            "current_week": self.current_week,
            "luck_chart": self.df_luck,
            "top_performers": self.df_top_performers,
            "worst_performers": self.df_worst_performers,
            "team_scoring": self.df_team_scoring
        }
