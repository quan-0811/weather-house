import streamlit as st
import pandas as pd
from cassandra.cluster import Cluster
import plotly.express as px
import time
from datetime import datetime, timedelta  # <--- Added for Partition Key Logic

# Page Config
st.set_page_config(
    page_title="Weather House Pipeline",
    page_icon="🌩️",
    layout="wide"
)

st.title("🌩️ Weather House Dashboard")

@st.cache_resource(validate=lambda session: not session.is_shutdown)
def get_cassandra_session():
    """Connects to Cassandra (Speed Layer)"""
    cluster = Cluster(['cassandra'])
    for i in range(5):
        try:
            session = cluster.connect()
            row = session.execute("SELECT keyspace_name FROM system_schema.keyspaces WHERE keyspace_name='weather_house'").one()
            if row:
                session.set_keyspace('weather_house')
                return session
            time.sleep(1)
        except Exception:
            time.sleep(1)
    return None

@st.cache_data(ttl=600)
def load_parquet(layer, table_name):
    """Reads Parquet from HDFS (Silver or Gold Layers)"""
    hdfs_url = f"webhdfs://namenode:9870/weather/{layer}/{table_name}"
    try:
        df = pd.read_parquet(hdfs_url, storage_options={"user": "root"})
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def load_forecast_data():
    """Reads the latest Forecast data from Gold Layer"""
    hdfs_url = "webhdfs://namenode:9870/weather/gold/weather_forecast"
    try:
        df = pd.read_parquet(hdfs_url, storage_options={"user": "root"})
        return df
    except Exception:
        return pd.DataFrame()

def load_station_metadata():
    """
    Hybrid Loading Strategy:
    1. Try HDFS Silver Layer (Best source, deduped).
    2. Fallback to Cassandra 'location_meta_data' (Immediate source).
    """
    df = load_parquet("silver", "dim_location")
    if not df.empty:
        return df.drop_duplicates(subset=['location_id'])
    
    session = get_cassandra_session()
    if session:
        try:
            # --- MODIFIED: Query the dedicated metadata table ---
            cql = "SELECT location_id, latitude, longitude, timezone, elevation FROM location_meta_data"
            rows = session.execute(cql)
            df_speed = pd.DataFrame(list(rows))
            
            if not df_speed.empty:
                st.toast("⚠️ Map loaded from Live Stream (Silver Layer not ready)", icon="⚡")
                return df_speed.drop_duplicates(subset=['location_id'])
        except Exception:
            pass
            
    return pd.DataFrame()

st.subheader("🗺️ Station Network")

df_stations = load_station_metadata()

selected_id = None

if not df_stations.empty:
    fig_map = px.scatter_mapbox(
        df_stations, 
        lat="latitude", 
        lon="longitude",
        hover_name="location_id",
        hover_data=["timezone", "elevation"],
        zoom=6, # Start zoomed in
        height=700,
        size_max=15
    )
    fig_map.update_layout(
        mapbox_style="open-street-map", 
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox_center={"lat": 43.0, "lon": -75.0}
    )
    fig_map.update_traces(marker=dict(size=12, color='red'))

    selection = st.plotly_chart(fig_map, on_select="rerun", use_container_width=True)
    
    if selection and selection["selection"]["points"]:
        point_index = selection["selection"]["points"][0]["point_index"]
        selected_id = df_stations.iloc[point_index]["location_id"]
        st.success(f"📍 Filtering Dashboard for Station ID: **{selected_id}**")
    else:
        st.info("👆 Click on a red dot above to filter the charts below.")
else:
    st.warning("⚠️ No station metadata found in /weather/silver/dim_location. Run the Silver job first.")


tab1, tab2 = st.tabs(["⚡ Speed Layer (Real-Time)", "🐢 Batch Layer (Historical)"])

with tab1:
    st.header("Live Sensor Data")
    
    @st.fragment(run_every=2)
    def render_speed_layer(station_id):
        session = get_cassandra_session()
        
        if session:
            try:
                cols = [
                    "location_id", "time", "data_quality",
                    "temperature_2m", "apparent_temperature", "relative_humidity_2m", "dew_point_2m",
                    "pressure_msl", "surface_pressure",
                    "wind_speed_10m", "wind_speed_100m", "wind_gusts_10m", "wind_direction_10m", "wind_direction_100m",
                    "precipitation", "rain", "snowfall", "snow_depth", 
                    "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
                    "soil_temperature_0_to_7cm", "soil_temperature_7_to_28cm", "soil_temperature_28_to_100cm", "soil_temperature_100_to_255cm",
                    "soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm", "soil_moisture_28_to_100cm", "soil_moisture_100_to_255cm"
                ]
                col_str = ", ".join(cols)

                if station_id:
                    cql = f"SELECT {col_str} FROM raw_weather_data WHERE location_id = {station_id} LIMIT 200"
                    title_suffix = f"(Station {station_id})"
                    
                else:
                    # Fallback for "All Stations" (Note: This scans random partitions in the new schema)
                    cql = f"SELECT {col_str} FROM raw_weather_data LIMIT 200"
                    title_suffix = "(All Stations)"
                
                rows = list(session.execute(cql))
                df_speed = pd.DataFrame(rows)
                
                if not df_speed.empty:
                    df_speed['time'] = pd.to_datetime(df_speed['time'])
                    df_speed = df_speed.sort_values(by='time')
                    latest = df_speed.iloc[-1]
                    
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Station ID", str(latest['location_id']))
                    m2.metric("Temp", f"{latest['temperature_2m']} °C", delta=f"{latest['apparent_temperature']}°C Feels Like")
                    m3.metric("Humidity", f"{latest['relative_humidity_2m']}%")
                    m4.metric("Wind", f"{latest['wind_speed_10m']} km/h")
                    
                    status_color = "normal" if latest['data_quality'] == "OK" else "off"
                    m5.metric("Quality", latest['data_quality'], delta_color=status_color)

                    if station_id:
                        st.markdown("---")
                        st.subheader("🤖 AI Forecast (Tomorrow)")
                        
                        df_forecast = load_forecast_data()
                        
                        pred_temp = "None"
                        pred_humid = "None"
                        pred_rain = "None"
                        pred_snow = "None"
                        
                        if not df_forecast.empty:
                            station_fcast = df_forecast[df_forecast['location_id'] == station_id]
                            if not station_fcast.empty:
                                row_p = station_fcast.iloc[-1]
                                pred_temp = f"{row_p['pred_temp_c']} °C"
                                pred_humid = f"{row_p['pred_humidity']}%"
                                pred_rain = row_p['pred_is_rain']
                                pred_snow = row_p['pred_is_snow']
                        
                        p1, p2, p3, p4 = st.columns(4)
                        p1.metric("Predicted Temp", pred_temp)
                        p2.metric("Predicted Humidity", pred_humid)
                        p3.metric("Rain Probability", pred_rain, delta="Alert" if pred_rain=="YES" else None, delta_color="inverse")
                        p4.metric("Snow Probability", pred_snow, delta="Alert" if pred_snow=="YES" else None, delta_color="inverse")
                        st.markdown("---")

                    viz_t1, viz_t2, viz_t3 = st.tabs(["🌡️ Atmosphere", "💨 Wind & Sky", "🌱 Ground & Water"])

                    with viz_t1:
                        st.subheader("Thermal & Barometric Conditions")
                        
                        col_temp, col_pres = st.columns(2)
                        with col_temp:
                            fig_temp = px.line(
                                df_speed, x='time', y=['temperature_2m', 'apparent_temperature', 'dew_point_2m'],
                                title=f"Temperature Profile {title_suffix}", markers=True
                            )
                            st.plotly_chart(fig_temp, use_container_width=True)
                        
                        with col_pres:
                            fig_pres = px.line(
                                df_speed, x='time', y=['pressure_msl', 'surface_pressure'], 
                                title="Pressure Gradient (hPa)",
                                color_discrete_sequence=['purple', 'violet']
                            )
                            st.plotly_chart(fig_pres, use_container_width=True)

                    with viz_t2:
                        st.subheader("Wind Profile")
                        
                        col_wind1, col_wind2 = st.columns(2)
                        with col_wind1:
                            fig_wind = px.scatter(
                                df_speed, x='time', y='wind_speed_10m',
                                size='wind_gusts_10m', color='wind_direction_10m',
                                title=f"10m Wind Speed & Gusts (Size=Gust) {title_suffix}"
                            )
                            fig_wind.add_traces(px.line(df_speed, x='time', y='wind_speed_10m').data[0])
                            fig_wind.data[-1].line.color = 'gray'
                            st.plotly_chart(fig_wind, use_container_width=True)
                            
                        with col_wind2:
                            fig_wind_100 = px.line(df_speed, x='time', y='wind_speed_100m', title="100m Wind Speed (High Altitude)")
                            st.plotly_chart(fig_wind_100, use_container_width=True)

                        st.subheader("Sky Conditions")
                        fig_cloud = px.area(
                            df_speed, x='time', 
                            y=['cloud_cover', 'cloud_cover_low', 'cloud_cover_mid', 'cloud_cover_high'],
                            title="Cloud Cover Layers (%)"
                        )
                        st.plotly_chart(fig_cloud, use_container_width=True)

                    with viz_t3:
                        st.subheader("Hydrology & Soil Physics")
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            fig_precip = px.bar(
                                df_speed, x='time', y=['rain', 'snowfall', 'precipitation'], 
                                title="Precipitation (mm/cm)", barmode='group'
                            )
                            st.plotly_chart(fig_precip, use_container_width=True)
                            
                            fig_snow = px.line(df_speed, x='time', y='snow_depth', title="Snow Depth")
                            st.plotly_chart(fig_snow, use_container_width=True)
                        
                        with col_g2:
                            fig_soil_temp = px.line(
                                df_speed, x='time', 
                                y=['soil_temperature_0_to_7cm', 'soil_temperature_7_to_28cm', 'soil_temperature_28_to_100cm', 'soil_temperature_100_to_255cm'],
                                title="Soil Temperature by Depth"
                            )
                            st.plotly_chart(fig_soil_temp, use_container_width=True)

                            fig_soil_moist = px.line(
                                df_speed, x='time', 
                                y=['soil_moisture_0_to_7cm', 'soil_moisture_7_to_28cm', 'soil_moisture_28_to_100cm', 'soil_moisture_100_to_255cm'],
                                title="Soil Moisture by Depth"
                            )
                            st.plotly_chart(fig_soil_moist, use_container_width=True)
                    
                else:
                    st.warning("No data found in Cassandra for this selection. Start the Producer!")
            except Exception as e:
                st.error(f"Cassandra Error: {e}")
        else:
            st.error("❌ Could not connect to Cassandra. Check if the container is healthy.")
    
    render_speed_layer(selected_id)

with tab2:
    st.header("Aggregated Analytics")
    if st.button("Refresh History"):
        load_parquet.clear()
        st.rerun()

    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Daily Trends")
        df_daily = load_parquet("gold", "daily_summary")
        
        if not df_daily.empty:
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
            if selected_id:
                df_daily = df_daily[df_daily['location_id'] == selected_id]

            if not df_daily.empty:
                fig_daily = px.bar(
                    df_daily, x='date', y='avg_temp_c', 
                    color='location_id' if not selected_id else None,
                    title="Avg Daily Temp"
                )
                st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info(f"No daily data for Station {selected_id}.")
        else:
            st.info("Daily Summary table is empty (Gold Layer not ready).")
            
    with col_b:
        st.subheader("Weekly Summary")
        df_weekly = load_parquet("gold", "weekly_summary")
        
        if not df_weekly.empty:
            if selected_id:
                df_weekly = df_weekly[df_weekly['location_id'] == selected_id]
                
            if not df_weekly.empty:
                st.dataframe(df_weekly, use_container_width=True)
                
                fig_rain = px.scatter(
                    df_weekly, x='week_start', y='total_precip_mm',
                    size='max_wind_gust_kmh', color='location_id' if not selected_id else None,
                    title="Rain vs Wind Intensity"
                )
                st.plotly_chart(fig_rain, use_container_width=True)
            else:
                st.info("No data for this station.")