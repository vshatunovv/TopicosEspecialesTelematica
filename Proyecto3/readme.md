# Proyecto 3 – Data Lake en AWS con RDS, Glue, EMR, S3 y Athena  
Curso: ST0263 – Tópicos Especiales en Telemática / Computación en la Nube

## 1. Descripción general del proyecto

Este repositorio contiene la implementación completa de un **Data Lake en AWS** para el análisis de datos de COVID, siguiendo una arquitectura basada en servicios administrados:

- **Fuente de datos**: tabla en **Amazon RDS** (MySQL).
- **Ingesta y carga a Data Lake (RAW)**: **AWS Glue** (Job Spark).
- **Procesamiento batch (ETL / Analytics)**: **Amazon EMR** con **Spark**.
- **Almacenamiento en niveles**: **Amazon S3** con zonas `raw/`, `processed/` y `analytics/`. 
- **Consulta interactiva (opcional)**: **Amazon Athena** sobre archivos Parquet.

El objetivo es demostrar un flujo de datos de punta a punta:

> RDS → Glue → S3 (raw) → EMR (ETL) → S3 (processed) → EMR (analytics) → S3 (analytics) → Athena

Este repositorio incluye los **scripts, instrucciones y documentación necesarios** para replicar el proyecto.

---

## 2. Arquitectura del sistema

En la carpeta [`/docs`](docs/) se incluyen imágenes de apoyo:

- `arquitectura.png` – Diagrama de alto nivel de la solución.
- `pipeline.png` – Flujo detallado del procesamiento de datos.
- Carpeta `docs/evidencias/` – Capturas de pantalla de cada componente funcionando.

### 2.1 Componentes principales

- **Amazon RDS (MySQL)**  
  Base de datos relacional donde se almacena la tabla `covid_complement` (datos complementarios de COVID).

- **Amazon EC2 (mysql-client)**  
  Instancia utilizada como:
  - cliente para conectarse al RDS vía `mysql`
  - máquina de administración para probar comandos `aws s3 ls`, etc.

- **Amazon S3 – Data Lake (`vladdatalake`)**  
  Estructura de carpetas:

  ```
  s3://vladdatalake/
    raw/
      rds/
        covid_complement/       # salida del Glue Job
    processed/
      covid/                    # salida del Step ETL en EMR
    analytics/
      covid/                    # salida del Step Analytics en EMR
    scripts/
      emr/
        etl_covid.py
        analytics_covid.py
  ```

- **AWS Glue**

  - Connection a RDS (en la misma VPC).

  - Crawler o definición de tabla en Glue Data Catalog.

  - Job Spark que extrae datos desde RDS y los escribe como Parquet en S3 (zona RAW).

- **Amazon EMR**

  - Clúster EMR (por ejemplo: `emr-covid`) en la misma VPC.

  - Step 1: `etl_covid.py` → genera capa processed.

  - Step 2: `analytics_covid.py` → genera capa analytics.

- **Amazon Athena**

  - Base de datos `covid_athena_db`.

  - Tablas externas `covid_processed` y `covid_analytics` apuntando a S3.
 
 ### 3.Estructura del repositorio
 
 ```
├── scripts/
│   ├── export_rds_to_s3.py          # Script del Job de Glue
│   └── emr/
│       ├── etl_covid.py             # Script de ETL en EMR (RAW → PROCESSED)
│       └── analytics_covid.py       # Script de Analytics en EMR (PROCESSED → ANALYTICS)
│
├── emr-steps/
│   └── README.md                    # Documentación de los steps usados en EMR (comandos spark-submit)
│
├── docs/
│   ├── arquitectura.png             # Diagrama de arquitectura
│   ├── pipeline.png                 # Flujo de datos
│   └── evidencias/
│       ├── rds.png
│       ├── ec2-mysql.png
│       ├── glue-job.png
│       ├── s3-raw.png
│       ├── s3-processed.png
│       ├── s3-analytics.png
│       ├── emr-steps.png
│       └── athena.png
│
└── README.md                        # Este documento
```


- ## 4. Prerrequisitos

Para poder replicar el proyecto se requiere:

  - Cuenta de AWS con permisos para:

    - RDS, EC2, S3, Glue, EMR, Athena, IAM.

  -Región usada: `us-east-2` (Ohio).

  -IAM Roles recomendados:

   - Rol para EC2 con permisos S3: `AmazonS3FullAccess` o política equivalente acotada al bucket.

   - Roles por defecto de EMR con permisos S3.

   - Rol de Glue con acceso a S3 y RDS.        

## 5. Detalle de implementación paso a paso
### 5.1 Creación de la base de datos en RDS (MySQL)

1.Ir a RDS → Databases → Create database.

2.Tipo: MySQL (Free tier/bajo costo).

3.Nombre de la instancia: `covid-db`.

4.Usuario administrador: por ejemplo, `admin`.

5.Crear una base de datos, por ejemplo `covid_db`.

6.Asegurarse de que la instancia:

 -  Está en la misma VPC que EMR y Glue.

 -  Tiene un Security Group que permite tráfico desde la instancia EC2 (mysql-client) y, vía Glue Connection, desde Glue.


## Conexión desde EC2

En una instancia EC2 llamada `mysql-client`:
```bash
ssh -i "llave.pem" ec2-user@<IP_PUBLICA_EC2>

# Conectarse al RDS MySQL:
mysql -h <ENDPOINT_RDS> -u admin -p

USE covid_db;
SELECT * FROM covid_complement LIMIT 10;
```
La tabla principal usada en el proyecto es:

  -  `covid_complement` (nombre de ejemplo, puede variar según la práctica).

## 5.2 Creación del Data Lake en S3

Crear un bucket S3 (ejemplo):

```text
Nombre del bucket: vladdatalake
Región: us-east-2
```

Estructura lógica usada:

```text
s3://vladdatalake/
  raw/
    rds/
      covid_complement/
  processed/
    covid/
  analytics/
    covid/
  scripts/
    emr/
```
Los scripts de EMR se suben a:

```text
s3://vladdatalake/scripts/emr/etl_covid.py
s3://vladdatalake/scripts/emr/analytics_covid.py
```

## 5.3 Glue: Connection + Job para exportar desde RDS a S3 (RAW)
### 5.3.1 Crear Connection a RDS
1.Ir a AWS Glue → Connections → Add connection.

2.Tipo: JDBC.

3.Proveer el endpoint de RDS y credenciales.

4.Seleccionar la misma VPC, subred privada y security group que permiten acceso a RDS.

5.Probar la conexión (Test connection → SUCCESS).

### 5.3.2 Script de Glue Job `(scripts/export_rds_to_s3.py)`

Ejemplo de script usado:
```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'TARGET_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

TARGET_BUCKET = args['TARGET_BUCKET']

# Leer la tabla desde Glue Catalog
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="covid_catalog_db",
    table_name="covid_db_covid_complement"
)

# Escribir en S3 como parquet (zona RAW)
output_path = f"s3://{TARGET_BUCKET}/raw/rds/covid_complement/"
glueContext.write_dynamic_frame.from_options(
    frame=dyf,
    connection_type="s3",
    connection_options={"path": output_path},
    format="parquet"
)

job.commit()
```

### 5.3.3 Crear y ejecutar el Glue Job

1.Ir a AWS Glue → Jobs → Add job.

2.Motor: Spark.

3.Asignar el rol de Glue con permisos a S3 y RDS.

4.En “Script”, usar `export_rds_to_s3.py` (copiar el contenido del archivo del repo).

5.En las opciones de Job parameters, pasar:

  -  `--TARGET_BUCKET` = `vladdatalake`

6.En la sección Connections, seleccionar la conexión creada a RDS.

7.Ejecutar el Job y verificar que termine en `SUCCEEDED.`

8.Comprobar en S3:

```bash
aws s3 ls s3://vladdatalake/raw/rds/covid_complement/
```
Debe haber archivos `.parquet`

## 5.4 EMR: procesamiento batch con Spark (ETL + Analytics)
### 5.4.1 Scripts para EMR (Spark)

Los scripts se encuentran en `scripts/emr/`:

`etl_covid.py` (RAW → PROCESSED)

Este script:

Lee los datos desde `raw/rds/covid_complement/`.

Realiza transformaciones básicas / limpieza.

Escribe el resultado en `processed/covid/`.

Ejemplo de estructura:
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

BUCKET = "vladdatalake"

spark = SparkSession.builder.appName("ETL-COVID").getOrCreate()

# Leer datos complementarios desde RAW
df = spark.read.parquet(f"s3://{BUCKET}/raw/rds/covid_complement/")

# (Opcional) Limpieza / selección de columnas
df_clean = df.dropDuplicates()

# Escribir a zona PROCESSED
output_path = f"s3://{BUCKET}/processed/covid/"
df_clean.write.mode("overwrite").parquet(output_path)

spark.stop()
```
`analytics_covid.py` (PROCESSED → ANALYTICS)

Este script:

Lee los datos procesados desde `processed/covid/`.

Calcula métricas agregadas (por ejemplo, conteo de registros).

Escribe la salida en `analytics/covid/`.

Ejemplo de estructura:
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import count

BUCKET = "vladdatalake"

spark = SparkSession.builder.appName("Analytics-COVID").getOrCreate()

df = spark.read.parquet(f"s3://{BUCKET}/processed/covid/")

# Ejemplo simple: contar registros totales
result = df.count()
result_df = spark.createDataFrame([(result,)], ["total_registros"])

# Escribir a zona ANALYTICS
output_path = f"s3://{BUCKET}/analytics/covid/"
result_df.write.mode("overwrite").parquet(output_path)

spark.stop()
```
### 5.4.2 Creación del clúster EMR

1.Ir a EMR → Create cluster → Advanced.

2.Nombre: `emr-covid`.

3.Versión de EMR: 6.15.

4.Aplicaciones: Spark (Hadoop viene incluido).

5.Hardware:

  -  1 master (`m5.xlarge`).

  -  1 core node (`m5.xlarge`).

6.VPC y subred: la misma de RDS/Glue.

7.Logging habilitado a un bucket, por ejemplo:

```text
s3://vladdatalake/emr-logs/
```
8.Autotermination despues de 1h de inactividad

### 5.4.3 Steps en EMR

Se agregan dos Steps de tipo "Spark application" usando `command-runner.jar`:

-  Step 1 – ETL
Ver `emr-steps/README.md`
.

Comando (Arguments):
```bash
spark-submit --deploy-mode cluster --master yarn s3://vladdatalake/scripts/emr/etl_covid.py
```

-  Step 2 – Analytics

```bash
spark-submit --deploy-mode cluster --master yarn s3://vladdatalake/scripts/emr/analytics_covid.py

```

Ambos Steps deben terminar con estado **COMPLETED**.

Al finalizar: 

```bash
aws s3 ls s3://vladdatalake/processed/covid/
aws s3 ls s3://vladdatalake/analytics/covid/
```

Deben existir archivos `.parquet` (y archivos tipo `_SUCCESS`).

### 5.5 Athena

1.Para facilitar la consulta de los datos:

2.Ir a **Athena** → **Query editor**.

3.Configurar ubicación de resultados:
```text
s3://vladdatalake/athena-results/
```
4.Crear tabla externa para `processed`:
```sql
CREATE EXTERNAL TABLE covid_athena_db.covid_processed (
  -- columnas según el schema real del parquet
)
STORED AS PARQUET
LOCATION 's3://vladdatalake/processed/covid/';
```
5.Crear tabla externa para analytics:
```sql
CREATE EXTERNAL TABLE covid_athena_db.covid_analytics (
  -- columnas según el schema del resultado analytics
)
STORED AS PARQUET
LOCATION 's3://vladdatalake/analytics/covid/';
```
6.Consultar
```sql
SELECT * FROM covid_athena_db.covid_processed LIMIT 10;
SELECT * FROM covid_athena_db.covid_analytics LIMIT 10;
```

## 6. Evidencias de funcionamiento

En la carpeta `docs/evidencias/` se incluyen capturas de:

-  RDS con la base de datos y tabla `covid_complement`.

-  EC2 conectándose a RDS vía `mysql` y mostrando datos.

-  Glue Job `export_rds_to_s3` en estado `SUCCEEDED`.

-  S3 con datos en:

  -  `raw/rds/covid_complement/`

  -  `processed/covid/`

  -  `analytics/covid/`

-  EMR con Steps `etl_covid` y `analytics_covid` en `COMPLETED`.

-  Athena mostrando tablas y consultas de ejemplo.


## 7. Cómo replicar el proyecto (resumen rápido)

1.Crear RDS MySQL y cargar la tabla `covid_complement`.

2.Crear EC2 `mysql-client` en la misma VPC y probar conexión al RDS.

3.Crear bucket S3 `vladdatalake` con estructura de Data Lake.

4.Crear Glue Connection a RDS, Glue Database y tabla en el Catalog.

5.Crear Glue Job con el script `export_rds_to_s3.py` y ejecutar → genera `raw/rds/covid_complement/`.

6.Subir `etl_covid.py` y `analytics_covid.py` a `s3://vladdatalake/scripts/emr/`.

7.Crear clúster EMR y agregar Steps Spark que ejecuten esos scripts.

8.Verificar en S3 las zonas `processed/` y `analytics/`.

9.(Opcional) Configurar Athena y crear tablas externas para consultar los datos.

## 8. Estudiante / Curso

-  Estudiante: **Vladlen Shatunov**

-  Curso: **ST0263 – Tópicos Especiales en Telemática**

-  Universidad: **EAFIT**

-  Semestre: **2025-2**
