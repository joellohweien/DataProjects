
# Enhancing Risk Assessment in Auto Insurance through Exploratory Data Analysis and Advanced Analytics

## Project Overview

### Introduction
This project undertakes a comprehensive Exploratory Data Analysis (EDA) on an auto insurance claims dataset provided by Porto Seguro, aiming to refine predictive models for assessing risk. Our analysis directly impacts the accuracy of insurance pricing, affecting company profitability and customer satisfaction.

### Objectives
- **Deep Dive into Data**: Understand the complexities within the dataset, uncovering hidden patterns and relationships.
- **Tackle Data Imbalance**: Address the challenge presented by the underrepresentation of claims within the data.
- **Feature Engineering and Selection**: Identify and engineer predictive features for future modeling.
- **Risk Identification**: Highlight key risk factors for insurance claims to aid in mitigation and model refinement.

## Data Clean-Up Decisions

After a thorough review, certain variables with high levels of missing data were removed to ensure the integrity and reliability of the analysis. A balanced approach to imputation was adopted to maintain statistical soundness without introducing bias:

- **Variables Removed**: 'ps_car_03_cat' and 'ps_car_05_cat' due to a missing data proportion of >=45%.
- **Imputation Strategy**: Median imputation for numerical variables and mode imputation for categorical variables.

## Advanced Analytics

The project delves into the correlations between categorical variables using Cramer's V, a measure derived from the Chi-square test. This analysis helps us understand the strength of association between pairs of variables, informing feature selection and potential predictive power.

### Key Findings
- A few variable pairs demonstrated a strong association, indicated by a Cramer's V score higher than 0.5. These pairs were scrutinized for their distribution and potential multicollinearity.

## Visualization Insights

- **Correlation Heatmap**: Offered a first glance at the correlation dynamics, guiding dimensionality reduction and feature engineering.
- **Violin Plots**: Provided a more nuanced view of distributions, especially useful for binary categorical data and identifying outliers.

## Conclusions

The EDA conducted provides actionable insights, preparing the data for the development of more accurate predictive models. The steps taken in data cleaning and analysis reflect a strategic and data-driven approach, aligning with the company's standards for excellence and regulatory compliance.

---

*This analysis is part of a larger project aimed at creating a predictive model, using the Porto Seguro automobile dataset. The findings here will inform the direction of future model development.*
