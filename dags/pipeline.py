"""Lógica del pipeline de churn — las seis funciones de
``notebooks/churn_pipeline_demo.ipynb``, extraídas a un módulo para que **tanto**
el notebook como el DAG de Airflow importen el mismo código.

Este módulo no sabe nada de Airflow. Es Python puro con pandas y scikit-learn,
que es exactamente el punto: el orquestador envuelve estas funciones, no las reemplaza.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

# ── Rutas ─────────────────────────────────────────────────────────────────────
# Resueltas relativas a la raíz del repo (este archivo vive en <repo>/dags/),
# así el pipeline funciona sin importar desde qué directorio lo ejecute Airflow.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data" / "raw" / "Telco_customer_churn.xlsx"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

CATEGORICAL_FEATURES = [
    "Gender", "Senior Citizen", "Partner", "Dependents",
    "Phone Service", "Multiple Lines", "Internet Service",
    "Online Security", "Online Backup", "Device Protection",
    "Tech Support", "Streaming TV", "Streaming Movies",
    "Contract", "Paperless Billing", "Payment Method",
]
NUMERIC_FEATURES = ["Tenure Months", "Monthly Charges", "Total Charges"]
TARGET = "Churn Value"


def extract_data() -> pd.DataFrame:
    """Paso 1 — Lee la base de clientes desde la fuente de datos."""
    df = pd.read_excel(DATA_PATH)
    print(f"✅ extract_data | {len(df):,} clientes cargados | {df.shape[1]} columnas")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Paso 2 — Corrige tipos, maneja nulos y estandariza valores."""
    df = df.copy()

    # Total Charges viene como string con espacios en blanco en algunos registros
    df["Total Charges"] = pd.to_numeric(df["Total Charges"], errors="coerce")

    # Clientes nuevos (Tenure = 0) tienen Total Charges nulo → rellenar con Monthly Charges
    df["Total Charges"] = df["Total Charges"].fillna(df["Monthly Charges"])

    # Churn Reason solo tiene valor para churners
    df["Churn Reason"] = df["Churn Reason"].fillna("No churn")

    nulls_remaining = df.isnull().sum().sum()
    print(f"✅ clean_data | Nulos restantes: {nulls_remaining}")
    return df


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Paso 3 — Encodea categóricas y selecciona las features del modelo."""
    df = df.copy()
    le = LabelEncoder()
    for col in CATEGORICAL_FEATURES:
        df[col] = le.fit_transform(df[col].astype(str))
    features = CATEGORICAL_FEATURES + NUMERIC_FEATURES + [TARGET]
    df_model = df[features]
    print(
        f"✅ feature_engineering | {len(CATEGORICAL_FEATURES)} features categóricas "
        f"encodadas | shape: {df_model.shape}"
    )
    return df_model


def train_model(df: pd.DataFrame):
    """Paso 4 — Entrena el clasificador y persiste los splits."""
    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Guardar splits en data/processed/
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    X_train.to_csv(PROCESSED_DIR / "X_train.csv", index=True)
    X_test.to_csv(PROCESSED_DIR / "X_test.csv", index=True)
    y_train.to_csv(PROCESSED_DIR / "y_train.csv", index=True)
    y_test.to_csv(PROCESSED_DIR / "y_test.csv", index=True)

    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    print(f"✅ train_model | Entrenado con {len(X_train):,} registros | Test: {len(X_test):,}")
    print(f"   💾 Splits guardados en {PROCESSED_DIR}/")

    return model, X_test, y_test


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> None:
    """Paso 5 — Calcula métricas de desempeño sobre el conjunto de prueba."""
    y_pred = model.predict(X_test)
    print("✅ evaluate_model\n")
    print(classification_report(y_test, y_pred, target_names=["No Churn", "Churn"]))


def generate_predictions(
    model, X_test: pd.DataFrame, df_original: pd.DataFrame, top_n: int = 20
) -> pd.DataFrame:
    """Paso 6 — Genera la lista de clientes con mayor riesgo de churn."""
    probs = model.predict_proba(X_test)[:, 1]  # probabilidad de churn sobre el set de test
    result = df_original.loc[
        X_test.index, ["CustomerID", "City", "Contract", "Monthly Charges"]
    ].copy()
    result["churn_probability"] = probs
    result["churn_probability"] = result["churn_probability"].map("{:.1%}".format)
    print("✅ generate_predictions")
    return result.reset_index(drop=True)
