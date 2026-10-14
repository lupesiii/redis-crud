from typing import Annotated, Optional
from pydantic import BaseModel, Field, BeforeValidator, ConfigDict
from models.Vendedor import VendedorProduto


class Produto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Annotated[str, BeforeValidator(str)] | None = Field(default=None, alias="_id")
    nome: str
    descricao: str
    precoEmCentavos: int = Field(ge=0)
    estoque: int = Field(ge=0)
    imagem: str
    vendedor: VendedorProduto


class ProdutoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Optional[str] = None
    descricao: Optional[str] = None
    precoEmCentavos: Optional[int] = Field(default=None, ge=0)
    estoque: Optional[int] = Field(default=None, ge=0)
    imagem: Optional[str] = None
