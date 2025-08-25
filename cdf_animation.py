import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Set page config
st.set_page_config(
    page_title="Empirical CDF Animation",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Empirical CDF Evolution Timelapse (2010-2015)")
st.markdown("---")

# Sidebar controls
st.sidebar.header("🎛️ Animation Controls")
n_observations = st.sidebar.slider("Number of Observations", 100, 2000, 1000, 50)
animation_speed = st.sidebar.slider("Animation Speed (seconds per year)", 0.5, 3.0, 1.0, 0.1)
trend_strength = st.sidebar.slider("Trend Strength", 0.0, 2.0, 0.5, 0.1)
volatility = st.sidebar.slider("Volatility", 0.1, 2.0, 1.0, 0.1)

# Generate synthetic data that evolves over time
@st.cache_data
def generate_evolving_data(n_obs, trend_str, vol):
    np.random.seed(42)  # For reproducibility
    years = list(range(2010, 2016))
    data = {}

    # Base distribution parameters
    base_mean = 50
    base_std = 15

    for i, year in enumerate(years):
        # Add trend and some randomness over time
        year_mean = base_mean + trend_str * i + np.random.normal(0, 2)
        year_std = base_std * vol + np.random.uniform(-2, 2)

        # Generate data with some autocorrelation to previous year
        if i == 0:
            values = np.random.normal(year_mean, year_std, n_obs)
        else:
            # Add some persistence from previous year
            prev_values = data[years[i-1]]
            noise = np.random.normal(0, year_std, n_obs)
            values = 0.7 * prev_values + 0.3 * year_mean + noise

        data[year] = values

    return data, years

# Calculate empirical CDF
def empirical_cdf(data):
    sorted_data = np.sort(data)
    n = len(data)
    y = np.arange(1, n + 1) / n
    return sorted_data, y

# Generate data
data_dict, years = generate_evolving_data(n_observations, trend_strength, volatility)

# Create columns for layout
col1, col2 = st.columns([3, 1])

with col1:
    # Create placeholder for the animated plot
    plot_placeholder = st.empty()

with col2:
    st.subheader("📊 Data Summary")

    # Statistics table
    stats_data = []
    for year in years:
        values = data_dict[year]
        stats_data.append({
            'Year': year,
            'Mean': f"{np.mean(values):.2f}",
            'Std Dev': f"{np.std(values):.2f}",
            'Min': f"{np.min(values):.2f}",
            'Max': f"{np.max(values):.2f}"
        })

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)

# Animation controls
col_start, col_stop, col_download = st.columns(3)

with col_start:
    start_animation = st.button("▶️ Start Animation", type="primary")

with col_stop:
    stop_animation = st.button("⏹️ Stop Animation")

with col_download:
    # Prepare data for download
    download_data = pd.DataFrame(data_dict)
    csv_data = download_data.to_csv(index=False)
    st.download_button(
        label="💾 Download Data",
        data=csv_data,
        file_name="cdf_evolution_data.csv",
        mime="text/csv"
    )

# Animation logic
if start_animation:
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Calculate global x-axis limits for consistent scaling
    all_values = np.concatenate([data_dict[year] for year in years])
    x_min, x_max = np.min(all_values) - 5, np.max(all_values) + 5

    for i, year in enumerate(years):
        if stop_animation:
            break

        # Update progress
        progress = (i + 1) / len(years)
        progress_bar.progress(progress)
        status_text.text(f"Showing year: {year}")

        # Get data for current year
        current_data = data_dict[year]
        x_cdf, y_cdf = empirical_cdf(current_data)

        # Create the plot
        fig = go.Figure()

        # Add CDF line
        fig.add_trace(go.Scatter(
            x=x_cdf,
            y=y_cdf,
            mode='lines',
            name=f'Empirical CDF - {year}',
            line=dict(color='blue', width=3),
            hovertemplate='<b>Value:</b> %{x:.2f}<br><b>Cumulative Probability:</b> %{y:.3f}<extra></extra>'
        ))

        # Add markers at quartiles
        q25, q50, q75 = np.percentile(current_data, [25, 50, 75])
        fig.add_trace(go.Scatter(
            x=[q25, q50, q75],
            y=[0.25, 0.50, 0.75],
            mode='markers',
            name='Quartiles',
            marker=dict(color='red', size=10, symbol='diamond'),
            hovertemplate='<b>Quartile:</b> %{text}<br><b>Value:</b> %{x:.2f}<extra></extra>',
            text=['Q1 (25%)', 'Q2 (50%)', 'Q3 (75%)']
        ))

        # Update layout
        fig.update_layout(
            title=f'<b>Empirical CDF Evolution - Year {year}</b><br><span style="font-size:14px">Sample Size: {n_observations:,} observations</span>',
            xaxis_title='Value',
            yaxis_title='Cumulative Probability',
            xaxis=dict(range=[x_min, x_max]),
            yaxis=dict(range=[0, 1]),
            height=500,
            showlegend=True,
            hovermode='closest',
            template='plotly_white',
            font=dict(size=12)
        )

        # Add grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

        # Display the plot
        with plot_placeholder.container():
            st.plotly_chart(fig, use_container_width=True)

        # Wait for specified duration
        time.sleep(animation_speed)

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    st.success("🎉 Animation completed!")

# Add explanation
with st.expander("ℹ️ About This Visualization"):
    st.markdown("""
    This app demonstrates how an empirical Cumulative Distribution Function (CDF) evolves over time from 2010 to 2015.

    **Key Features:**
    - **Synthetic Data**: Generated with realistic trends and year-to-year correlation
    - **Empirical CDF**: Shows the probability that a randomly selected observation is ≤ a given value
    - **Quartile Markers**: Red diamonds mark the 25th, 50th, and 75th percentiles
    - **Interactive Controls**: Adjust sample size, animation speed, trend strength, and volatility

    **How to Use:**
    1. Adjust parameters in the sidebar
    2. Click "Start Animation" to see the CDF evolution
    3. Observe how the distribution shape changes over time
    4. Download the generated data for further analysis

    **Interpretation:**
    - Steeper curves = more concentrated data
    - Shifts right/left = changes in central tendency
    - Changes in curve shape = changes in distribution characteristics
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit and Plotly")
