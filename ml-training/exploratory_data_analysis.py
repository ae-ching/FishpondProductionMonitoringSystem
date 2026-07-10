import pandas as pd
import matplotlib.pyplot as plt

# ==========================
# LOAD DATASET
# ==========================
df = pd.read_csv("dataset/fishpond_harvest_dataset.csv")

print("Dataset loaded successfully!")

# # ==========================
# # HARVEST QUANTITY DISTRIBUTION
# # ==========================
# plt.figure(figsize=(8,5))

# plt.hist(df["Harvest_Quantity"], bins=20)

# plt.title("Harvest Quantity Distribution")
# plt.xlabel("Harvest Quantity (kg)")
# plt.ylabel("Frequency")

# plt.show()

# # ==========================
# # FISH TYPE DISTRIBUTION
# # ==========================
# plt.figure(figsize=(8,5))
# plt.tight_layout()

# df["Fish_Type"].value_counts().plot(kind="bar")

# plt.title("Fish Type Distribution")
# plt.xlabel("Fish Type")
# plt.ylabel("Number of Records")

# plt.tight_layout()
# plt.show()

# # ==========================
# # HARVEST RECORDS PER MONTH
# # ==========================
# plt.figure(figsize=(8,5))

# df["Harvest_Month"].value_counts().sort_index().plot(kind="bar")

# plt.title("Harvest Records per Month")
# plt.xlabel("Harvest Month")
# plt.ylabel("Number of Records")

# plt.tight_layout()
# plt.show()


# # ==========================
# # POND SIZE VS HARVEST
# # ==========================
# plt.figure(figsize=(8,5))

# plt.scatter(
#     df["Pond_Size"],
#     df["Harvest_Quantity"]
# )

# plt.title("Pond Size vs Harvest Quantity")
# plt.xlabel("Pond Size (hectares)")
# plt.ylabel("Harvest Quantity (kg)")

# plt.tight_layout()
# plt.show()


# # ==========================
# # PREVIOUS VS CURRENT HARVEST
# # ==========================
# plt.figure(figsize=(8,5))

# plt.scatter(
#     df["Previous_Harvest_Quantity"],
#     df["Harvest_Quantity"]
# )

# plt.title("Previous Harvest vs Current Harvest")
# plt.xlabel("Previous Harvest (kg)")
# plt.ylabel("Current Harvest (kg)")

# plt.tight_layout()
# plt.show()


# # ==========================
# # AVERAGE LAST 3 VS CURRENT
# # ==========================
# plt.figure(figsize=(8,5))

# plt.scatter(
#     df["Average_Harvest_Last_3_Records"],
#     df["Harvest_Quantity"]
# )

# plt.title("Average of Last 3 Harvests vs Current Harvest")
# plt.xlabel("Average of Last 3 Harvests (kg)")
# plt.ylabel("Current Harvest (kg)")

# plt.tight_layout()
# plt.show()

# ==========================
# CORRELATION MATRIX
# ==========================
print("\n" + "=" * 60)
print("CORRELATION MATRIX")
print("=" * 60)

correlation = df.corr(numeric_only=True)

print(correlation)