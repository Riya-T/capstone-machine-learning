```python file=records.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ValidationError(Exception):
    pass


class RecordStore:
    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        self.records: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1
        self.load()

    def load(self):
        if self.path.exists():
            with self.path.open("r") as file:
                data = json.load(file)
                self.records = data.get("records", {})
                self.next_id = data.get("next_id", 1) + 1

    def save(self):
        with self.path.open("w") as file:
            json.dump({"records": self.records, "next_id": self.next_id}, file)

    def validate_record(self, record: Dict[str, Any]) -> None:
        if not isinstance(record, dict):
            raise ValidationError("Record must be a dictionary")
        if len(record) != 3:
            raise ValidationError("Record must have exactly three fields")
        if not all(key in record for key in ["name", "email", "age"]):
            raise ValidationError("Record must have 'name', 'email', and 'age' fields")
        if not isinstance(record["name"], str) or len(record["name"]) > 100:
            raise ValidationError("Name must be a string of 1 to 100 characters")
        if not isinstance(record["email"], str) or "@" not in record["email"]:
            raise ValidationError("Email must be a string containing exactly one '@'")
        if not isinstance(record["age"], int) or record["age"] < 0 or record["age"] > 150:
            raise ValidationError("Age must be an integer from 0 to 150 inclusive")

    def add(self, record: Dict[str, Any]) -> int:
        self.validate_record(record)
        record_id = self.next_id
        self.records[record_id] = {
            key: value for key, value in record.items() if key in ["name", "email", "age"]
        }
        self.next_id += 1
        self.save()
        return record_id

    def get(self, record_id: int) -> Dict[str, Any]:
        if record_id not in self.records:
            raise KeyError(f"Record with id {record_id} not found")
        return self.records[record_id].copy()

    def update(self, record_id: int, fields: Dict[str, Any]) -> None:
        if record_id not in self.records:
            raise KeyError(f"Record with id {record_id} not found")
        for field, value in fields.items():
            if field not in ["name", "email", "age"]:
                raise ValidationError(f"Invalid field: {field}")
        self.validate_record({**self.records[record_id], **fields})
        self.records[record_id].update(fields)
        self.save()

    def delete(self, record_id: int) -> None:
        if record_id not in self.records:
            raise KeyError(f"Record with id {record_id} not found")
        del self.records[record_id]
        self.save()

    def list_ids(self) -> List[int]:
        return sorted(self.records.keys())
```
