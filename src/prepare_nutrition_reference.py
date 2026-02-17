import pandas as pd

input_file = "Data/Indian_Food_Nutrition_Processed.csv"
output_file = "Data/nutrition_reference_clean.csv"

# -------------------------------
# Load Raw Dataset
# -------------------------------
df = pd.read_csv(input_file)

# -------------------------------
# Select Relevant Columns
# -------------------------------
df = df[
    [
        "Dish Name",
        "Calories (kcal)",
        "Carbohydrates (g)",
        "Protein (g)",
        "Fats (g)"
    ]
]

# -------------------------------
# Rename Columns
# -------------------------------
df = df.rename(columns={
    "Dish Name": "dish",
    "Calories (kcal)": "calories_kcal",
    "Carbohydrates (g)": "carbs_g",
    "Protein (g)": "protein_g",
    "Fats (g)": "fat_g"
})

# -------------------------------
# Basic Cleaning
# -------------------------------
df["dish"] = df["dish"].str.strip().str.lower()

# Remove rows with missing values
df = df.dropna()

# Remove duplicate dish entries (keep first)
df = df.drop_duplicates(subset="dish", keep="first")

# Remove rows with non-positive macro values
df = df[
    (df["calories_kcal"] > 0) &
    (df["carbs_g"] >= 0) &
    (df["protein_g"] >= 0) &
    (df["fat_g"] >= 0)
]

# Save Clean Reference
df.to_csv(output_file, index=False)

print("Nutrition reference file cleaned and saved successfully.")
