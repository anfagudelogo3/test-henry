FROM apache/airflow:2.9.3

# scikit-learn y openpyxl no están en la imagen base.
# Se instalan aquí para que cada contenedor arranque rápido — sin pip install en tiempo de ejecución.
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
