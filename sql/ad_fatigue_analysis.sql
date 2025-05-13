-- This query calculates ad fatigue by tracking and ranking how many times
-- a specific ad (ad_creative) is seen by a user (entity_proxy_id) before they make a purchase.

-- CTE to create a unique identifier (entity_proxy_id) for each distinct individual.
-- consolidates various identifiers (household, device, user, cookie) from the sim_id_mapping table.
WITH entity_map AS (
    SELECT
        simulated_household_id_linear,
        simulated_device_id_A,
        simulated_user_id_A,
        simulated_visitor_cookie_id,
        -- Concatenate all available IDs to form a unique signature for the row.
        -- Using COALESCE to handle NULLs and ensure a consistent string format.
        -- The separator '|' is chosen to be unlikely to appear in the IDs themselves.
        COALESCE(simulated_household_id_linear, 'null_hid') || '|' ||
        COALESCE(simulated_device_id_A,      'null_did_A') || '|' ||
        COALESCE(simulated_user_id_A,         'null_uid_A') || '|' ||
        COALESCE(simulated_visitor_cookie_id, 'null_cid') AS entity_proxy_id
    FROM
        sim_id_mapping
),

-- CTE to gather all ad exposures from Linear TV and Streaming App A,
-- linking them to the unified entity_proxy_id.
all_exposures AS (
    -- Linear TV ad exposures
    SELECT
        em.entity_proxy_id,
        linear.timestamp_utc AS ad_timestamp,
        linear.creative_name AS ad_creative,
        'Linear TV' AS ad_platform,
        linear.linear_airing_id AS original_ad_id -- Used for deduplication/tie-breaking
    FROM
        sim_linear_ad_log linear
    JOIN
        entity_map em ON linear.simulated_household_id_linear = em.simulated_household_id_linear
    WHERE
        linear.creative_name IS NOT NULL

    UNION ALL

    -- Streaming App A ad exposures, linked via device_id_A
    SELECT
        em.entity_proxy_id,
        stream.timestamp_app_A AS ad_timestamp,
        stream.creative_id_A AS ad_creative,
        'Streaming App A' AS ad_platform,
        stream.streaming_ad_id_A AS original_ad_id
    FROM
        sim_streaming_ad_log_A stream
    JOIN
        entity_map em ON stream.simulated_device_id_A = em.simulated_device_id_A

    UNION ALL

    -- Streaming App A ad exposures, linked via user_id_A
    -- This allows an ad to be associated with an entity if either its device or user ID matches.
    SELECT
        em.entity_proxy_id,
        stream.timestamp_app_A AS ad_timestamp,
        stream.creative_id_A AS ad_creative,
        'Streaming App A' AS ad_platform,
        stream.streaming_ad_id_A AS original_ad_id
    FROM
        sim_streaming_ad_log_A stream
    JOIN
        entity_map em ON stream.simulated_user_id_A = em.simulated_user_id_A
),

-- CTE to deduplicate ad exposures.
-- A single streaming ad might link to the same entity_proxy_id if both device_id and user_id are not null
unique_exposures AS (
    SELECT DISTINCT
        entity_proxy_id,
        ad_timestamp,
        ad_creative,
        ad_platform,
        original_ad_id
    FROM
        all_exposures
),

-- CTE to rank ad exposures for each entity and creative.
-- The rank indicates the chronological order of impressions for a given creative for a specific entity.
ranked_impressions AS (
    SELECT
        ue.entity_proxy_id,
        ue.ad_timestamp,
        ue.ad_creative,
        ue.ad_platform,
        ue.original_ad_id, -- Kept for reference and tie-breaking
        ROW_NUMBER() OVER (
            PARTITION BY ue.entity_proxy_id, ue.ad_creative
            ORDER BY ue.ad_timestamp, ue.original_ad_id -- original_ad_id as additional parameter if timestamps clash
        ) AS impression_rank_for_creative
    FROM
        unique_exposures ue
),

-- CTE to link purchase data to the entity_proxy_id via its visitor cookie ID.
purchases_mapped_to_entity AS (
    SELECT DISTINCT
        p.purchase_id,
        p.purchase_timestamp,
        p.purchase_value,
        em.entity_proxy_id
    FROM
        sim_purchases p
    JOIN
        entity_map em ON p.simulated_visitor_cookie_id = em.simulated_visitor_cookie_id
)

-- Final aggregation to calculate ad fatigue metrics, including
-- total exposures, total purchases, total value, and conversion rate, at each impression rank for every creative and ad_platform.
SELECT
    ri.ad_creative,
    ri.ad_platform,
    ri.impression_rank_for_creative,
    COUNT(ri.original_ad_id) AS total_exposures_at_rank,
    COUNT(p_me.purchase_id) AS total_purchases_linked_to_rank,
    COALESCE(SUM(p_me.purchase_value), 0) AS total_value_linked_to_rank,
    CASE
        WHEN COUNT(ri.original_ad_id) > 0 THEN
            CAST(COUNT(p_me.purchase_id) AS REAL) / COUNT(ri.original_ad_id) -- casting is necessary to force floating-point division
        ELSE 0
    END AS conversion_rate_at_rank
FROM
    ranked_impressions ri
LEFT JOIN
    purchases_mapped_to_entity p_me
    ON ri.entity_proxy_id = p_me.entity_proxy_id
    AND p_me.purchase_timestamp > ri.ad_timestamp -- Purchase must occur after the ad exposure
    AND p_me.purchase_timestamp <= ri.ad_timestamp + INTERVAL '30 days' -- 7-day attribution window for purchase
GROUP BY
    ri.ad_creative,
    ri.ad_platform,
    ri.impression_rank_for_creative
ORDER BY
    ri.ad_creative,
    ri.ad_platform,
    ri.impression_rank_for_creative;