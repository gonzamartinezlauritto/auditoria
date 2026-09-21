from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class ReabrirEventoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "motivo": (
                    "Corrección de resultados "
                    "del extracto 52"
                )
            }
        }
    )

    motivo: str = Field(
        min_length=3,
        max_length=1000,
        description=(
            "Motivo por el cual se solicita "
            "la reapertura del evento."
        ),
        examples=[
            "Corrección de resultados del extracto 52"
        ],
    )