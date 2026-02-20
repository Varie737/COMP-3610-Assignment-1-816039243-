from pathlib import Path
import streamlit as st
import polars as pl
import plotly.express as px
import pandas as pd
import plotly.io as pio

# Page configuration, title and intro
pio.templates.default = "plotly_dark"
st.set_page_config(page_title="NYC Taxi Dashboard (Jan 2024)", layout="wide")

st.title("NYC Yellow Taxi Trips — January 2024")
st.write(
    "Interactive dashboard exploring Trip demand patterns, Fare trends, Trip distances and Payment behavior "
    "for NYC Yellow Taxis in January 2024."
)

BASE_DIR = Path(__file__).resolve().parent
TRIPS_PATH = BASE_DIR / "data" / "processed" / "clean_trips.parquet"
ZONES_PATH = BASE_DIR / "data" / "raw" / "taxi_zone_lookup.csv"


# Cached data loading

@st.cache_data
def load_data():
    if not TRIPS_PATH.exists():
        st.error(
            f"Missing processed file: {TRIPS_PATH}\n\n"
            "Go back to Part 2 and save your cleaned and feature dataset to data/processed/clean_trips.parquet"
        )
        st.stop()
    if not ZONES_PATH.exists():
        st.error(f"Missing zone lookup file: {ZONES_PATH}")
        st.stop()

    trips = pl.read_parquet(TRIPS_PATH)
    zones = pl.read_csv(ZONES_PATH)
    return trips, zones

trips, zones = load_data()


# Add pickup_date for filtering 
trips = trips.with_columns(
    pl.col("tpep_pickup_datetime").dt.date().alias("pickup_date")
)

# Sidebar filters 

st.sidebar.header("Filters")

min_date = trips.select(pl.col("pickup_date").min()).item()
max_date = trips.select(pl.col("pickup_date").max()).item()

date_range = st.sidebar.date_input(
    "Pickup date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

hour_min, hour_max = st.sidebar.slider("Pickup hour range", 0, 23, (0, 23))

# map payment types to readable labels for UI
payment_map = {
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
}
payment_labels = [payment_map[k] for k in sorted(payment_map.keys())]

selected_payment_labels = st.sidebar.multiselect(
    "Payment types",
    options=payment_labels,
    default=payment_labels,
)

selected_payment_codes = [k for k, v in payment_map.items() if v in selected_payment_labels]

# Apply filters
start_date, end_date = date_range
filtered = trips.filter(
    (pl.col("pickup_date") >= pl.lit(start_date))
    & (pl.col("pickup_date") <= pl.lit(end_date))
    & (pl.col("pickup_hour") >= hour_min)
    & (pl.col("pickup_hour") <= hour_max)
    & (pl.col("payment_type").is_in(selected_payment_codes))
)

if filtered.height == 0:
    st.warning("No trips match the current filters. Try widening the date/hour range or selecting more payment types.")
    st.stop()


# Key metrics 

col1, col2, col3, col4, col5 = st.columns(5)

total_trips = filtered.height
avg_fare = filtered.select(pl.col("fare_amount").mean()).item()
total_revenue = filtered.select(pl.col("total_amount").sum()).item()
avg_distance = filtered.select(pl.col("trip_distance").mean()).item()
avg_duration = filtered.select(pl.col("trip_duration_minutes").mean()).item()

col1.metric("Total Trips", f"{total_trips:,}")
col2.metric("Average Fare", f"${avg_fare:,.2f}")
col3.metric("Total Revenue", f"${total_revenue:,.2f}")
col4.metric("Avg Trip Distance", f"{avg_distance:,.2f} mi")
col5.metric("Avg Trip Duration", f"{avg_duration:,.2f} min")

st.divider()


zones_small = zones.select(["LocationID", "Zone"])

# r) Bar chart: Top 10 pickup zones by trip count 
st.subheader("1) Top 10 Pickup Zones by Trip Count")

top_pu = (
    filtered.join(zones_small, left_on="PULocationID", right_on="LocationID", how="left")
    .group_by("Zone")
    .agg(pl.len().alias("trip_count"))
    .sort("trip_count", descending=True)
    .head(10)
)

fig1 = px.bar(top_pu.to_pandas(), x="Zone", y="trip_count", title="Top 10 Pickup Zones")
fig1.update_layout(xaxis_title="Pickup Zone", yaxis_title="Trips", xaxis_tickangle=-35)
st.plotly_chart(fig1, use_container_width=True)

st.write(
    "The highest-ranked zones concentrate a large share of pickups, suggesting strong demand hotspots. "
    "If one zone dominates, it may indicate major transit hubs or dense commercial/visitor areas within the selected filters."
)

st.divider()

# s) Line chart: Average fare by hour of day 
st.subheader("2) Average Fare by Pickup Hour")

fare_by_hour = (
    filtered.group_by("pickup_hour")
    .agg(pl.col("fare_amount").mean().alias("avg_fare"))
    .sort("pickup_hour")
)

fig2 = px.line(fare_by_hour.to_pandas(), x="pickup_hour", y="avg_fare", markers=True,
               title="Average Fare Amount by Hour of Day")
fig2.update_layout(xaxis_title="Pickup Hour (0–23)", yaxis_title="Average Fare ($)")
st.plotly_chart(fig2, use_container_width=True)

st.write(
    "Peaks in average fare correlate with commute hours and late-night travel. "
    "If fares rise overnight, it can reflect longer trips, lower traffic enabling farther travel, or different rider behavior."
)

st.divider()

# t) Histogram: Distribution of trip distances 
st.subheader("3) Distribution of Trip Distances")

# cap at 30 miles for readability while still reflecting distribution shape
dist_df = filtered.select(pl.col("trip_distance").clip(0, 30).alias("trip_distance_capped"))

fig3 = px.histogram(dist_df.to_pandas(), x="trip_distance_capped", nbins=40,
                    title="Trip Distance Distribution (Capped at 30 miles)")
fig3.update_layout(xaxis_title="Trip Distance (miles)", yaxis_title="Trips")
st.plotly_chart(fig3, use_container_width=True)

st.write(
    "Most taxi trips are typically short-to-medium distance, producing a right-skewed distribution. "
    "A long tail suggests occasional longer airport or cross-city rides."
)

st.divider()

# u) Pie or bar: Breakdown of payment types 
st.subheader("4) Payment Type Breakdown")

pay_counts = (
    filtered.group_by("payment_type")
    .agg(pl.len().alias("trips"))
    .with_columns(
        pl.col("payment_type")
        .map_elements(lambda x: payment_map.get(x, "Other"), return_dtype=pl.Utf8)
        .alias("payment_label")
    )
    .sort("trips", descending=True)
)
fig4 = px.pie(pay_counts.to_pandas(), names="payment_label", values="trips",
              title="Payment Type Share")
st.plotly_chart(fig4, use_container_width=True)

st.write(
    "A larger credit card share often implies more recorded tips (since tips are auto-populated for card payments). "
    "The majority of New Yorkers paid taxi fares."
)

st.divider()

# v) Heatmap: Trips by day of week and hour 
st.subheader("5) Trips by Day of Week and Hour (Heatmap)")

dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

heat = (
    filtered.group_by(["pickup_day_of_week", "pickup_hour"])
    .agg(pl.len().alias("trips"))
)

# ensure consistent day ordering for the heatmap
heat_pd = heat.to_pandas()
heat_pd["pickup_day_of_week"] = pd.Categorical(heat_pd["pickup_day_of_week"], categories=dow_order, ordered=True)
heat_pd = heat_pd.sort_values(["pickup_day_of_week", "pickup_hour"])

fig5 = px.density_heatmap(
    heat_pd,
    x="pickup_hour",
    y="pickup_day_of_week",  
    z="trips",
    title="Trips by Day of Week and Hour",
)
fig5.update_layout(xaxis_title="Hour (0–23)", yaxis_title="Day of Week")
st.plotly_chart(fig5, use_container_width=True)

st.write(
    "Concentrated blocks indicate consistent peak demand periods (e.g., weekday commutes or Saturday nights). "
    "Comparing weekdays vs weekends reveals demand are highest later in the day." 
    " Trips are significantly less on Sundays, especially during weekday commute hours, reflecting different travel patterns on that day."
)


