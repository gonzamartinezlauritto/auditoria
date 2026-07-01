# CHANGELOG

Todos los cambios importantes del proyecto serán documentados en este archivo.

---

# [1.0.0] - En desarrollo

## Arquitectura

* Creación de la estructura base del proyecto utilizando FastAPI.
* Organización por routers, services y base de datos.
* Configuración inicial de PostgreSQL.
* Creación de la estructura de uploads y reports.

---

## Base de datos

Se crearon las tablas principales del sistema:

* quiniela_exp
* resultados
* premios
* aciertos_dbf
* resumen_auditoria
* auditoria_cargas
* cargas_exp

---

## Carga de archivos EXP

Implementaciones realizadas:

* Lectura de archivos EXP.
* Procesamiento masivo mediante COPY de PostgreSQL.
* Uso de tabla temporal para optimizar la carga.
* Inserción mediante INSERT ... SELECT.
* Eliminación de duplicados utilizando ON CONFLICT DO NOTHING.
* Incorporación de archivo_origen.
* Incorporación de fecha_carga.
* Organización de archivos por fecha y turno.

---

## Procesamiento de archivos ZIP

Se agregó soporte para:

### EXP

* Recepción de ZIP externo.
* Descompresión automática.
* Lectura de ZIP interno.
* Extracción automática de quiniela.exp.

### DBF

* Recepción de ZIP.
* Descompresión automática.
* Extracción del archivo DBF.

---

## Resultados Oficiales

Se implementó:

* Carga de resultados oficiales.
* Asociación por fecha.
* Asociación por turno.
* Asociación por extracto.
* Validación de resultados.

---

## Motor de cálculo

Implementaciones:

* Premios normales.
* Aproximaciones.
* Redoblonas.
* Validación por líneas.
* Agrupación de premios.
* Cálculo de importes.
* Comparación con el sistema anterior.

---

## Comparación con archivos oficiales

Implementaciones:

* Lectura de archivos DBF.
* Comparación de apuestas premiadas.
* Comparación de cupones ganadores.
* Validación contra información oficial.

---

## Resúmenes

Se desarrollaron:

* Resumen por extracto.
* Resumen por turno.
* Resumen por fecha.

Se incorporó la tabla:

* resumen_auditoria

para evitar recálculos innecesarios.

---

## Control de estados

Se implementó:

* auditoria_cargas

Estados registrados:

* EXP cargado.
* Resultados cargados.
* DBF cargado.
* Cálculo ejecutado.

---

## APIs

Se desarrollaron los siguientes endpoints:

### EXP

* /exp/upload
* /exp/process
* /exp/process-zip

### DBF

* /dbf/process
* /dbf/process-zip

### Resultados

* /resultados

### Cálculo

* /calculo/run
* /calculo/resumen

### Auditoría

* /auditoria/estado

---

## Optimizaciones

* Uso de COPY PostgreSQL.
* Tabla temporal.
* ON CONFLICT DO NOTHING.
* Evita duplicados.
* Persistencia de resúmenes.
* Medición de tiempos de procesamiento.

---

## Rendimiento

Prueba realizada con archivo real:

* 777.791 apuestas.
* 72 MB.

Tiempo promedio:

* COPY: ~1,5 segundos.
* Inserción: ~24 segundos.
* Tiempo total: ~26 segundos.

---

## Documentación

Se incorporó:

* README.md
* CHANGELOG.md

---

## Estado del proyecto

Versión funcional lista para validación integral y preparación para producción.
