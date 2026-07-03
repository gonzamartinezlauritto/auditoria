# Sistema de Auditoría de Quiniela

Sistema desarrollado para la auditoría automática de sorteos de quiniela mediante el procesamiento de archivos **EXP**, **DBF** y resultados oficiales.

El sistema permite validar que los premios calculados localmente coincidan con los premios entregados por la empresa.

---

# Características

- Procesamiento masivo de archivos EXP.
- Procesamiento de archivos DBF oficiales.
- Descompresión automática de archivos ZIP.
- Soporte para los cinco turnos diarios.
- Cálculo automático de premios.
- Comparación con archivos oficiales.
- Resumen diario.
- Control de estados de auditoría.
- Alto rendimiento mediante COPY de PostgreSQL.

---

# Tecnologías

- Python 3.12
- FastAPI
- PostgreSQL
- psycopg2
- dbfread
- uvicorn

---

# Instalación

## Clonar proyecto

```bash
git clone <repositorio>
```

## Crear entorno virtual

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux

```bash
source venv/bin/activate
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

---

# Ejecutar proyecto

```bash
uvicorn app.main:app --reload
```

Swagger

```
http://127.0.0.1:8000/docs
```

---

# Flujo operativo

El flujo diario de trabajo es el siguiente.

```
EXP
     ↓

Resultados Oficiales
     ↓

DBF de Aciertos
     ↓

Cálculo
     ↓

Resumen Diario
```

---

# Organización de archivos

```
uploads/

    20260629/

        PV/

            exp/

                O260629PV_TS.zip
                quiniela.exp

            dbf/

                Aciertos260629PV_TS.zip
                Aciertos260629PV.dbf

        PR/

        M/

        V/

        N/
```

---

# Turnos soportados

| Turno | Descripción |
|--------|-------------|
| PV | La Previa |
| PR | Primera |
| M | Matutina |
| V | Vespertina |
| N | Nocturna |

---

# Extractos

## La Previa

50 Corrientes

51 Ciudad B.A.

52 Buenos Aires

53 Santa Fe

54 Córdoba

55 Entre Ríos

56 Chaqueña

---

## Primera

30 Corrientes

31 Ciudad B.A.

32 Buenos Aires

33 Santa Fe

42 Córdoba

46 Entre Ríos

57 Chaqueña

---

## Matutina

4 Corrientes

3 Ciudad B.A.

5 Buenos Aires

34 Santa Fe

43 Córdoba

47 Entre Ríos

59 Chaqueña

---

## Vespertina

7 Corrientes

8 Ciudad B.A.

9 Buenos Aires

35 Santa Fe

44 Córdoba

48 Entre Ríos

58 Chaqueña

---

## Nocturna

1 Corrientes

2 Ciudad B.A.

6 Buenos Aires

36 Santa Fe

40 Misiones

45 Córdoba

49 Entre Ríos

60 Chaqueña

---

# Endpoints

## EXP

### Cargar ZIP

```
POST /exp/process-zip
```

Parámetros

```
fecha
turno
file
```

---

## Resultados

```
POST /resultados/cargar
```

---

## DBF

```
POST /dbf/process-zip
```

---

## Cálculo

```
POST /calculo/run
```

---

## Resumen

```
GET /calculo/resumen?fecha=YYYYMMDD
```

---

## Estado

```
GET /auditoria/estado?fecha=YYYYMMDD
```

---

# Estados del proceso

Cada turno mantiene el siguiente estado.

- EXP cargado
- Resultados cargados
- DBF cargado
- Cálculo ejecutado

Ejemplo

```
29/06/2026

PV ✅
PR ✅
M ⏳
V ❌
N ❌
```

---

# Rendimiento

Prueba realizada con un archivo real.

```
777.791 apuestas
72 MB
```

Tiempo promedio

```
COPY PostgreSQL........1.5 segundos

Inserción.............24 segundos

Total.................26 segundos
```

---

# Base de datos

Tablas principales

- quiniela_exp
- resultados
- premios
- aciertos_dbf
- resumen_auditoria
- auditoria_cargas

---

# Proceso interno

```
ZIP EXP
      ↓

Descompresión automática

      ↓

quiniela.exp

      ↓

COPY PostgreSQL

      ↓

quiniela_exp

      ↓

Carga Resultados

      ↓

Carga DBF

      ↓

Motor de cálculo

      ↓

Resumen Auditoría
```

---

# Autor

Sistema desarrollado para la auditoría de sorteos de quiniela utilizando Python, FastAPI y PostgreSQL.