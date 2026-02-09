import pandas as pd

nutrition_df = pd.read_csv("Data/nutrition_reference_clean.csv")
nutrition_df["dish"] = nutrition_df["dish"].str.strip().str.lower()

menu_df = pd.read_csv("Data/mess_menu.csv")
menu_df["dish"] = menu_df["dish"].str.strip().str.lower()

def normalize_dish_name(dish):
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
)

unmatched = merged_df[merged_df["calories_kcal"].isna()]["dish_x"].unique()
if len(unmatched) > 0:
    print("Unmatched dishes (skipped):")
    for d in unmatched:
        print("-", d)

merged_df = merged_df.dropna()

for col in ["calories_kcal", "carbs_g", "protein_g", "fat_g"]:
    merged_df[col] = (merged_df[col] * merged_df["quantity_g"]) / 100

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

daily_summary["carbs_pct"] = (daily_summary["carbs_g"] / macro_total) * 100
daily_summary["protein_pct"] = (daily_summary["protein_g"] / macro_total) * 100
daily_summary["fat_pct"] = (daily_summary["fat_g"] / macro_total) * 100

print(daily_summary)


window = 3

daily_summary["carbs_roll"] = daily_summary["carbs_pct"].rolling(window, min_periods=1).mean()
daily_summary["protein_roll"] = daily_summary["protein_pct"].rolling(window, min_periods=1).mean()
daily_summary["fat_roll"] = daily_summary["fat_pct"].rolling(window, min_periods=1).mean()

baseline_carbs = daily_summary["carbs_pct"].mean()
baseline_protein = daily_summary["protein_pct"].mean()
baseline_fat = daily_summary["fat_pct"].mean()

daily_summary["carbs_dev"] = daily_summary["carbs_roll"] - baseline_carbs
daily_summary["protein_dev"] = daily_summary["protein_roll"] - baseline_protein
daily_summary["fat_dev"] = daily_summary["fat_roll"] - baseline_fat

daily_summary["imbalance_score"] = (
    abs(daily_summary["carbs_dev"]) +
    abs(daily_summary["protein_dev"]) +
    abs(daily_summary["fat_dev"])
)

max_score = daily_summary["imbalance_score"].max()
daily_summary["risk_score"] = (
    (daily_summary["imbalance_score"] / max_score) * 100
    if max_score != 0 else 0
)

print("\nDaily Imbalance & Risk Score")
print(daily_summary[[
    "date",
    "carbs_pct",
    "protein_pct",
    "fat_pct",
    "risk_score"
]])

