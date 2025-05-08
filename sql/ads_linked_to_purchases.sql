-- This query prepares data for a time-decay attribution model.
-- It calculates the sum of time-decayed credits from Linear TV and Streaming App A ads
-- for each purchase.

-- CTE to deterministically match purchases to various user identifiers via the mapping table
-- (purchases with missing cookies are excluded).
WITH PurchaseToUserMapping AS (
    SELECT
        p.purchase_id,
        p.purchase_timestamp,
        p.purchase_value,
        p.simulated_visitor_cookie_id AS purchase_cookie_id,
        map.simulated_household_id_linear,
        map.simulated_device_id_A,
        map.simulated_user_id_A
    FROM sim_purchases p
    JOIN sim_id_mapping map ON p.simulated_visitor_cookie_id = map.simulated_visitor_cookie_id
),

-- CTE to gather purchases with ad exposures within a lookback window of 30 days
-- (purchases with no ad exposure are excluded).
AdExposures AS (
    -- We will query linear impressions and streaming impressison separately to avoid fan-out from many-to-many joins.
    SELECT
        p_map.purchase_id,
        p_map.purchase_timestamp,
        linear.linear_airing_id AS original_ad_id,
        linear.timestamp_utc AS ad_timestamp,
        linear.creative_name AS ad_creative,
        'Linear TV' AS ad_platform, -- Categorical variable so we can differentiate with streaming ads
        linear.simulated_impressions as ad_impression_value
    FROM PurchaseToUserMapping p_map
    JOIN sim_linear_ad_log linear ON p_map.simulated_household_id_linear = linear.simulated_household_id_linear
    WHERE linear.timestamp_utc < p_map.purchase_timestamp -- only ads happening before a purchase are relevant
        AND linear.timestamp_utc >= p_map.purchase_timestamp - INTERVAL '30 days' -- lookback window

    UNION ALL
    -- Streaming App A Ad Exposures
    SELECT
        p_map.purchase_id,
        p_map.purchase_timestamp,
        streaming.streaming_ad_id_A AS original_ad_id,
        streaming.timestamp_app_A AS ad_timestamp,
        streaming.creative_id_A AS ad_creative,
        'Streaming App A' AS ad_platform,
        streaming.simulated_impressions_count AS ad_impression_value
    FROM PurchaseToUserMapping p_map
    JOIN sim_streaming_ad_log_A streaming
        ON (p_map.simulated_device_id_A = streaming.simulated_device_id_A)
        OR (p_map.simulated_user_id_A = streaming.simulated_user_id_A)
    WHERE streaming.timestamp_app_A < p_map.purchase_timestamp
        AND streaming.timestamp_app_A >= p_map.purchase_timestamp - INTERVAL '30 days'
),

-- CTE deduplicate rows.
UniqueAdExposuresPerPurchase AS (
    SELECT DISTINCT * FROM AdExposures
),

-- CTE to calculate the time-decayed credit for each unique ad exposure
DecayedAttribution AS (
    SELECT
        unique_ads.purchase_id,
        unique_ads.purchase_timestamp,
        unique_ads.ad_timestamp,
        unique_ads.ad_creative,
        unique_ads.ad_platform,
        unique_ads.ad_impression_value,
        -- Calculate time difference in days
        EXTRACT(EPOCH FROM (unique_ads.purchase_timestamp - unique_ads.ad_timestamp)) / (24.0*60.0*60.0) AS time_diff_days,
        -- Apply exponential decay (half-life model) so 
        -- credit = start * (0.5 ^ (time_diff_days / half_life_period_days))
        -- using a 7-day half-life: an ad's influence halves every 7 days.
        unique_ads.ad_impression_value * POWER(0.5, (EXTRACT(EPOCH FROM (unique_ads.purchase_timestamp - unique_ads.ad_timestamp)) / (24.0*60.0*60.0)) / 7.0) AS decayed_credit
    FROM UniqueAdExposuresPerPurchase unique_ads
)

-- aggregate the results (decayed credits for each purchase by platform).
SELECT
    p.purchase_id,
    p.purchase_value,
    -- handle purchases with no ad exposure (at least within the lookback window)
    COALESCE(SUM(CASE WHEN attribution.ad_platform = 'Linear TV' THEN attribution.decayed_credit ELSE 0 END), 0) AS total_decayed_linear_tv_credit,
    COALESCE(SUM(CASE WHEN attribution.ad_platform = 'Streaming App A' THEN attribution.decayed_credit ELSE 0 END), 0) AS total_decayed_streaming_app_a_credit
FROM sim_purchases p
LEFT JOIN DecayedAttribution attribution ON p.purchase_id = attribution.purchase_id
WHERE p.purchase_value > 0 -- we're interested in profitable transactions for this analysis
GROUP BY p.purchase_id, p.purchase_value
ORDER BY p.purchase_id;