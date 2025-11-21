# Pipeline ETL – Proyecto 3

Este pipeline implementa un flujo de analítica batch completamente en AWS:

1. **RDS → Glue Catalog**
   - Se crea una conexión JDBC en Glue.
   - Glue lee la tabla `covid_complement`.

2. **Glue Job → S3 RAW**
   - Un Glue Job Spark extrae los datos.
   - Se convierte a Parquet.
   - Se deposita en `s3://vladdatalake/raw/rds/covid_complement/`.

3. **EMR Step 1: ETL**
   - El script `etl_covid.py` limpia y transforma los datos.
   - Genera la capa PROCESSED en S3.

4. **EMR Step 2: Analytics**
   - El script `analytics_covid.py` calcula métricas.
   - Genera la capa ANALYTICS en S3.

5. **Athena (opcional)**
   - Se crean tablas externas para consultar los Parquet procesados.
