"""DAG de Airflow — el pipeline del notebook, ahora orquestado.

Las mismas seis funciones que los estudiantes vieron en ``churn_pipeline_demo.ipynb``
se convierten en seis **tasks** de Airflow. Airflow agrega lo que un script simple
no puede: un schedule (``0 6 * * *`` → todos los días a las 6 AM), reintentos
automáticos, logs por tarea, y un grafo de dependencias que se niega a ejecutar
pasos posteriores cuando uno anterior falla.

Interruptor de demo
-------------------
Establecer la Variable de Airflow ``FAIL_CLEAN`` en ``"true"`` hace que ``clean_data``
falle a propósito. Disparar el DAG y observar cómo ``feature_engineering`` → … →
``generate_predictions`` pasan a *upstream_failed* — Airflow no entrenará un modelo
con datos que nunca fueron limpiados. Volver a ``"false"`` para recuperar.

    docker compose exec airflow-scheduler airflow variables set FAIL_CLEAN true
    docker compose exec airflow-scheduler airflow variables set FAIL_CLEAN false
"""

from __future__ import annotations

import pendulum
from airflow.decorators import dag, task
from airflow.models import Variable

import pipeline  # dags/ está en sys.path, el módulo vive junto a este archivo

default_args = {
    "owner": "data-science",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=1),
}


@dag(
    dag_id="churn_pipeline",
    description="Pipeline diario de churn — extract → clean → features → train → evaluate → predict",
    schedule="0 6 * * *",                       # todos los días a las 6:00 AM
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,                              # no rellenar ejecuciones históricas
    default_args=default_args,
    tags=["ml", "churn", "demo"],
)
def churn_pipeline():
    @task
    def extract():
        return pipeline.extract_data()

    @task
    def clean(df):
        # Interruptor de demo: simula un fallo en la limpieza de datos.
        if Variable.get("FAIL_CLEAN", default_var="false").lower() == "true":
            raise ValueError(
                "💥 Fallo simulado en clean_data — las tareas siguientes quedarán bloqueadas."
            )
        return pipeline.clean_data(df)

    @task
    def engineer(df):
        return pipeline.feature_engineering(df)

    @task
    def train(df_features):
        model, X_test, y_test = pipeline.train_model(df_features)
        return {"model": model, "X_test": X_test, "y_test": y_test}

    @task
    def evaluate(trained):
        pipeline.evaluate_model(trained["model"], trained["X_test"], trained["y_test"])

    @task
    def generate(trained, df_clean):
        predictions = pipeline.generate_predictions(
            trained["model"], trained["X_test"], df_clean
        )
        print("\n📋 Lista lista para el equipo comercial:")
        print(predictions.to_string())
        return predictions

    # ── Dependencias del pipeline ──────────────────────────────────────────────
    raw = extract()
    clean_df = clean(raw)
    features = engineer(clean_df)
    trained = train(features)

    evaluate(trained)                 # evaluate y generate dependen del modelo entrenado
    generate(trained, clean_df)       # generate además usa los datos limpios (CustomerID, City…)


churn_pipeline()
