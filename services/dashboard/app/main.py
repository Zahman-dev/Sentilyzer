import os
import sys
from datetime import datetime, timedelta

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output
from sqlalchemy import desc, func
import streamlit as st
from sqlalchemy.orm import Session

# Add common module to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../common"))

from services.common.app.db.models import RawArticle, SentimentScore
from services.common.app.db.session import create_db_session
from services.common.app.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(service_name="dashboard")
logger = get_logger("dashboard")

# Initialize Dash app
app = dash.Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title="Sentilyzer Dashboard"
)

# Layout components
header = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H1("Sentilyzer Dashboard", className="text-white mb-0"),
                        className="col-12",
                    )
                ],
                align="center",
                className="flex-grow-1",
            )
        ],
        fluid=True,
    ),
    dark=True,
    color="primary",
    className="mb-4",
)

# Create layout
app.layout = dbc.Container(
    [
        header,
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Sentiment Analysis Overview"),
                                dbc.CardBody(
                                    [
                                        dcc.Graph(id="sentiment-trend"),
                                        dcc.Interval(
                                            id="interval-component",
                                            interval=300000,  # 5 minutes
                                            n_intervals=0,
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ],
                    width=12,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Recent Articles"),
                                dbc.CardBody([html.Div(id="recent-articles")]),
                            ]
                        )
                    ],
                    width=12,
                )
            ],
            className="mt-4",
        ),
    ],
    fluid=True,
)


@app.callback(
    Output("sentiment-trend", "figure"), Input("interval-component", "n_intervals")
)
def update_sentiment_trend(_):
    """Update sentiment trend graph."""
    try:
        # Get database session
        db = create_db_session()

        # Get sentiment scores for the last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        # Query sentiment scores
        scores = (
            db.query(
                func.date_trunc("hour", RawArticle.created_at).label("hour"),
                func.avg(SentimentScore.sentiment_score).label("avg_score"),
            )
            .join(SentimentScore)
            .filter(RawArticle.created_at.between(start_time, end_time))
            .group_by("hour")
            .order_by("hour")
            .all()
        )

        # Convert to pandas DataFrame
        df = pd.DataFrame(
            [(score.hour, score.avg_score) for score in scores],
            columns=["hour", "avg_score"],
        )

        # Create figure
        figure = {
            "data": [
                {
                    "x": df["hour"],
                    "y": df["avg_score"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Average Sentiment",
                }
            ],
            "layout": {
                "title": "Sentiment Trend (Last 24 Hours)",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Average Sentiment Score"},
            },
        }

        return figure

    except Exception as e:
        logger.error("Error updating sentiment trend: {}".format(str(e)))
        return {}

    finally:
        if "db" in locals():
            db.close()


@app.callback(
    Output("recent-articles", "children"), Input("interval-component", "n_intervals")
)
def update_recent_articles(_):
    """Update recent articles list."""
    try:
        # Get database session
        db = create_db_session()

        # Get recent articles with sentiment scores
        articles = (
            db.query(RawArticle, SentimentScore)
            .join(SentimentScore)
            .order_by(desc(RawArticle.created_at))
            .limit(10)
            .all()
        )

        # Create article cards
        article_cards = []
        for article, score in articles:
            card = dbc.Card(
                [
                    dbc.CardHeader(
                        "Source: {} | Score: {:.2f}".format(
                            article.source, score.sentiment_score
                        )
                    ),
                    dbc.CardBody(
                        [
                            html.P(article.content[:200] + "..."),
                            html.Small(
                                "Created at: {}".format(
                                    article.created_at.strftime("%Y-%m-%d %H:%M:%S")
                                )
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            )
            article_cards.append(card)

        return article_cards

    except Exception as e:
        logger.error("Error updating recent articles: {}".format(str(e)))
        return []

    finally:
        if "db" in locals():
            db.close()


@st.cache_data(ttl=600)
def get_data(_db_session: Session) -> pd.DataFrame:
    """
    Fetches and processes data from the database.
    The session object is passed with an underscore to signal to Streamlit
    that it should not be hashed.
    """
    logger.info("Fetching data from the database.")
    try:
        query = (
            _db_session.query(
                RawArticle.headline,
                RawArticle.published_at,
                SentimentScore.sentiment_score,
                SentimentScore.sentiment_label,
            )
            .join(SentimentScore, RawArticle.id == SentimentScore.article_id)
            .order_by(RawArticle.published_at.desc())
            .limit(100)
        )
        df = pd.read_sql(query.statement, _db_session.bind)
        logger.info(f"Successfully fetched {len(df)} records.")
        return df
    except Exception as e:
        logger.error(f"Error fetching data: {e}", exc_info=True)
        return pd.DataFrame()


def main():
    st.set_page_config(page_title="Sentilyzer Dashboard", layout="wide")
    st.title("Sentilyzer: Sentiment Analysis Dashboard")

    db_session = create_db_session()
    if not db_session:
        st.error("Could not connect to the database. Please check the connection.")
        return

    try:
        df = get_data(db_session)

        if df.empty:
            st.warning("No data available to display.")
            return

        st.subheader("Latest Sentiment Analysis Results")
        st.dataframe(df)

        st.sidebar.header("Filters")
        sentiment_filter = st.sidebar.multiselect(
            "Filter by sentiment:",
            options=df["sentiment_label"].unique(),
            default=df["sentiment_label"].unique(),
        )

        filtered_df = df[df["sentiment_label"].isin(sentiment_filter)]

        st.subheader("Sentiment Distribution")
        if not filtered_df.empty:
            sentiment_counts = filtered_df["sentiment_label"].value_counts()
            st.bar_chart(sentiment_counts)
        else:
            st.info("No data for the selected sentiment filters.")

    except Exception as e:
        logger.error(f"An error occurred in the dashboard: {e}", exc_info=True)
        st.error("An error occurred while rendering the dashboard.")
    finally:
        if db_session:
            db_session.close()


if __name__ == "__main__":
    main()
