import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# Page configuration
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
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1E3A8A;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert > div {
        padding: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Configuration
SIGNALS_API_URL = "http://signals_api:8000"  # Docker service name
DEFAULT_TICKER = "AAPL"


def call_signals_api(
    ticker: str, start_date: str, end_date: str, api_key: str
) -> Optional[Dict]:
    """Call the signals API and return the response"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {"ticker": ticker, "start_date": start_date, "end_date": end_date}

        response = requests.post(
            f"{SIGNALS_API_URL}/v1/signals", headers=headers, json=payload, timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None


def create_sentiment_chart(data: List[Dict]) -> go.Figure:
    """Create a sentiment analysis chart"""
    df = pd.DataFrame(data)

    if df.empty:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

    # Convert published_at to datetime
    df["published_at"] = pd.to_datetime(df["published_at"])
    df = df.sort_values("published_at")

    # Color mapping for sentiment
    color_map = {"positive": "#10B981", "negative": "#EF4444", "neutral": "#6B7280"}

    fig = go.Figure()

    # Add scatter plot for sentiment scores
    fig.add_trace(
        go.Scatter(
            x=df["published_at"],
            y=df["sentiment_score"],
            mode="markers+lines",
            marker=dict(
                color=[
                    color_map.get(label, "#6B7280") for label in df["sentiment_label"]
                ],
                size=8,
                line=dict(width=1, color="white"),
            ),
            line=dict(width=2, color="rgba(99, 102, 241, 0.3)"),
            name="Sentiment Score",
            hovertemplate="<b>%{text}</b><br>"
            + "Date: %{x}<br>"
            + "Score: %{y:.3f}<br>"
            + "Sentiment: %{customdata}<br>"
            + "<extra></extra>",
            text=df["headline"].str[:50] + "...",
            customdata=df["sentiment_label"],
        )
    )

    # Add horizontal reference lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_hline(y=0.1, line_dash="dot", line_color="green", opacity=0.3)
    fig.add_hline(y=-0.1, line_dash="dot", line_color="red", opacity=0.3)

    fig.update_layout(
        title="Sentiment Analysis Over Time",
        xaxis_title="Date",
        yaxis_title="Sentiment Score",
        hovermode="closest",
        showlegend=False,
        height=500,
        template="plotly_white",
    )

    return fig


def create_sentiment_distribution(data: List[Dict]) -> go.Figure:
    """Create a sentiment distribution pie chart"""
    df = pd.DataFrame(data)

    if df.empty:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

    # Count sentiment labels
    sentiment_counts = df["sentiment_label"].value_counts()

    colors = ["#10B981", "#EF4444", "#6B7280"]  # Green, Red, Gray

    fig = go.Figure(
        data=[
            go.Pie(
                labels=sentiment_counts.index,
                values=sentiment_counts.values,
                marker_colors=colors[: len(sentiment_counts)],
                textinfo="label+percent",
                textposition="auto",
                hovertemplate="<b>%{label}</b><br>"
                + "Count: %{value}<br>"
                + "Percentage: %{percent}<br>"
                + "<extra></extra>",
            )
        ]
    )

    fig.update_layout(title="Sentiment Distribution", height=400, showlegend=False)

    return fig


def main():
    # Header
    st.markdown(
        '<div class="main-header">📊 Sentilyzer Dashboard</div>', unsafe_allow_html=True
    )

    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")

    # API Key input
    api_key = st.sidebar.text_input(
        "API Key", type="password", help="Enter your Sentilyzer API key"
    )

    # Ticker input (for future use)
    ticker = st.sidebar.text_input(
        "Stock Ticker", value=DEFAULT_TICKER, help="Currently used for display only"
    )

    # Date range selection
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
        )

    with col2:
        end_date = st.date_input(
            "End Date", value=datetime.now(), max_value=datetime.now()
        )

    # Validate dates
    if start_date >= end_date:
        st.sidebar.error("Start date must be before end date")
        return

    # Fetch data button
    if st.sidebar.button("🔍 Fetch Data", type="primary"):
        if not api_key:
            st.sidebar.error("Please enter your API key")
            return

        # Show loading spinner
        with st.spinner("Fetching sentiment data..."):
            # Convert dates to ISO format
            start_date_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
            end_date_str = end_date.strftime("%Y-%m-%dT23:59:59Z")

            # Call the API
            response = call_signals_api(ticker, start_date_str, end_date_str, api_key)

            if response and "data" in response:
                data = response["data"]

                if not data:
                    st.warning("No data found for the selected date range")
                    return

                # Store data in session state
                st.session_state["sentiment_data"] = data
                st.session_state["ticker"] = ticker
                st.session_state["date_range"] = f"{start_date} to {end_date}"
                st.success(f"Found {len(data)} articles")

    # Display results if data exists
    if "sentiment_data" in st.session_state:
        data = st.session_state["sentiment_data"]

        # Summary metrics
        st.subheader("📈 Summary")

        df = pd.DataFrame(data)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Articles", len(data))

        with col2:
            avg_sentiment = df["sentiment_score"].mean()
            st.metric("Average Sentiment", f"{avg_sentiment:.3f}")

        with col3:
            positive_count = len(df[df["sentiment_label"] == "positive"])
            st.metric("Positive Articles", positive_count)

        with col4:
            negative_count = len(df[df["sentiment_label"] == "negative"])
            st.metric("Negative Articles", negative_count)

        # Charts
        st.subheader("📊 Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Sentiment over time chart
            fig1 = create_sentiment_chart(data)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Sentiment distribution
            fig2 = create_sentiment_distribution(data)
            st.plotly_chart(fig2, use_container_width=True)

        # Detailed data table
        st.subheader("📋 Detailed Data")

        # Prepare data for display
        display_df = df.copy()
        display_df["published_at"] = pd.to_datetime(
            display_df["published_at"]
        ).dt.strftime("%Y-%m-%d %H:%M")
        display_df["sentiment_score"] = display_df["sentiment_score"].round(3)

        # Add color coding
        def color_sentiment(val):
            if val == "positive":
                return "background-color: #DEF7EC; color: #065F46"
            elif val == "negative":
                return "background-color: #FEE2E2; color: #991B1B"
            else:
                return "background-color: #F3F4F6; color: #374151"

        styled_df = display_df.style.applymap(
            color_sentiment, subset=["sentiment_label"]
        )

        st.dataframe(
            styled_df,
            column_config={
                "article_url": st.column_config.LinkColumn("Article URL"),
                "headline": st.column_config.TextColumn("Headline", width="large"),
                "published_at": st.column_config.TextColumn("Published"),
                "sentiment_score": st.column_config.NumberColumn(
                    "Score", format="%.3f"
                ),
                "sentiment_label": st.column_config.TextColumn("Sentiment"),
            },
            use_container_width=True,
            hide_index=True,
        )

        # Export functionality
        st.subheader("💾 Export Data")

        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"sentilyzer_data_{ticker}_{start_date}_{end_date}.csv",
                mime="text/csv",
            )

        with col2:
            json_data = json.dumps(data, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"sentilyzer_data_{ticker}_{start_date}_{end_date}.json",
                mime="application/json",
            )

    else:
        # Welcome message
        st.info(
            "👋 Welcome to Sentilyzer Dashboard! Enter your API key and click 'Fetch Data' to get started."
        )

        # Instructions
        st.subheader("🔧 How to Use")
        st.markdown(
            """
        1. **Enter your API Key**: Get your API key from the Sentilyzer platform
        2. **Select Date Range**: Choose the time period you want to analyze
        3. **Fetch Data**: Click the button to retrieve sentiment analysis data
        4. **Explore Results**: View charts, metrics, and detailed data
        5. **Export Data**: Download results in CSV or JSON format
        """
        )

        # API Key generation help
        st.subheader("🔑 Need an API Key?")
        st.markdown(
            """
        To generate an API key, run the following command:
        ```bash
        python scripts/generate_api_key.py
        ```
        """
        )


if __name__ == "__main__":
    main()
