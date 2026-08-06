from pydantic import BaseModel, Field


class ResultadoExtractoRequest(BaseModel):
    codigo_extracto: int = Field(
        gt=0,
    )
    numeros: list[str] = Field(
        min_length=20,
        max_length=20,
    )


class CargarResultadosRequest(BaseModel):
    fecha: int = Field(
        gt=0,
    )
    turno: str = Field(
        min_length=1,
        max_length=10,
    )
    resultados: list[ResultadoExtractoRequest] = Field(
        min_length=1,
    )