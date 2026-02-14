import pandas as pd
import numpy as np

REFERENCE_RANGES = {
    "carbs": (45, 65),
    "protein": (10, 35),
    "fat": (20, 35)
}

WINDOW_OPTIONS = {
    "day": 1,
    "week": 7,
    "month": 30
}

def normalize_dish_name(dish):
    dish = dish.lower()
    keywords = [
        "roti", "chapati",
        "rice",
        "dal", "lentil",
        "rajma",
        "paneer",
        "curd", "yogurt",
        "tea", "coffee"
    ]
    for key in keywords:
        if key in dish:
            return key
    return dish

def find_best_match(dish, nutrition_dishes):
    for ref_dish in nutrition_dishes:
        if dish in ref_dish or ref_dish in dish:
            return ref_dish
    return None

def normalize_1_100(x, k=1.5):
    return 100 / (1 + np.exp(-k * (x - 1)))

def analyze_menu(menu_df, window="week"):
    """
    Analyze mess menu nutrition risk.

    menu_df columns:
    - date
    - dish
    - quantity_g
    """

    # ---- Load nutrition reference ----
    nutrition_df = pd.read_csv("Data/nutrition_reference_clean.csv")
    nutrition_df["dish"] = nutrition_df["dish"].str.strip().str.lower()

    # ---- Clean menu input ----
    menu_df = menu_df.copy()
    menu_df["dish"] = menu_df["dish"].str.strip().str.lower()

    # ---- Normalize dish names ----
    nutrition_df["norm_dish"] = nutrition_df["dish"].apply(normalize_dish_name)
    menu_df["norm_dish"] = menu_df["dish"].apply(normalize_dish_name)

    nutrition_dishes = nutrition_df["norm_dish"].tolist()

    menu_df["matched_dish"] = menu_df["norm_dish"].apply(
        lambda x: x if x in nutrition_dishes else find_best_match(x, nutrition_dishes)
    )

    merged_df = menu_df.merge(
        nutrition_df,
        left_on="matched_dish",
        right_on="norm_dish",
        how="left"
    ).dropna()

    if merged_df.empty:
        return {
            "risk_score": 0,
            "risk_level": "Unknown",
            "flags": ["No matched dishes"],
            "macro_pct": {},
            "deviation_score": 0,
            "explanation": "No dishes could be matched with nutrition reference data."
        }


    # ---- Scale nutrition by quantity ----
    for col in ["calories_kcal", "carbs_g", "protein_g", "fat_g"]:
        merged_df[col] = (merged_df[col] * merged_df["quantity_g"]) / 100

    # ---- Aggregate daily ----
    daily_summary = merged_df.groupby("date").agg({
        "calories_kcal": "sum",
        "carbs_g": "sum",
        "protein_g": "sum",
        "fat_g": "sum"
    }).reset_index()

    macro_total = (
        daily_summary["carbs_g"] +
        daily_summary["protein_g"] +
        daily_summary["fat_g"]
    )

    daily_summary["carbs_pct"] = daily_summary["carbs_g"] / macro_total * 100
    daily_summary["protein_pct"] = daily_summary["protein_g"] / macro_total * 100
    daily_summary["fat_pct"] = daily_summary["fat_g"] / macro_total * 100

    # ---- Rolling window ----
    window_size = WINDOW_OPTIONS.get(window, 7)

    daily_summary["carbs_roll"] = daily_summary["carbs_pct"].rolling(window_size, 1).mean()
    daily_summary["protein_roll"] = daily_summary["protein_pct"].rolling(window_size, 1).mean()
    daily_summary["fat_roll"] = daily_summary["fat_pct"].rolling(window_size, 1).mean()

    # ---- Deviation ----
    baseline = daily_summary[["carbs_pct", "protein_pct", "fat_pct"]].mean()

    daily_summary["deviation_score"] = (
        abs(daily_summary["carbs_roll"] - baseline["carbs_pct"]) +
        abs(daily_summary["protein_roll"] - baseline["protein_pct"]) +
        abs(daily_summary["fat_roll"] - baseline["fat_pct"])
    )

    # ---- Range pressure ----
    def range_pressure(row):
        p = 0
        if row["carbs_roll"] > REFERENCE_RANGES["carbs"][1]:
            p += row["carbs_roll"] - REFERENCE_RANGES["carbs"][1]
        if row["protein_roll"] < REFERENCE_RANGES["protein"][0]:
            p += REFERENCE_RANGES["protein"][0] - row["protein_roll"]
        if row["fat_roll"] > REFERENCE_RANGES["fat"][1]:
            p += row["fat_roll"] - REFERENCE_RANGES["fat"][1]
        return p

    daily_summary["range_pressure"] = daily_summary.apply(range_pressure, axis=1)

    avg_dev = daily_summary["deviation_score"].mean() + 1e-6
    avg_pressure = daily_summary["range_pressure"].mean() + 1e-6

    daily_summary["raw_risk"] = (
        (daily_summary["deviation_score"] / avg_dev) *
        (1 + daily_summary["range_pressure"] / avg_pressure)
    )

    daily_summary["risk_score"] = daily_summary["raw_risk"].apply(normalize_1_100)

    # ---- Labels ----
    def tag_day(row):
        tags = []
        if row["carbs_roll"] > REFERENCE_RANGES["carbs"][1]:
            tags.append("Carb-heavy")
        if row["fat_roll"] > REFERENCE_RANGES["fat"][1]:
            tags.append("Fat-heavy")
        if row["protein_roll"] < REFERENCE_RANGES["protein"][0]:
            tags.append("Protein-low")
        return tags or ["Within reference range"]

    daily_summary["flags"] = daily_summary.apply(tag_day, axis=1)


    latest = daily_summary.iloc[-1]
    # ---- Risk Level Interpretation ----
    risk_score = int(latest["risk_score"])

    if risk_score < 30:
        risk_level = "Low"
    elif risk_score < 60:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    # ---- Explanation Builder ----
    explanations = []

    if latest["range_pressure"] == 0:
        explanations.append("All macro-nutrient shares remain within reference ranges.")

    if latest["carbs_roll"] > REFERENCE_RANGES["carbs"][1]:
        explanations.append("Carbohydrate share exceeds recommended upper limit.")

    if latest["protein_roll"] < REFERENCE_RANGES["protein"][0]:
        explanations.append("Protein share is below recommended minimum.")

    if latest["fat_roll"] > REFERENCE_RANGES["fat"][1]:
        explanations.append("Fat share exceeds recommended upper limit.")

    if latest["deviation_score"] > daily_summary["deviation_score"].mean():
        explanations.append("Menu composition deviates significantly from historical baseline.")

    if not explanations:
        explanations.append("No abnormal patterns detected in macro distribution.")

    explanation_text = " ".join(explanations)

    return {
    "risk_score": risk_score,
    "risk_level": risk_level,
    "flags": latest["flags"],
    "macro_pct": {
        "carbs": round(latest["carbs_pct"], 1),
        "protein": round(latest["protein_pct"], 1),
        "fat": round(latest["fat_pct"], 1)
    },
    "deviation_score": round(latest["deviation_score"], 2),
    "explanation": explanation_text
}
