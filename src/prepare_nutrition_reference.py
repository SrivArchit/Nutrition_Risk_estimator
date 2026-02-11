import pandas as pd

input_file = "Data/Indian_Food_Nutrition_Processed.csv"
df = pd.read_csv(input_file)


df = df[
    [
        "Dish Name",
        "Calories (kcal)",
        "Carbohydrates (g)",
        "Protein (g)",
        "Fats (g)"
    ]
]

df = df.rename(columns={
    "Dish Name": "dish",
    "Calories (kcal)": "calories_kcal",
    "Carbohydrates (g)": "carbs_g",
    "Protein (g)": "protein_g",
    "Fats (g)": "fat_g"
})


df["dish"] = df["dish"].str.strip().str.lower()

df = df.dropna()

output_file = "Data/nutrition_reference_clean.csv"

df.to_csv(output_file, index=False)
