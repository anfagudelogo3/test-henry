# Pipelines de datos para ML con Airflow

Demo práctica de 15 minutos para la clase de **ingeniería de datos**. Construimos un pipeline de ML para predecir churn en una empresa de telecomunicaciones, y lo orquestamos con Apache Airflow.

## ¿Qué hay en este repo?

```
notebooks/churn_pipeline_demo.ipynb   # La clase: pipeline paso a paso + bridge a Airflow
dags/pipeline.py                      # Las 6 funciones del pipeline (importadas por el DAG)
dags/churn_pipeline_dag.py            # El mismo pipeline como DAG de Airflow
data/raw/Telco_customer_churn.xlsx    # Dataset: 7,043 clientes de telecomunicaciones
docker-compose.yml                    # Stack de Airflow (postgres + webserver + scheduler)
run_airflow.sh                        # Script para levantar el stack
runbook.md                            # Instrucciones detalladas de operación
```

## Levantar Airflow

```bash
./run_airflow.sh
```

UI disponible en `http://localhost:8080` — usuario `admin` / contraseña `admin`.

Ver `runbook.md` para instrucciones completas, troubleshooting y la demo del fallo simulado.

## Stack

- Python 3.12 · pandas · scikit-learn · Apache Airflow 2.9.3
- Docker Compose (LocalExecutor + Postgres)
- Gestión de paquetes: [uv](https://github.com/astral-sh/uv)
