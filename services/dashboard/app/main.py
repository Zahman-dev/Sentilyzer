import os
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import and_, desc, func

# Add common module to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from services.common.app.db.models import RawArticle, SentimentScore
from services.common.app.db.session import create_db_session
from services.common.app.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(service_name="dashboard")
logger = get_logger("dashboard")

# Page config
st.set_page_config(
    page_title="Sentilyzer Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 0.5rem solid #1f77b4;
}
.positive-sentiment {
    color: #28a745;
    font-weight: bold;
}
.negative-sentiment {
    color: #dc3545;
    font-weight: bold;
}
.neutral-sentiment {
    color: #6c757d;
    font-weight: bold;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 4px 4px 0 0;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
}
.stTabs [aria-selected="true"] {
    background-color: #1f77b4;
    color: white;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_stats() -> dict:
    """Get basic database statistics."""
    try:
        db = create_db_session()

        total_articles = db.query(RawArticle).count()
        processed_articles = db.query(RawArticle).filter(RawArticle.is_processed).count()
        error_articles = db.query(RawArticle).filter(RawArticle.has_error).count()

        # Get latest article
        latest_article = (
            db.query(RawArticle).order_by(desc(RawArticle.published_at)).first()
        )
        latest_date = latest_article.published_at if latest_article else None

        # Ensure latest_date is timezone-aware
        if latest_date is not None:
            if latest_date.tzinfo is None:
                latest_date = latest_date.replace(tzinfo=timezone.utc)

            # Add debug logging for database datetime
            logger.info(
                f"Database latest_date: {latest_date} (type: {type(latest_date)}, tzinfo: {latest_date.tzinfo})"
            )

        # Get sentiment distribution
        sentiment_dist = (
            db.query(
                SentimentScore.sentiment_label,
                func.count(SentimentScore.id).label("count"),
            )
            .group_by(SentimentScore.sentiment_label)
            .all()
        )

        # Get articles by source
        source_dist = (
            db.query(RawArticle.source, func.count(RawArticle.id).label("count"))
            .group_by(RawArticle.source)
            .all()
        )

        # Get tickers with most articles
        ticker_dist = (
            db.query(RawArticle.ticker, func.count(RawArticle.id).label("count"))
            .filter(RawArticle.ticker.isnot(None))
            .group_by(RawArticle.ticker)
            .order_by(desc("count"))
            .limit(10)
            .all()
        )

        db.close()

        return {
            "total_articles": total_articles,
            "processed_articles": processed_articles,
            "error_articles": error_articles,
            "processing_rate": processed_articles / max(total_articles, 1),
            "latest_date": latest_date,
            "sentiment_distribution": {label: count for label, count in sentiment_dist},  # noqa: C416
            "source_distribution": {source: count for source, count in source_dist},  # noqa: C416
            "ticker_distribution": {ticker: count for ticker, count in ticker_dist},  # noqa: C416
        }

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}


@st.cache_data(ttl=300)
def get_sentiment_trend_data(hours: int = 24) -> pd.DataFrame:
    """Get sentiment trend data for specified hours."""
    try:
        db = create_db_session()

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)

        # Query sentiment scores grouped by hour
        sentiment_data = (
            db.query(
                func.date_trunc("hour", RawArticle.published_at).label("hour"),
                func.avg(SentimentScore.sentiment_score).label("avg_sentiment"),
                func.count(SentimentScore.id).label("article_count"),
                SentimentScore.sentiment_label,
            )
            .join(SentimentScore, RawArticle.id == SentimentScore.article_id)
            .filter(
                and_(
                    RawArticle.published_at >= start_time,
                    RawArticle.published_at <= end_time,
                )
            )
            .group_by("hour", SentimentScore.sentiment_label)
            .order_by("hour")
            .all()
        )

        db.close()

        # Convert to DataFrame
        df = pd.DataFrame(
            [
                {
                    "hour": item.hour,
                    "avg_sentiment": float(item.avg_sentiment),
                    "article_count": item.article_count,
                    "sentiment_label": item.sentiment_label,
                }
                for item in sentiment_data
            ]
        )

        return df

    except Exception as e:
        logger.error(f"Error getting sentiment trend data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_recent_articles(limit: int = 20) -> list[dict]:
    """Get recent articles with sentiment scores."""
    try:
        db = create_db_session()

        articles = (
            db.query(RawArticle, SentimentScore)
            .join(SentimentScore, RawArticle.id == SentimentScore.article_id)
            .order_by(desc(RawArticle.published_at))
            .limit(limit)
            .all()
        )

        db.close()

        result = []
        for article, sentiment in articles:
            result.append(
                {
                    "headline": article.headline,
                    "source": article.source,
                    "ticker": article.ticker,
                    "published_at": article.published_at,
                    "sentiment_score": sentiment.sentiment_score,
                    "sentiment_label": sentiment.sentiment_label,
                    "article_url": article.article_url,
                }
            )

        return result

    except Exception as e:
        logger.error(f"Error getting recent articles: {e}")
        return []


def render_overview_metrics(stats: dict):
    """Render overview metrics."""
    latest_date = stats.get("latest_date")

    # Calculate time since last article
    last_article_time_str = "N/A"
    if latest_date:
        # Both datetimes should be timezone-aware UTC
        now_utc = datetime.now(timezone.utc)
        if latest_date.tzinfo is None:
            latest_date = latest_date.replace(tzinfo=timezone.utc)
            logger.warning("Latest date was timezone-naive, converted to UTC")

        try:
            hours_ago = (now_utc - latest_date).total_seconds() / 3600

            if hours_ago < 1:
                minutes_ago = int(hours_ago * 60)
                last_article_time_str = f"{minutes_ago}m ago"
            else:
                last_article_time_str = f"{int(hours_ago)}h ago"
        except Exception as e:
            logger.error(f"Error calculating time difference: {e}")
            last_article_time_str = "Error"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Articles",
            f"{stats.get('total_articles', 0):,}",
            help="Total number of articles in the database.",
        )

    with col2:
        st.metric(
            "Processed Articles",
            f"{stats.get('processed_articles', 0):,}",
            delta=f"{stats.get('processing_rate', 0):.1%}",
            help="Percentage of articles processed for sentiment.",
        )

    with col3:
        st.metric(
            "Articles with Errors",
            f"{stats.get('error_articles', 0):,}",
            delta=None,
            help="Articles that failed during processing.",
        )

    with col4:
        st.metric(
            "Latest Article",
            last_article_time_str,
            delta=None,
            help="Time since the last article was published.",
        )


def render_sentiment_charts(stats: dict, sentiment_df: pd.DataFrame):
    """Render sentiment analysis charts."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sentiment Distribution")
        sentiment_dist = stats.get("sentiment_distribution", {})
        if sentiment_dist:
            labels = list(sentiment_dist.keys())
            values = list(sentiment_dist.values())
            colors = {"positive": "#28a745", "negative": "#dc3545", "neutral": "#6c757d"}

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        marker_colors=[colors.get(label, "#1f77b4") for label in labels],
                        textinfo="label+percent",
                        textposition="inside",
                    )
                ]
            )
            fig.update_layout(title="Overall Sentiment Distribution", height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment data available")

    with col2:
        st.subheader("Sentiment Trend (24h)")
        if not sentiment_df.empty:
            # Aggregate by hour for trend line
            hourly_avg = (
                sentiment_df.groupby("hour")["avg_sentiment"].mean().reset_index()
            )

            fig = px.line(
                hourly_avg,
                x="hour",
                y="avg_sentiment",
                title="Average Sentiment Over Time",
                labels={"avg_sentiment": "Average Sentiment Score", "hour": "Time"},
            )
            fig.add_hline(
                y=0, line_dash="dash", line_color="gray", annotation_text="Neutral"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment trend data available")


def render_source_analysis(stats: dict):
    """Render source and ticker analysis."""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Articles by Source")
        source_dist = stats.get("source_distribution", {})
        if source_dist:
            source_df = pd.DataFrame(
                list(source_dist.items()),
                columns=pd.Index(["Source", "Articles"], dtype="object")
            )
            fig = px.bar(
                source_df, x="Source", y="Articles", title="Article Count by Source"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data available")

    with col2:
        st.subheader("Top Tickers")
        ticker_dist = stats.get("ticker_distribution", {})
        if ticker_dist:
            ticker_df = pd.DataFrame(
                list(ticker_dist.items()),
                columns=pd.Index(["Ticker", "Articles"], dtype="object")
            )
            fig = px.bar(
                ticker_df,
                x="Ticker",
                y="Articles",
                title="Top 10 Tickers by Article Count",
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ticker data available")


def render_recent_articles(articles: list[dict]):
    """Render recent articles table."""
    st.subheader("Recent Articles")

    if articles:
        # Convert to DataFrame for better display
        df = pd.DataFrame(articles)

        # Format the DataFrame
        df["published_at"] = pd.to_datetime(df["published_at"]).dt.strftime(
            "%Y-%m-%d %H:%M"
        )
        df["sentiment_score"] = df["sentiment_score"].round(3)

        # Apply sentiment styling
        def style_sentiment(val):
            if val > 0.1:
                return "color: #28a745; font-weight: bold"
            elif val < -0.1:
                return "color: #dc3545; font-weight: bold"
            else:
                return "color: #6c757d; font-weight: bold"

        # Display the table
        st.dataframe(
            df[
                [
                    "headline",
                    "source",
                    "ticker",
                    "published_at",
                    "sentiment_score",
                    "sentiment_label",
                ]
            ],
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No recent articles available")


def main():
    """Main dashboard application."""
    # Dashboard title and header
    st.title("📊 Sentilyzer Dashboard")
    st.markdown("Real-time financial sentiment analysis and market insights")

    # Sidebar with refresh controls
    st.sidebar.title("Dashboard Controls")

    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.markdown("🔄 Auto-refreshing...")
        # Auto refresh every 30 seconds
        st.rerun()

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Time range selector
    time_range = st.sidebar.selectbox(
        "Time Range for Trends",
        options=[6, 12, 24, 48, 72],
        index=2,
        format_func=lambda x: f"Last {x} hours",
    )
    # Ensure time_range is not None
    if time_range is None:
        time_range = 24

    # Load data
    with st.spinner("Loading dashboard data..."):
        stats = get_database_stats()
        sentiment_df = get_sentiment_trend_data(hours=time_range)
        recent_articles = get_recent_articles()

    # Check if we have data
    if not stats:
        st.error("Unable to load data from database. Please check the connection.")
        return

    # Main dashboard tabs
    tab1, tab2, tab3 = st.tabs(["📈 Overview", "📊 Analytics", "📰 Recent Articles"])

    with tab1:
        st.header("System Overview")
        render_overview_metrics(stats)

        st.divider()
        render_sentiment_charts(stats, sentiment_df)

    with tab2:
        st.header("Data Analytics")
        render_source_analysis(stats)

        # Additional analytics
        st.subheader("Processing Health")
        col1, col2, col3 = st.columns(3)

        with col1:
            processing_rate = stats.get("processing_rate", 0) * 100
            st.metric("Processing Rate", f"{processing_rate:.1f}%")

        with col2:
            error_rate = (
                stats.get("error_articles", 0) / max(stats.get("total_articles", 1), 1)
            ) * 100
            st.metric("Error Rate", f"{error_rate:.1f}%")

        with col3:
            total_sentiment_records = sum(
                stats.get("sentiment_distribution", {}).values()
            )
            st.metric("Sentiment Records", f"{total_sentiment_records:,}")

    with tab3:
        render_recent_articles(recent_articles)

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
        Sentilyzer Dashboard - Real-time Financial Sentiment Analysis<br>
        Last updated: {}
        </div>
        """.format(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
