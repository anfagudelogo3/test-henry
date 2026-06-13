# Runbook — Demo Churn Pipeline (Airflow + Docker)

## Requisitos previos

| Requisito | Versión | Cómo verificar |
|---|---|---|
| Docker Desktop | ≥ 4.x | `docker --version` |
| Docker Compose | ≥ 2.x (plugin) | `docker compose version` |
| RAM libre | ≥ 4 GB asignados a Docker | Docker Desktop → Configuración → Resources |
| Espacio en disco | ≥ 3 GB | Para imágenes + volumen de postgres |
| Puerto 8080 | Disponible | `lsof -i :8080` (no debe devolver nada) |

No se necesita Python, pip ni entorno virtual en el host — todo corre dentro de los contenedores.

---

## Configuración inicial

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd test-henry

# 2. Levantar el stack (construye la imagen en el primer run — tarda ~2 min)
./run_airflow.sh
```

El script construye la imagen de Docker, inicia todos los servicios, espera a que el webserver esté disponible y muestra la URL y las credenciales.

---

## Acceder a la UI

```
URL:        http://localhost:8080
Usuario:    admin
Contraseña: admin
```

---

## Uso diario

| Acción | Comando |
|---|---|
| Levantar el stack | `./run_airflow.sh` |
| Apagar el stack | `docker compose down` |
| Reiniciar el stack | `docker compose restart` |
| Ver todos los logs | `docker compose logs -f` |
| Ver logs de un servicio | `docker compose logs -f airflow-scheduler` |
| Reconstruir tras un cambio | `docker compose up -d --build` |

---

## Ejecutar el pipeline

### Desde la UI

1. Abrir `http://localhost:8080` e iniciar sesión.
2. Hacer clic en **churn_pipeline**.
3. Presionar el botón **▶ Trigger DAG** (arriba a la derecha).
4. Ir a la vista **Graph** y observar cómo las tareas se ponen en verde una por una.
5. Hacer clic en cualquier tarea → **Log** para ver su salida.

### Desde la terminal

```bash
# Ejecutar manualmente
docker compose exec airflow-scheduler airflow dags trigger churn_pipeline

# Ver el estado de la ejecución
docker compose exec airflow-scheduler airflow dags list-runs -d churn_pipeline
```

---

## Demo: simulación de fallo en una tarea

Demuestra por qué un orquestador es mejor que un script — cuando `clean` falla, Airflow bloquea automáticamente todas las tareas siguientes.

```bash
# 1. Activar el interruptor de fallo
docker compose exec airflow-scheduler airflow variables set FAIL_CLEAN true

# 2. Disparar el DAG desde la UI y observar cómo clean falla en rojo,
#    y engineer → train → evaluate → generate quedan en upstream_failed.

# 3. Recuperar
docker compose exec airflow-scheduler airflow variables set FAIL_CLEAN false
```

---

## Archivos de salida

Después de una ejecución exitosa, los siguientes archivos quedan escritos en el host:

```
data/
├── raw/
│   └── Telco_customer_churn.xlsx   # dataset de entrada
└── processed/
    ├── X_train.csv                 # features de entrenamiento
    ├── X_test.csv                  # features de prueba
    ├── y_train.csv                 # etiquetas de entrenamiento
    └── y_test.csv                  # etiquetas de prueba

logs/                               # logs por tarea de Airflow (un archivo por ejecución)
```

---

## Descripción de servicios

| Servicio | Rol | Puerto |
|---|---|---|
| `postgres` | Base de datos de metadatos de Airflow | solo interno |
| `airflow-init` | Migración de DB + creación del usuario admin (se ejecuta una vez) | — |
| `airflow-webserver` | UI y API REST | 8080 |
| `airflow-scheduler` | Programa y ejecuta las tareas (LocalExecutor) | solo interno |

---

## Apagar el stack

```bash
# Detener contenedores y conservar el volumen de postgres (historial preservado)
docker compose down

# Detener contenedores Y eliminar el historial (pizarrón en blanco)
docker compose down -v
```

---

## Solución de problemas

**Puerto 8080 en uso**
```bash
lsof -i :8080        # encontrar el proceso
kill -9 <PID>        # terminarlo
```

**El webserver no levanta**
```bash
docker compose logs airflow-webserver | tail -30
```

**El DAG no aparece en la UI**
```bash
# Verificar errores de importación
docker compose exec airflow-scheduler airflow dags list-import-errors
```

**Errores de permisos en `data/` o `logs/`**
```bash
chmod -R 755 data/ logs/
```

**Reseteo completo**
```bash
docker compose down -v          # eliminar contenedores + volumen de postgres
docker image rm test-henry-airflow-webserver test-henry-airflow-scheduler test-henry-airflow-init 2>/dev/null
./run_airflow.sh                # reconstruir desde cero
```
