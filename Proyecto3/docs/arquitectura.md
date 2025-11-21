# Arquitectura del Data Lake (AWS)

Este documento describe el flujo general del sistema implementado:

1. Los datos originales se encuentran en un RDS MySQL.
2. Una instancia EC2 se conecta para validación.
3. Glue crea una conexión JDBC hacia RDS.
4. Un Glue Job ejecuta `export_rds_to_s3.py` y exporta datos en formato Parquet hacia la zona RAW del Data Lake.
5. Un clúster EMR ejecuta dos Steps de Spark:
   - `etl_covid.py` → genera la zona PROCESSED.
   - `analytics_covid.py` → genera la zona ANALYTICS.
6. Athena puede consultar datos en PROCESSED o ANALYTICS mediante tablas externas.
