import pytest
from fastapi import FastAPI
from fastapi._compat import v2
from pydantic import BaseModel, ConfigDict


class Leaf(BaseModel):
    model_config = ConfigDict(defer_build=True)

    name: str


class Branch(BaseModel):
    model_config = ConfigDict(defer_build=True)

    leaf: Leaf
    leaves: list[Leaf] = []


class Tree(BaseModel):
    branch: Branch
    other: Branch | None = None


app = FastAPI()


@app.post("/trees")
def create_tree(tree: Tree) -> Tree:
    return tree  # pragma: no cover


def test_openapi_does_not_create_model_fields_for_nested_models(
    monkeypatch: pytest.MonkeyPatch,
):
    created: list[v2.ModelField] = []
    original_post_init = v2.ModelField.__post_init__

    def tracking_post_init(self: v2.ModelField) -> None:
        created.append(self)
        original_post_init(self)

    monkeypatch.setattr(v2.ModelField, "__post_init__", tracking_post_init)
    app.openapi_schema = None
    schema = app.openapi()

    assert created == []
    assert set(schema["components"]["schemas"]) >= {"Tree", "Branch", "Leaf"}
    assert schema["components"]["schemas"]["Branch"]["properties"]["leaf"] == {
        "$ref": "#/components/schemas/Leaf"
    }
