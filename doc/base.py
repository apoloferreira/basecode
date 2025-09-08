import sys
import os
from abc import ABC, abstractmethod
from dataclasses import asdict
from pandas import DataFrame
from pyarrow import Table

sys.path.append(os.getcwd())
from exceptions import PrimaryKeyDuplicatedError


class Record(ABC):

    def to_dict(self) -> dict:
        return asdict(self)


class PATable(ABC):

    @property
    @abstractmethod
    def schema(self):
        pass

    def __init__(self) -> None:
        self.values: list[dict] = []

    def check_unique_id(self, record_id: str) -> None:
        ids = [record['id_poligono'] for record in self.values]
        if record_id in ids:
            raise PrimaryKeyDuplicatedError(f"Record with id '{record_id}' already exists.")

    def add_record(self, record: Record) -> None:
        record_dict = record.to_dict()
        self.check_unique_id(record_id=record_dict['id_poligono'])
        self.values.append(record_dict)

    def add_dataframe(self, df: DataFrame) -> None:
        for item in df.to_dict(orient="index").values():
            self.values.append(item)

    def clear(self) -> None:
        self.values = []

    def to_pyarrow_table(self) -> Table:
        return Table.from_pylist(
            self.values,
            schema=self.schema
        )
