# Dashboard User Guide

This document explains how to use the **Streamlit**-based Dashboard that visualizes and enables interactive analysis of Sentilyzer project data.

> **Access Address:** [http://localhost:8501](http://localhost:8501)

## Purpose

The Dashboard is designed to help end users and analysts easily see sentiment changes over time for a specific stock, examine news headlines, and quickly gain insights about general market sentiment.

## Components and Usage

The Dashboard typically consists of the following core components:

1.  **Stock Selection Area (Ticker Input):**
    - A text box where you can enter the symbol of the stock you want to analyze (e.g., `AAPL`, `TSLA`, `GOOGL`).

2.  **Date Range Selection:**
    - A calendar tool that allows you to select which time period's data you want to view.

3.  **Sentiment Analysis Time Series Chart:**
    - A line graph showing the change in daily average sentiment score over time for the selected stock and date range.
    - This graph is useful for detecting sudden rises or falls in market sentiment.

4.  **News Headlines and Scores Table:**
    - Shows a list of relevant news articles in the selected period.
    - Typically includes columns: `Date`, `News Headline`, `Source`, `Sentiment Label` (positive/negative/neutral), `Sentiment Score`.
    - The table allows you to quickly scan news headlines to understand what influenced sentiment on a particular day.

> **Update Note:** When a new graph, filter, or metric is added to the Dashboard, it's important to update this user guide with relevant screenshots and explanations.
