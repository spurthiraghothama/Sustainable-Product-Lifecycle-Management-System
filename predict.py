import mysql.connector
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib

# ---------------------------
# 1. Connect to MySQL
# ---------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",        # Change if your MySQL username is different
    password="Spurthi1-5",        # If you have a password, put it here
    database="circular_economy_db"
)

print("✅ Connected to MySQL successfully!\n")

# ---------------------------
# 2. Create training dataset
# ---------------------------
query = """
SELECT 
    pi.InstanceID,
    p.ProductID,
    p.ModelName,
    SUM(cc.WeightInGrams) AS total_weight,
    AVG(
        CASE rm.RecyclableGrade
            WHEN 'A' THEN 4
            WHEN 'B' THEN 3
            WHEN 'C' THEN 2
            WHEN 'D' THEN 1
            ELSE 0
        END
    ) AS avg_recyclability,
    SUM(rm.IsHazardous) AS hazardous_count,
    COUNT(DISTINCT cc.ComponentID) AS component_count,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM LifecycleEvents le 
            WHERE le.InstanceID = pi.InstanceID 
              AND (le.EventType = 'Recycled' OR le.EventType = 'Recycled_Hazardous')
        ) THEN 1
        WHEN EXISTS (
            SELECT 1 FROM LifecycleEvents le 
            WHERE le.InstanceID = pi.InstanceID 
              AND le.EventType = 'Disposed'
        ) THEN 0
        ELSE NULL
    END AS target
FROM ProductInstances pi
JOIN Products p ON pi.ProductID = p.ProductID
JOIN BillOfMaterial bom ON bom.ParentComponentID LIKE 'C%'   -- Join only component assemblies
JOIN ComponentComposition cc ON bom.ChildComponentID = cc.ComponentID
JOIN RawMaterials rm ON rm.MaterialID = cc.MaterialID
GROUP BY pi.InstanceID;
"""

df = pd.read_sql(query, conn)
conn.close()

print("Dataset preview:")
print(df.head(), "\n")

# Drop rows where target is NULL (no lifecycle event)
df = df.dropna(subset=["target"])

if df.empty:
    print("⚠️ No data found for training. Please ensure LifecycleEvents and Components are linked correctly.")
    exit()

# ---------------------------
# 3. Feature Engineering
# ---------------------------
X = df[["total_weight", "avg_recyclability", "hazardous_count", "component_count"]]
y = df["target"]

# Scale the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------------------------
# 4. Train-Test Split
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

# ---------------------------
# 5. Train Model
# ---------------------------
model = LogisticRegression()
model.fit(X_train, y_train)

# ---------------------------
# 6. Evaluate Model
# ---------------------------
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print("✅ Model Trained Successfully!")
print(f"Accuracy: {acc * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# ---------------------------
# 7. Save Model & Scaler
# ---------------------------
joblib.dump(model, "recycle_predictor.pkl")
joblib.dump(scaler, "recycle_scaler.pkl")
print("\n🎯 Model and scaler saved successfully!")
print("Files saved as: recycle_predictor.pkl and recycle_scaler.pkl")
