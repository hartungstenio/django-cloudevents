"""Type aliases for subscription filter expressions.

This module defines the supported filter dialects and the corresponding
expression shapes used by the subscription layer.
"""

from collections.abc import Mapping
from typing import Literal, TypeAlias

FilterDialect: TypeAlias = Literal["exact", "prefix", "suffix", "all", "any", "not", "sql"]

ExactFilter: TypeAlias = Mapping[Literal["exact"], Mapping[str, str]]
PrefixFilter: TypeAlias = Mapping[Literal["prefix"], Mapping[str, str]]
SuffixFilter: TypeAlias = Mapping[Literal["suffix"], Mapping[str, str]]
AllFilter: TypeAlias = Mapping[Literal["all"], list["FilterExpression"]]
AnyFilter: TypeAlias = Mapping[Literal["any"], list["FilterExpression"]]
NotFilter: TypeAlias = Mapping[Literal["not"], "FilterExpression"]
SQLFilter: TypeAlias = Mapping[Literal["sql"], str]

FilterExpression: TypeAlias = ExactFilter | PrefixFilter | SuffixFilter | AllFilter | AnyFilter | NotFilter | SQLFilter
