import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Amazon Product Dashboard",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    df = pd.read_csv("amazon.csv")

    # --------------------------------------------------------
    # Clean price variables
    # --------------------------------------------------------

    df["discounted_price"] = (
        df["discounted_price"]
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    df["actual_price"] = (
        df["actual_price"]
        .astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    # --------------------------------------------------------
    # Clean discount percentage
    # --------------------------------------------------------

    df["discount_percentage"] = (
        df["discount_percentage"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .astype(float) / 100
    )

    # --------------------------------------------------------
    # Clean rating
    # --------------------------------------------------------

    # Replace invalid "|" with NaN
    df["rating"] = df["rating"].replace("|", np.nan)

    # Convert to numeric
    df["rating"] = pd.to_numeric(
        df["rating"],
        errors="coerce"
    )

    # Fill invalid rating with median
    df["rating"] = df["rating"].fillna(
        df["rating"].median()
    )

    # --------------------------------------------------------
    # Clean rating count
    # --------------------------------------------------------

    df["rating_count"] = pd.to_numeric(
        df["rating_count"]
        .astype(str)
        .str.replace(",", "", regex=False),
        errors="coerce"
    )

    # Impute missing rating_count using median
    # within the corresponding rating group
    df["rating_count"] = (
        df.groupby("rating")["rating_count"]
        .transform(
            lambda x: x.fillna(x.median())
        )
    )

    # --------------------------------------------------------
    # Remove URL columns
    # --------------------------------------------------------

    df = df.drop(
        columns=["img_link", "product_link"],
        errors="ignore"
    )

    # --------------------------------------------------------
    # Remove exact duplicate rows
    # --------------------------------------------------------

    df = df.drop_duplicates()

    # --------------------------------------------------------
    # Category features
    # --------------------------------------------------------

    df["main_category"] = (
        df["category"]
        .astype(str)
        .str.split("|")
        .str[0]
    )

    df["sub_category"] = (
        df["category"]
        .astype(str)
        .str.split("|")
        .str[-1]
    )

    # --------------------------------------------------------
    # Additional dashboard features
    # --------------------------------------------------------

    df["discount_amount"] = (
        df["actual_price"] -
        df["discounted_price"]
    )

    df["log_rating_count"] = np.log1p(
        df["rating_count"]
    )

    df["log_actual_price"] = np.log1p(
        df["actual_price"]
    )

    return df


df = load_data()


# ============================================================
# TITLE
# ============================================================

st.title("📊 Amazon Product Dashboard")

st.markdown(
    """
    This interactive dashboard provides an overview of Amazon
    products based on price, discount, ratings and popularity.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Dashboard Filters")

categories = sorted(
    df["main_category"].dropna().unique()
)

selected_category = st.sidebar.selectbox(
    "Select Product Category",
    ["All Categories"] + categories
)


# ============================================================
# FILTER DATA
# ============================================================

if selected_category == "All Categories":

    filtered_df = df.copy()

else:

    filtered_df = df[
        df["main_category"] == selected_category
    ].copy()


# ============================================================
# KPI CALCULATIONS
# ============================================================

number_products = len(filtered_df)

median_price = filtered_df["actual_price"].median()

median_discount = (
    filtered_df["discount_percentage"].median() * 100
)

mean_rating = filtered_df["rating"].mean()

total_rating_count = filtered_df["rating_count"].sum()


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Number of Products",
        f"{number_products:,}"
    )

with col2:
    st.metric(
        "Median Actual Price",
        f"₹{median_price:,.0f}"
    )

with col3:
    st.metric(
        "Median Discount",
        f"{median_discount:.1f}%"
    )

with col4:
    st.metric(
        "Mean Rating",
        f"{mean_rating:.2f}"
    )


st.divider()


# ============================================================
# CATEGORY SUMMARY
# ============================================================

category_summary = (
    df.groupby("main_category")
    .agg(
        number_of_products=("product_id", "count"),
        median_actual_price=("actual_price", "median"),
        median_discount=("discount_percentage", "median"),
        mean_rating=("rating", "mean"),
        total_rating_count=("rating_count", "sum")
    )
    .reset_index()
)


# ============================================================
# CHART 1 — PRODUCTS BY CATEGORY
# ============================================================

st.subheader("Product Distribution by Category")

fig_products = px.bar(
    category_summary.sort_values(
        "number_of_products",
        ascending=True
    ),
    x="number_of_products",
    y="main_category",
    orientation="h",
    title="Number of Products by Category",
    labels={
        "number_of_products": "Number of Products",
        "main_category": "Category"
    }
)

fig_products.update_layout(
    height=500
)

st.plotly_chart(
    fig_products,
    use_container_width=True
)


# ============================================================
# TWO-COLUMN CHART SECTION
# ============================================================

col1, col2 = st.columns(2)


# ============================================================
# CHART 2 — MEDIAN PRICE
# ============================================================

with col1:

    st.subheader("Median Actual Price")

    fig_price = px.bar(
        category_summary.sort_values(
            "median_actual_price",
            ascending=True
        ),
        x="median_actual_price",
        y="main_category",
        orientation="h",
        title="Median Actual Price by Category",
        labels={
            "median_actual_price": "Median Price (₹)",
            "main_category": "Category"
        }
    )

    st.plotly_chart(
        fig_price,
        use_container_width=True
    )


# ============================================================
# CHART 3 — MEDIAN DISCOUNT
# ============================================================

with col2:

    st.subheader("Median Discount")

    discount_plot = category_summary.copy()

    discount_plot["median_discount_pct"] = (
        discount_plot["median_discount"] * 100
    )

    fig_discount = px.bar(
        discount_plot.sort_values(
            "median_discount_pct",
            ascending=True
        ),
        x="median_discount_pct",
        y="main_category",
        orientation="h",
        title="Median Discount by Category",
        labels={
            "median_discount_pct": "Median Discount (%)",
            "main_category": "Category"
        }
    )

    st.plotly_chart(
        fig_discount,
        use_container_width=True
    )


# ============================================================
# CHART 4 — RATING BY CATEGORY
# ============================================================

st.subheader("Average Rating by Category")

fig_rating = px.bar(
    category_summary.sort_values(
        "mean_rating",
        ascending=True
    ),
    x="mean_rating",
    y="main_category",
    orientation="h",
    title="Mean Rating by Category",
    labels={
        "mean_rating": "Mean Rating",
        "main_category": "Category"
    }
)

fig_rating.update_xaxes(
    range=[0, 5]
)

st.plotly_chart(
    fig_rating,
    use_container_width=True
)


# ============================================================
# CHART 5 — PRICE VS POPULARITY
# ============================================================

st.subheader("Price vs Product Popularity")

fig_scatter = px.scatter(
    filtered_df,
    x="actual_price",
    y="rating_count",
    color="main_category",
    hover_data=[
        "product_name",
        "rating",
        "discount_percentage"
    ],
    log_x=True,
    log_y=True,
    title="Actual Price vs Rating Count",
    labels={
        "actual_price": "Actual Price (₹)",
        "rating_count": "Rating Count"
    }
)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)


# ============================================================
# SELECTED CATEGORY DETAILS
# ============================================================

if selected_category != "All Categories":

    st.subheader(
        f"Details: {selected_category}"
    )

    selected_summary = category_summary[
        category_summary["main_category"]
        == selected_category
    ].copy()

    selected_summary["median_discount"] *= 100

    selected_summary = selected_summary.rename(
        columns={
            "main_category": "Category",
            "number_of_products": "Products",
            "median_actual_price": "Median Price (₹)",
            "median_discount": "Median Discount (%)",
            "mean_rating": "Mean Rating",
            "total_rating_count": "Total Rating Count"
        }
    )

    st.dataframe(
        selected_summary,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Amazon Product Analysis Dashboard | Pine Labs Assignment"
)