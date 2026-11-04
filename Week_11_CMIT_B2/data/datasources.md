# Dataset Sources

## 1. RetailRocket
- Source: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset
- Purpose: User interactions and recommendations
- Data type: Real public data
- Transformations: Event cleaning, timestamp conversion
- Limitations: Approximately 4.5 months of interactions;
  anonymized item identifiers
- License: Verify the source's current terms before use

## 2. Olist
- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- Purpose: Orders, products, reviews
- Data type: Real anonymized Brazilian data
- Transformations: Join order items, orders, products and reviews
- Limitations: Not representative of Pakistan
- License: Verify current dataset license and restrictions

## 3. Store Item Demand Forecasting
- Source: https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data
- Purpose: Daily demand forecasting
- Data type: Historical sales data
- Transformations: Date parsing, calendar features,
  chronological train/validation/test split
- Limitations: Synthetic product metadata may be required
- License: Review competition rules

## 4. Pakistani Calendar
- Source: Document the calendar references used
- Purpose: Festival and promotional features
- Data type: Calendar-derived features
- Transformations: Create date flags and promotional windows

## 5. Synthetic UrduLish Reviews
- Source: Generated for this project
- Purpose: Test multilingual review processing
- Data type: Synthetic
- Transformations: Document generation method and labels

Start with RetailRocket + Olist + Store Item Demand Forecasting.These three sources give you the strongest foundation for the interaction, catalogue/review, and daily forecasting components. Add your Pakistani calendar and clearly labeled synthetic PKR catalogue attributes and UrduLish reviews.

That combination lets you demonstrate all three parts of the platform without claiming the source data represents actual Pakistani shoppers.
