import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# --- Configuration ---
# Added SEED for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

NUM_BASE_INDIVIDUALS = 5000 # Represents the underlying pool of unique people/households
CAMPAIGN_START_DATE = datetime(2024, 10, 1)
CAMPAIGN_END_DATE = datetime(2024, 10, 31)
LINEAR_AIRINGS_PER_DAY = 100 # Average number of linear ad airings per day
STREAMING_IMPRESSIONS_PER_DAY = 500 # Average number of streaming impressions per day
WEBSITE_VISITS_PER_DAY = 300 # Average number of website visits per day
PURCHASE_RATE = 0.02 # Percentage of website visits that result in a purchase

# Simulate different levels of identity mapping completeness
LINEAR_MAPPING_RATE = 0.9 # % of individuals with a linear TV ID
STREAMING_DEVICE_MAPPING_RATE = 0.85 # % of individuals with a streaming device ID
STREAMING_USER_MAPPING_RATE = 0.7 # % of individuals with a streaming user ID (different from device)
WEBSITE_COOKIE_MAPPING_RATE = 0.6 # % of individuals with a website cookie ID

# Simulate some data quality issues
LINEAR_MISSING_CREATIVE_RATE = 0.05 # % of linear airings with missing creative name
STREAMING_DUPLICATE_RATE = 0.03 # % of streaming impressions that are duplicates

# Output directory for the generated CSVs. if you change this and use docker, update the docker-compose.yml
OUTPUT_DIR = 'data'

# --- Helper Functions ---
def generate_timestamps(start_date: datetime, end_date: datetime, num_timestamps: int) -> list[datetime]:
    """
    Generates a list of random datetime objects within a specified date range.

    Args:
        start_date (datetime): inclusive start date.
        end_date (datetime): inclusive end date.
        num_timestamps (int): the number of timestamps to generate.

    Returns:
        list[datetime]: A list containing the generated random datetime objects.
    """
    time_between_dates = end_date - start_date
    seconds_between_dates = time_between_dates.total_seconds()
    # Ensure seconds_between_dates is not negative or zero if dates are the same
    if seconds_between_dates <= 0 and num_timestamps > 0:
         if start_date == end_date: # Handle edge case where start and end are the same
             return [start_date] * num_timestamps
         # Should not happen with normal date ranges, but as a safeguard
         raise ValueError("End date must be after start date for generating multiple timestamps.")

    random_seconds = np.random.uniform(0, seconds_between_dates, num_timestamps)
    return [start_date + timedelta(seconds=s) for s in random_seconds]

def generate_ids(prefix: str, num: int) -> list[str]:
    """
    Generates a list of unique string identifiers with a given prefix.

    Args:
        prefix (str): The prefix for the IDs (e.g., "user", "event").
        num (int): The number of IDs to generate.

    Returns:
        list[str]: A list of unique string IDs.
    """
    return [f"{prefix}_{i:05d}" for i in range(num)]

# --- Main Generation Logic ---
if __name__ == "__main__":
    print(f"Generating synthetic dataset with SEED={SEED}...")

    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured output directory '{OUTPUT_DIR}' exists.")

    # --- 1. Generate sim_id_mapping.csv ---
    print("Generating sim_id_mapping.csv...")
    base_individuals = generate_ids("individual", NUM_BASE_INDIVIDUALS)

    mapping_data = []
    for individual in base_individuals:
        # Use random.random() for simple Bernoulli trial
        linear_id = individual if random.random() < LINEAR_MAPPING_RATE else None
        streaming_device_id = individual if random.random() < STREAMING_DEVICE_MAPPING_RATE else None
        streaming_user_id = individual if random.random() < STREAMING_USER_MAPPING_RATE else None
        website_cookie_id = individual if random.random() < WEBSITE_COOKIE_MAPPING_RATE else None

        # Ensure at least one ID exists for the individual to be included in logs
        # This slightly reduces the number of individuals in the mapping vs base_individuals
        if linear_id or streaming_device_id or streaming_user_id or website_cookie_id:
              mapping_data.append({
                'simulated_individual_base_id': individual, # Base ID for linking in this script, not in final CSV
                'simulated_household_id_linear': linear_id,
                'simulated_device_id_A': streaming_device_id,
                'simulated_user_id_A': streaming_user_id,
                'simulated_visitor_cookie_id': website_cookie_id
            })

    id_mapping_df = pd.DataFrame(mapping_data)
    id_mapping_df_to_save = id_mapping_df.drop(columns=['simulated_individual_base_id'])
    id_mapping_df_to_save.to_csv(os.path.join(OUTPUT_DIR, 'sim_id_mapping.csv'), index=False)
    print(f"Generated sim_id_mapping.csv with {len(id_mapping_df_to_save)} potential entities.")

    # --- 2. Generate sim_linear_ad_log.csv ---
    print("Generating sim_linear_ad_log.csv...")
    linear_ids_available = id_mapping_df.dropna(subset=['simulated_household_id_linear'])['simulated_household_id_linear'].tolist()
    num_linear_days = (CAMPAIGN_END_DATE - CAMPAIGN_START_DATE).days + 1 # Include end date
    num_linear_airings = int(num_linear_days * LINEAR_AIRINGS_PER_DAY)

    if not linear_ids_available:
        print("Warning: No linear IDs available in mapping. Is your LINEAR_MAPPING_RATE too low? Skipping linear log generation.")
        linear_log_df = pd.DataFrame() # Create empty df to avoid errors later
    else:
        linear_log_data = {
            'linear_airing_id': generate_ids("linear_airing", num_linear_airings),
            'timestamp_utc': generate_timestamps(CAMPAIGN_START_DATE, CAMPAIGN_END_DATE + timedelta(days=1), num_linear_airings), # Generate slightly past end date to match digital logs
            'linear_channel': np.random.choice([f'Channel_{i}' for i in range(1, 21)], num_linear_airings),
            # Use np.random.choice with p for weighted probability, including None
            'creative_name': np.random.choice([f'Creative_{i}' for i in range(1, 6)] + [None],
                                            num_linear_airings,
                                            p=[(1-LINEAR_MISSING_CREATIVE_RATE)/5]*5 + [LINEAR_MISSING_CREATIVE_RATE]),
            'simulated_household_id_linear': np.random.choice(linear_ids_available, num_linear_airings),
            'simulated_impressions': 1
        }
        linear_log_df = pd.DataFrame(linear_log_data)
        linear_log_df.to_csv(os.path.join(OUTPUT_DIR, 'sim_linear_ad_log.csv'), index=False)
        print(f"Generated sim_linear_ad_log.csv with {len(linear_log_df)} rows.")


    # --- 3. Generate sim_streaming_ad_log_A.csv ---
    print("Generating sim_streaming_ad_log_A.csv...")
    streaming_device_ids_available = id_mapping_df.dropna(subset=['simulated_device_id_A'])['simulated_device_id_A'].tolist()
    streaming_user_ids_available = id_mapping_df.dropna(subset=['simulated_user_id_A'])['simulated_user_id_A'].tolist()
    num_streaming_days = (CAMPAIGN_END_DATE - CAMPAIGN_START_DATE).days + 1 # Include end date
    num_streaming_impressions = int(num_streaming_days * STREAMING_IMPRESSIONS_PER_DAY)

    if not streaming_device_ids_available or not streaming_user_ids_available:
         print("Warning: Not enough streaming device or user IDs available in mapping. Try increasing STREAMING_DEVICE_MAPPING_RATE or STREAMING_USER_MAPPING_RATE. Skipping streaming log generation.")
         streaming_log_df = pd.DataFrame() # Create empty df to avoid errors later
    else:
        streaming_log_data = {
            'streaming_ad_id_A': generate_ids("streaming_ad_A", num_streaming_impressions),
            'timestamp_app_A': generate_timestamps(CAMPAIGN_START_DATE, CAMPAIGN_END_DATE + timedelta(days=1), num_streaming_impressions), # UTC for simplicity, in reality, there might be timezone differences
            'streaming_platform': 'StreamingApp_A',
            'creative_id_A': np.random.choice([f'CreativeID_A_{i}' for i in range(1, 8)], num_streaming_impressions),
            'simulated_device_id_A': np.random.choice(streaming_device_ids_available, num_streaming_impressions),
            'simulated_user_id_A': np.random.choice(streaming_user_ids_available, num_streaming_impressions),
            'simulated_impressions_count': np.random.randint(1, 4, num_streaming_impressions)
        }
        streaming_log_df = pd.DataFrame(streaming_log_data)

        # Introduce duplicates
        num_duplicates = int(len(streaming_log_df) * STREAMING_DUPLICATE_RATE)
        if num_duplicates > 0 and len(streaming_log_df) > 0:
            duplicate_rows = streaming_log_df.sample(num_duplicates, replace=True, random_state=SEED)
            streaming_log_df = pd.concat([streaming_log_df, duplicate_rows]).sample(frac=1, random_state=SEED).reset_index(drop=True)
            print(f"Added {num_duplicates} duplicates.")


        streaming_log_df.to_csv(os.path.join(OUTPUT_DIR, 'sim_streaming_ad_log_A.csv'), index=False)
        print(f"Generated sim_streaming_ad_log_A.csv with {len(streaming_log_df)} rows (including duplicates).")


    # --- 4. Generate sim_website_visits.csv ---
    print("Generating sim_website_visits.csv...")
    website_cookie_ids_available = id_mapping_df.dropna(subset=['simulated_visitor_cookie_id'])['simulated_visitor_cookie_id'].tolist()
    num_website_days = (CAMPAIGN_END_DATE - CAMPAIGN_START_DATE).days + 1
    num_website_visits = int(num_website_days * WEBSITE_VISITS_PER_DAY) # Visits happen during and shortly after campaign

    if not website_cookie_ids_available:
        print("Warning: No website cookie IDs available in mapping. Try increasing your WEBSITE_COOKIE_MAPPING_RATE. Skipping website visit generation.")
        website_visits_df = pd.DataFrame() # Create empty df to avoid errors later
    else:
        # Generate visit timestamps, biased towards occurring after campaign start
        # Allow visits slightly after campaign end, up to 7 days
        visit_timestamps = generate_timestamps(CAMPAIGN_START_DATE, CAMPAIGN_END_DATE + timedelta(days=7), num_website_visits)

        # product_page visits are later used to generate purchases
        website_visits_data = {
            'visit_id': generate_ids("visit", num_website_visits),
            'visit_timestamp': visit_timestamps,
            'entry_url': np.random.choice(['/homepage', '/product_page_A', '/product_page_B', '/about_us', '/blog'], num_website_visits),
            'simulated_visitor_cookie_id': np.random.choice(website_cookie_ids_available, num_website_visits)
        }
        website_visits_df = pd.DataFrame(website_visits_data)
        website_visits_df.to_csv(os.path.join(OUTPUT_DIR, 'sim_website_visits.csv'), index=False)
        print(f"Generated sim_website_visits.csv with {len(website_visits_df)} rows.")

    # --- 5. Generate sim_purchases.csv ---
    print("Generating sim_purchases.csv...")

    if website_visits_df.empty:
         print("Warning: No website visits generated. Try increasing your WEBSITE_VISITS_PER_DAY. Skipping purchase generation.")
         purchases_df = pd.DataFrame() # Create empty df to avoid errors
    else:
        # Select a subset of visits to product_page that could potentially lead to a purchase
        potential_purchase_visits = website_visits_df[
            website_visits_df['entry_url'].str.contains('product_page')
        ].copy()

        # Randomly select visits that result in a purchase
        num_potential_purchases = len(potential_purchase_visits)
        num_purchases = int(num_potential_purchases * PURCHASE_RATE)

        if num_purchases > 0 and num_potential_purchases > 0:
             purchase_visits = potential_purchase_visits.sample(num_purchases, replace=False, random_state=SEED).copy() # Use seed for reproducible sample
             # Generate purchase timestamps slightly after visit timestamps (5s to 5min)
             purchase_visits['purchase_timestamp'] = purchase_visits['visit_timestamp'] + pd.to_timedelta(np.random.randint(5, 60*5, num_purchases), unit='s')

             purchase_data = {
                 'purchase_id': generate_ids("purchase", num_purchases),
                 'purchase_timestamp': purchase_visits['purchase_timestamp'],
                 'purchase_value': np.random.uniform(10, 500, num_purchases).round(2),
                 'simulated_visitor_cookie_id': purchase_visits['simulated_visitor_cookie_id']
             }
             purchases_df = pd.DataFrame(purchase_data)
             purchases_df.to_csv(os.path.join(OUTPUT_DIR, 'sim_purchases.csv'), index=False)
             print(f"Generated sim_purchases.csv with {len(purchases_df)} rows.")
        else:
             print("No potential purchase visits or PURCHASE_RATE too low. No purchases generated.")
             purchases_df = pd.DataFrame() # Create empty df to avoid errors

    print("\nDataset generation complete.")
    print(f"Files created in the '{OUTPUT_DIR}' directory.")