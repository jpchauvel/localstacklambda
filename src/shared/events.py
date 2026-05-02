from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class OrderItem(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(ge=Decimal("0"))


class OrderCreated(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    order_id: str = Field(min_length=1, max_length=64)
    customer_id: str = Field(min_length=1, max_length=64)
    amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    items: list[OrderItem] = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("currency")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.upper()

    def to_eventbridge_detail(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_eventbridge_detail(cls, detail: dict | str) -> OrderCreated:
        if isinstance(detail, str):
            return cls.model_validate_json(detail)
        return cls.model_validate(detail)
