# This file is a part of the AnyBlok / FastAPI
#
#    Copyright (C) 2026 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
"""Automatic REST CRUD router generator for AnyBlok models using Pydantic v2."""

from datetime import date, datetime, time
from typing import Any

from anyblok.registry import Registry
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, create_model
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    Time,
    inspect,
)

from anyblok_fastapi.fastapi import get_registry


def _sqla_to_py_type(col_type: Any) -> type[Any]:
    """Map a SQLAlchemy column type to a corresponding Python type."""
    if isinstance(col_type, Boolean):
        return bool
    if isinstance(col_type, Integer):
        return int
    if isinstance(col_type, Numeric | Float):
        return float
    if isinstance(col_type, DateTime):
        return datetime
    if isinstance(col_type, Date):
        return date
    if isinstance(col_type, Time):
        return time
    return str


def _cast_pk(model_cls: Any, pk_val: Any) -> Any:
    """Cast a URL parameter to the primary key's Python type."""
    pks = list(inspect(model_cls).primary_key)
    if not pks:
        return pk_val
    pk_col = pks[0]
    if isinstance(pk_col.type, Integer):
        try:
            return int(pk_val)
        except (ValueError, TypeError):
            return pk_val
    return pk_val


def generate_pydantic_models(
    model_cls: type[Any],
    exclude_columns: list[str] | None = None,
) -> dict[str, type[BaseModel]]:
    """Generate Read, Create, and Update Pydantic v2 models from an AnyBlok Model."""
    exclude = set(exclude_columns or [])
    mapper = inspect(model_cls)

    read_fields: dict[str, Any] = {}
    create_fields: dict[str, Any] = {}
    update_fields: dict[str, Any] = {}

    for col in mapper.columns:
        if col.name in exclude:
            continue
        py_type = _sqla_to_py_type(col.type)

        read_fields[col.name] = (py_type, ... if not col.nullable else None)

        if col.primary_key:
            continue

        has_default = (
            col.nullable
            or col.default is not None
            or getattr(col, "server_default", None) is not None
        )
        if has_default:
            create_fields[col.name] = (py_type | None, None)
        else:
            create_fields[col.name] = (py_type, ...)

        update_fields[col.name] = (py_type | None, None)

    name = model_cls.__name__
    config = ConfigDict(from_attributes=True)

    ReadModel = create_model(f"{name}Read", __config__=config, **read_fields)
    CreateModel = create_model(f"{name}Create", __config__=config, **create_fields)
    UpdateModel = create_model(f"{name}Update", __config__=config, **update_fields)

    return {
        "read": ReadModel,
        "create": CreateModel,
        "update": UpdateModel,
    }


def create_crud_router(
    model_name: str,
    prefix: str | None = None,
    tags: list[str] | None = None,
    exclude_columns: list[str] | None = None,
) -> APIRouter:
    """Generate a FastAPI CRUD APIRouter for an AnyBlok model."""
    route_prefix = prefix or f"/{model_name.lower().replace('.', '_')}"
    router = APIRouter(prefix=route_prefix, tags=tags or [model_name])

    schemas: dict[str, type[BaseModel]] = {}

    def _get_schemas(registry: Registry):
        nonlocal schemas
        if not schemas:
            model_cls = getattr(registry, model_name)
            schemas = generate_pydantic_models(
                model_cls, exclude_columns=exclude_columns
            )
        return schemas

    @router.get("/", response_model=list[Any])
    def list_records(
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        registry: Registry = Depends(get_registry),
    ):
        model_cls = getattr(registry, model_name)
        schema = _get_schemas(registry)["read"]
        records = model_cls.query().offset(offset).limit(limit).all()
        return [schema.model_validate(r) for r in records]

    @router.get("/{id}", response_model=Any)
    def get_record(
        id: Any,
        registry: Registry = Depends(get_registry),
    ):
        model_cls = getattr(registry, model_name)
        schema = _get_schemas(registry)["read"]
        cast_id = _cast_pk(model_cls, id)
        record = model_cls.query().filter(model_cls.id == cast_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found",
            )
        return schema.model_validate(record)

    @router.post("/", response_model=Any, status_code=status.HTTP_201_CREATED)
    def create_record(
        payload: dict[str, Any],
        registry: Registry = Depends(get_registry),
    ):
        model_cls = getattr(registry, model_name)
        _get_schemas(registry)
        record = model_cls.insert(**payload)
        registry.flush()
        schema = schemas["read"]
        return schema.model_validate(record)

    @router.put("/{id}", response_model=Any)
    def update_record(
        id: Any,
        payload: dict[str, Any],
        registry: Registry = Depends(get_registry),
    ):
        model_cls = getattr(registry, model_name)
        cast_id = _cast_pk(model_cls, id)
        record = model_cls.query().filter(model_cls.id == cast_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found",
            )
        for key, val in payload.items():
            if hasattr(record, key):
                setattr(record, key, val)
        registry.flush()
        schema = _get_schemas(registry)["read"]
        return schema.model_validate(record)

    @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_record(
        id: Any,
        registry: Registry = Depends(get_registry),
    ):
        model_cls = getattr(registry, model_name)
        cast_id = _cast_pk(model_cls, id)
        record = model_cls.query().filter(model_cls.id == cast_id).first()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found",
            )
        record.delete()
        registry.flush()

    return router
