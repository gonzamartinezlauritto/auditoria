API_DESCRIPTION = """
API para el proceso de auditoría de quiniela.

## Flujo recomendado

1. **Autenticación**
   - Iniciar sesión mediante `POST /auth/login`.
   - Utilizar el token JWT obtenido en los endpoints protegidos.

2. **Carga del EXP**
   - Procesar el archivo EXP correspondiente a la fecha y turno.
   - Turnos válidos: `PV`, `PR`, `M`, `V` y `N`.
   - Los registros pertenecientes a turnos no válidos son ignorados.

3. **Carga de extractos**
   - Cargar los resultados oficiales mediante `POST /extractos/cargar`.
   - Deben enviarse los **5 extractos juntos**.
   - Cada extracto debe contener exactamente **20 números**.

4. **Cálculo**
   - Ejecutar `POST /calculo/run`.
   - El cálculo se realiza con el EXP y los extractos cargados.
   - El DBF no participa en el cálculo propio del sistema.

5. **Carga del DBF**
   - Procesar el archivo DBF de aciertos oficiales.
   - Puede cargarse directamente o desde un archivo ZIP.

6. **Comparación**
   - Ejecutar `POST /comparacion/run`.
   - Se compara el resultado calculado por el sistema contra el DBF.
   - Se controlan aciertos totales, por extracto, cupones únicos y diferencias.

7. **Auditoría**
   - Consultar `GET /auditoria/estado`.
   - Permite conocer el estado del flujo por fecha y turno.

8. **Reporte**
   - Consultar `GET /reporte/control-aciertos`.
   - El backend entrega los datos consolidados.
   - La generación visual/PDF queda a cargo del frontend.

## Roles

### ADMIN
Acceso completo, incluyendo administración de usuarios.

### OPERADOR
Puede ejecutar el flujo operativo de auditoría.

### CONSULTA
Puede consultar estados, resultados y reportes.

## Autenticación

Los endpoints protegidos requieren:

`Authorization: Bearer <token>`
"""


OPENAPI_TAGS = [
    {
        "name": "Sistema",
        "description": (
            "Información general y estado de disponibilidad de la API."
        ),
    },
    {
        "name": "Auth",
        "description": (
            "Autenticación y generación de tokens JWT."
        ),
    },
    {
        "name": "Usuarios",
        "description": (
            "Administración de usuarios del sistema."
        ),
    },
    {
        "name": "EXP",
        "description": (
            "Carga y procesamiento de archivos EXP con apuestas."
        ),
    },
    {
        "name": "Extractos",
        "description": (
            "Carga y consulta de resultados oficiales de extractos."
        ),
    },
    {
        "name": "Cálculo",
        "description": (
            "Cálculo propio de premios y resumen de resultados."
        ),
    },
    {
        "name": "DBF",
        "description": (
            "Carga de archivos DBF con aciertos oficiales."
        ),
    },
    {
        "name": "Comparación",
        "description": (
            "Comparación entre resultados calculados y DBF."
        ),
    },
    {
        "name": "Auditoría",
        "description": (
            "Consulta del estado general del proceso de auditoría."
        ),
    },
    {
        "name": "Reporte",
        "description": (
            "Datos consolidados para el Control de Aciertos."
        ),
    },
]