from pydantic import BaseModel, ConfigDict, Field


class ResultadoExtractoRequest(BaseModel):
    codigo_extracto: int = Field(
        gt=0,
        description="Código identificador del extracto.",
        examples=[50],
    )

    numeros: list[str] = Field(
        min_length=20,
        max_length=20,
        description=(
            "Lista con exactamente 20 números sorteados, "
            "respetando el orden de salida del 1 al 20."
        ),
        examples=[
            [
                "3359",
                "4249",
                "6765",
                "2210",
                "5357",
                "4051",
                "6479",
                "5895",
                "9818",
                "7106",
                "8184",
                "0922",
                "3165",
                "1275",
                "2968",
                "7639",
                "0682",
                "6683",
                "9474",
                "2243",
            ]
        ],
    )


class CargarResultadosRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "fecha": 20260810,
                    "turno": "PV",
                    "resultados": [
                        {
                            "codigo_extracto": 50,
                            "numeros": [
                                "3359", "4249", "6765", "2210",
                                "5357", "4051", "6479", "5895",
                                "9818", "7106", "8184", "0922",
                                "3165", "1275", "2968", "7639",
                                "0682", "6683", "9474", "2243",
                            ],
                        },
                        {
                            "codigo_extracto": 51,
                            "numeros": [
                                "5603", "1545", "6242", "7770",
                                "0864", "3515", "8708", "4234",
                                "4161", "6774", "0453", "4564",
                                "8771", "1483", "6517", "7932",
                                "3418", "9920", "0969", "2054",
                            ],
                        },
                        {
                            "codigo_extracto": 52,
                            "numeros": [
                                "1741", "6331", "0931", "5727",
                                "0972", "8682", "2189", "8937",
                                "8887", "5818", "2303", "2124",
                                "0719", "3091", "1312", "4863",
                                "8789", "2778", "2645", "9750",
                            ],
                        },
                        {
                            "codigo_extracto": 53,
                            "numeros": [
                                "4233", "8215", "2918", "5443",
                                "0390", "8269", "0779", "3774",
                                "2177", "9787", "3455", "5307",
                                "0281", "4966", "3352", "1011",
                                "6753", "2421", "5090", "2442",
                            ],
                        },
                        {
                            "codigo_extracto": 54,
                            "numeros": [
                                "6778", "7082", "8416", "5737",
                                "9291", "8666", "2457", "7486",
                                "7231", "5318", "8352", "6886",
                                "3460", "7666", "8883", "7246",
                                "7577", "4966", "7103", "2758",
                            ],
                        },
                    ],
                }
            ]
        }
    )

    fecha: int = Field(
        gt=0,
        description="Fecha del sorteo en formato AAAAMMDD.",
        examples=[20260810],
    )

    turno: str = Field(
        min_length=1,
        max_length=10,
        description=(
            "Turno correspondiente al sorteo. "
            "Valores válidos: PV, PR, M, V o N."
        ),
        examples=["PV"],
    )

    resultados: list[ResultadoExtractoRequest] = Field(
        min_length=5,
        max_length=5,
        description=(
            "Los 5 extractos deben enviarse juntos "
            "en una única solicitud."
        ),
    )