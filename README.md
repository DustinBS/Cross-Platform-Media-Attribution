# Synthetic Cross-Platform Media Measurement Dataset

This repository contains a synthetic dataset designed to simulate the common data challenges encountered in cross-platform media measurement and advertising attribution. The simulated challenges are primarily **identity resolution & mapping**, **cross-platform data integration**, **data quality issues**, and **timestamp reconciliation**.

## Motivation

In advertising technology and media measurement, data can comes from numerous disparate sources, including linear TV logs, various streaming platforms, website analytics, CRM systems, etc. Linking data points across these sources to understand a user's journey and attribute conversions is a significant challenge. In this dataset, there are inconsistent identifiers, varying data granularities, data quality issues, and complex identity resolution processes.

This synthetic dataset is not intended to be a statistically accurate reflection of real-world data volumes or distributions but serves as a playground to approach these challenges in a manageable format.

## How to Use This Repository

To use this dataset for your project:

1.  **Clone the repository:**
    ```Powershell
    git clone https://github.com/DustinBS/TV-and-Streaming-Advertisement-Conversion-Patterns
    cd path/to/TV-and-Streaming-Advertisement-Conversion-Patterns
    ```
2.  **Install required Python dependencies:**
    ```Powershell
    pip install -r requirements.txt
    ```
3.  **Generate the synthetic dataset:**
    ```Powershell
    python generate_synthetic_data.py
    ```
    The script will create a `data/` subdirectory and save the five CSV files (`sim_id_mapping.csv`, `sim_linear_ad_log.csv`, `sim_streaming_ad_log_A.csv`, `sim_website_visits.csv`, `sim_purchases.csv`) within it.

## Statistical Distributions Used in Data Generation

Here are the primary distributions used: **Bernoulli Distribution** in (ID mapping rates in `sim_id_mapping.csv`), **Uniform Distribution** in (timestamps across logs/visits, purchase values in `sim_purchases.csv`), **Categorical Distribution** in (creative names in `sim_linear_ad_log.csv`), **Discrete Uniform Distribution** in (selecting IDs for log/visit entries, channel/creative IDs, impression counts, entry URLs, purchase timestamp deltas), and **Sampling** in (introducing duplicates in `sim_streaming_ad_log_A.csv`, selecting purchases in `sim_purchases.csv`).

## File Contents (Columns)

Here's a brief overview of the columns in each file:

**`sim_id_mapping.csv`**
* `simulated_household_id_linear`: ID used in linear data (can be null).
* `simulated_device_id_A`: Device ID used in Streaming App A data (can be null).
* `simulated_user_id_A`: User ID used in Streaming App A data (can be null).
* `simulated_visitor_cookie_id`: Cookie ID used in website data (can be null).

**`sim_linear_ad_log.csv`**
* `linear_airing_id`: Unique identifier for the ad airing event.
* `timestamp_utc`: Timestamp of the ad airing (UTC).
* `linear_channel`: Simulated TV channel.
* `creative_name`: Name of the ad creative (can be null).
* `simulated_household_id_linear`: Household ID exposed to the ad.
* `simulated_impressions`: Number of impressions (typically 1 per household airing).

**`sim_streaming_ad_log_A.csv`**
* `streaming_ad_id_A`: Unique identifier for the streaming ad impression event.
* `timestamp_app_A`: Timestamp of the impression (simulated as UTC).
* `streaming_platform`: Name of the streaming platform ('StreamingApp_A').
* `creative_id_A`: ID of the ad creative on this platform.
* `simulated_device_id_A`: Device ID associated with the impression.
* `simulated_user_id_A`: User ID associated with the impression.
* `simulated_impressions_count`: Number of impressions counted for this log entry (can be > 1).

**`sim_website_visits.csv`**
* `visit_id`: Unique identifier for the website visit.
* `visit_timestamp`: Timestamp of the visit.
* `entry_url`: The URL the user entered the site on.
* `simulated_visitor_cookie_id`: Cookie ID associated with the visit.

**`sim_purchases.csv`**
* `purchase_id`: Unique identifier for the purchase event.
* `purchase_timestamp`: Timestamp of the purchase.
* `purchase_value`: Simulated monetary value of the purchase.
* `simulated_visitor_cookie_id`: Cookie ID associated with the purchase.

