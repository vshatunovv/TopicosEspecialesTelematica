Este documento describe en detalle los **Steps ejecutados en Amazon EMR** para el procesamiento ETL y analítico del Proyecto 3. Incluye:

- Scripts usados en cada Step
- Comandos ejecutados
- Lugar donde se usan
- Requisitos previos
- Cómo reproducir los Steps
- Resultados esperados

---

## 1. Introducción

En este proyecto, Amazon EMR se utilizó como motor de procesamiento distribuido con **Apache Spark**.  
El clúster ejecuta dos Steps principales:

1. **ETL (Transformación de datos)**  
   Script: `etl_covid.py`

2. **Analytics (Cálculo de métricas)**  
   Script: `analytics_covid.py`

Ambos scripts se almacenan en:

```
s3://vladdatalake/scripts/emr/
```

---

## 2. Scripts utilizados en EMR

### 2.1 Script ETL – `etl_covid.py`

Ruta en S3:

```
s3://vladdatalake/scripts/emr/etl_covid.py
```

Función:

- Leer archivos Parquet desde la zona **RAW** en S3.
- Limpiar / transformar datos.
- Escribir el resultado en la zona **PROCESSED**:

```
s3://vladdatalake/processed/covid/
```

---

### 2.2 Script Analytics – `analytics_covid.py`

Ruta en S3:

```
s3://vladdatalake/scripts/emr/analytics_covid.py
```

Función:

- Leer datos desde la zona **PROCESSED**.
- Generar métricas o agregaciones.
- Guardar resultados en **ANALYTICS**:

```
s3://vladdatalake/analytics/covid/
```

---

## 3. Creación del clúster EMR

Antes de agregar los Steps, se creó un clúster EMR con la siguiente configuración:

- **Aplicaciones**: Spark, Hadoop  
- **Versión de EMR**: 6.x  
- **Flota**: 1 Master + 1 Core  
- **Tipo de instancias**: m5.xlarge
- **VPC**: misma VPC de RDS y Glue  
- **Logging habilitado**:  
  ```
  s3://vladdatalake/emr-logs/
  ```

---

## 4. Steps ejecutados

---

### 🟩 STEP 1: ETL – RAW → PROCESSED

**Nombre del Step:** `etl_covid`  
**Tipo:** Spark application  
**Comando (`Arguments`):**

```
spark-submit --deploy-mode cluster --master yarn s3://vladdatalake/scripts/emr/etl_covid.py
```

**Resultado esperado:**  
En caso de éxito aparece:

```
processed/covid/
    part-0000*.parquet
    _SUCCESS
```

---

### 🟦 STEP 2: Analytics – PROCESSED → ANALYTICS

**Nombre del Step:** `analytics_covid`  
**Tipo:** Spark application  
**Comando (`Arguments`):**

```
spark-submit --deploy-mode cluster --master yarn s3://vladdatalake/scripts/emr/analytics_covid.py
```

**Resultado esperado:**

```
analytics/covid/
    part-0000*.parquet
    _SUCCESS
```

---

## 5. Cómo reproducir los Steps si el EMR es eliminado

1. Crear un nuevo clúster EMR con Spark.  
2. Agregar Step 1 (ETL):

```
spark-submit --deploy-mode cluster --master yarn s3://vladdatalake/scripts/emr/etl_covid.py
```

3. Agregar Step 2 (Analytics):

```
spark-submit --deploy-mode cluster --master yarn s3://vladdatalake/scripts/emr/analytics_covid.py
```

---

## 6. Estructura esperada del S3

```
vladdatalake/
  raw/
    rds/covid_complement/
  processed/
    covid/
  analytics/
    covid/
  scripts/
    emr/
      etl_covid.py
      analytics_covid.py
```

---

## 7. Logs del EMR

Todos los logs se guardan automáticamente en:

```
s3://vladdatalake/emr-logs/<cluster-id>/steps/<step-id>/
```

Incluyendo:
- stdout.gz  
- stderr.gz  
- controller.gz  

---
