# Product Requirements Document (PRD)
**Project:** AI-Powered Category Management System
**Domain:** Pharmacy Retail Chain (43 Stores)
**Document Version:** 1.0 (Production-Ready)

---

## 1. Executive Summary
This document outlines the architecture, data models, and machine learning strategies for a full-scale AI-powered Category Management System tailored for a 43-store pharmacy chain. The system transforms raw, localized flat files (Excel/CSV) into actionable decision intelligence. By combining advanced machine learning (K-Means clustering, XGBoost forecasting) with a deterministic business rules engine, the platform provides granular, store-by-store, SKU-by-SKU recommendations to optimize assortment, minimize expiry waste, maximize Gross Margin Return on Investment (GMROI), and automate next-best-action decisions.

## 2. Business Problem
Current retail operations rely on aggregate heuristics rather than localized, data-driven insights. This leads to four critical inefficiencies:
1.  **Capital Tie-up & Expiry Waste:** Overstocking slow-moving SKUs leads to tied-up working capital and high expiry loss, particularly in Medicine and Wellness divisions.
2.  **Opportunity Loss:** Fast-moving items experience stockouts due to a lack of predictive demand forecasting.
3.  **Homogeneous Assortment:** Applying a uniform assortment strategy across 43 diverse stores (e.g., hospital-adjacent vs. suburban retail) ignores local demographic and behavioral nuances.
4.  **Manual Analysis Paralysis:** Category managers lack the bandwidth to analyze thousands of SKUs across 43 stores individually.

## 3. Data Architecture
The architecture follows a modular "Local-to-Cloud" paradigm. It treats local directories as a data lake, implements an in-memory feature store using Pandas, and outputs to flat files and Streamlit, ensuring seamless future migration to a cloud data warehouse (e.g., Snowflake/BigQuery).

* **Bronze Layer (Ingestion):** Raw CSV/Excel files are validated against strict data schemas.
* **Silver Layer (Processing):** Cleaned, merged, and imputed datasets. 
* **Gold Layer (Feature Store):** Engineered features ready for ML inference (e.g., historical lag features, rolling averages).
* **Platinum Layer (Inference & Output):** Joined ML predictions and business rules mapped to final actionable CSVs and Dashboards.

## 4. Data Model (Tables & Schemas)

| Data Entity | Columns | Description / Primary Key |
| :--- | :--- | :--- |
| **sales_transactions** | `transaction_id`, `store_id`, `sku`, `date`, `qty`, `sales_value`, `discount_applied` | Fact table tracking daily SKU-level sales per store. |
| **inventory_snapshot** | `store_id`, `sku`, `stock_on_hand`, `expiry_date`, `batch_id`, `snapshot_date` | Daily/Weekly snapshot of SOH and expiry timelines. |
| **product_master** | `sku` (PK), `division`, `department`, `category`, `subcategory`, `segment`, `cost`, `price`, `supplier_id` | Dimension table defining the hierarchical taxonomy of items. |
| **store_master** | `store_id` (PK), `location_type`, `region`, `sqm`, `opening_date` | Dimension table of the 43 stores and their static attributes. |
| **purchase_data** | `po_id`, `sku`, `supplier_id`, `order_date`, `delivery_date`, `lead_time_days`, `unit_cost` | Tracks supplier performance and replenishment lead times. |
| **calendar** | `date` (PK), `is_holiday`, `season`, `is_weekend`, `promo_event_id` | Dimension table for temporal and seasonal features. |

## 5. Feature Engineering
A local Feature Store module will calculate these metrics dynamically before model training:

* **Velocity Metrics:** 7-day, 14-day, 30-day, and 90-day rolling sales volumes.
* **Profitability Metrics:** SKU-Store Margin %, $GMROI = \frac{Gross Profit}{Average Inventory Cost}$.
* **Temporal Features:** Month, day of week, days until a major holiday.
* **Risk Metrics:** `days_to_expiry`, `expiry_risk_score` (Ratio of SOH to 30-day velocity against days to expiry).
* **Cross-Dimensional Features:** `store_sku_deviation` (How a SKU's velocity in Store X deviates from the 43-store mean for that SKU).

## 6. ML Models Design
The system employs a dual-engine ML approach, separating unsupervised clustering (for segmentation) from supervised learning (for forecasting).

* **Scaling:** Due to retail data outliers (e.g., massive spikes from bulk buys), we utilize `RobustScaler` prior to clustering. The formula is $x_{scaled} = \frac{x - Q_1(x)}{Q_3(x) - Q_1(x)}$, which centers around the median and scales by the Interquartile Range.
* **Clustering Pipeline:** K-Means algorithm optimized via the Elbow Method for $k$ selection, validated by the Silhouette Score.
* **Forecasting Pipeline:** XGBoost Regressor (Tree-based) is the primary model. It natively handles non-linear retail patterns, complex feature interactions, and tabular data better than ARIMA. Facebook Prophet is maintained as a fallback for highly seasonal, long-history categories (e.g., Sunscreen in Wellness).

## 7. Clustering Strategy (Store + SKU)

### A. Store Intelligence (Store Clustering)
Groups the 43 stores to optimize localized strategies.
* **Features:** % Revenue by Division, Average Basket Size, Total SQM, Inventory Turnover Rate, Location Type.
* **Target Clusters:**
    * *Hospital-Adjacent:* High volume in Medicine, low volume in Beauty.
    * *Premium Retail:* High Beauty/Personal Care penetration, high basket size.
    * *Neighborhood Growth:* High Mom & Baby, balanced Medicine.
    * *Low Efficiency:* High SOH, low velocity across categories.

### B. Category Intelligence (SKU Clustering within Categories)
Groups SKUs based on behavioral economics within their specific Subcategory/Segment.
* **Features:** Sales Velocity, Margin %, Volatility (Coefficient of Variation), Stock Cover Days.
* **Target Clusters:**
    * *Traffic Builders:* High volume, low margin (e.g., basic painkillers).
    * *Margin Generators:* Low volume, high margin (e.g., premium skincare).
    * *Seasonal Spikes:* High volatility tied to calendar events.
    * *Dead/Toxic Stock:* Near zero volume, high SOH.

### C. Cross-Dimensional Intelligence
Analyzes the intersection of Store Clusters and SKU Clusters. Example: A "Traffic Builder" SKU in a "Premium Retail" store might behave as a "Margin Generator" if price elasticity permits, triggering store-specific assortment localization.

## 8. Forecasting Strategy
* **Target Variable:** `qty_sold` at the $T+1$ to $T+14$ day horizon (per SKU per Store).
* **Features:** Rolling means, lag features (sales 7 days ago, 30 days ago), price changes, holiday flags, and lead time.
* **Output:** Generates `predicted_demand`.
* **Risk Thresholds:** 
    * `stockout_risk`: If $(SOH + Inbound) < predicted\_demand$.
    * `overstock_risk`: If $SOH > (predicted\_demand \times 3)$.

## 9. Business Rules Engine
A deterministic Python module that overrides or formats ML outputs into strict retail guidelines.

| Trigger Condition (ML + Data) | Business Rule Action |
| :--- | :--- |
| `days_to_expiry` < 60 AND `SOH` > `30d_velocity` | Flag for aggressive targeted discount (e.g., 40% off). |
| SKU Cluster = "Traffic Builder" AND `SOH` < `lead_time_demand` | Trigger IMMEDIATE AUTO-REORDER. |
| SKU Cluster = "Dead Stock" AND `GMROI` < 0.5 | Flag for DELISTING and vendor return. |
| Store Cluster = "Hospital" AND Category = "Premium Beauty" | Restrict assortment to Top 10% Fast Movers only. |

## 10. Decision Intelligence Layer
The output is synthesized into a "Next Best Action" (NBA) master table for Category Managers.

* **Entity:** `Store_ID` + `SKU`
* **Action Categories:** `[REORDER, PROMOTE, DISCOUNT, DELIST, HOLD, TRANSFER]`
* **Context:** Human-readable explanation (e.g., *"Transfer 50 units from Store A to Store B: Store A has 90 days cover, Store B stocks out in 3 days."*)
* **Opportunity Detection:** Identifies missing SKUs. If Store A belongs to Cluster 1, and 90% of Cluster 1 stores successfully sell SKU X, the system flags SKU X as a "Missing Opportunity" for Store A.

## 11. KPI Framework

* **Enterprise Level:** Total Revenue Growth, Global GMROI, Total Working Capital Efficiency.
* **Store Level:** Store Inventory Turnover, Store Sell-through Rate %, Out-of-Stock (OOS) %.
* **Category Level:** Category Contribution % (to total sales), Category GMROI, Subcategory Growth YoY.
* **SKU Level:** SKU Velocity, Fill Rate, Expiry Loss %, Stock Cover Days.

## 12. System Architecture Diagram
```text
[Raw Flat Files: CSV/Excel] 
       │
       ▼
[Data Ingestion & Validation Layer] (Pandas, Pydantic)
       │
       ▼
[Feature Store Generation] ─── (Rolling averages, RFM, Lag features)
       │
       ├────────────────────────────────┐
       ▼                                ▼
[Unsupervised ML Pipeline]       [Supervised ML Pipeline]
(Scikit-Learn: K-Means)          (XGBoost / Prophet)
- Store Clustering               - 14-day Demand Forecasting
- SKU Clustering                 - Volatility Scoring
       │                                │
       └───────────────┬────────────────┘
                       ▼
          [Business Rules Engine]
     (Heuristics, Expiry Logic, GMROI Check)
                       │
                       ▼
        [Decision Intelligence Output]
         (Next Best Action per Store/SKU)
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
[CSV Extracts]   [Excel Reports]   [Streamlit Dashboard]