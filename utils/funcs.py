from typing import List, Iterable
from datetime import datetime




class IDGenerator:
    counter = 0
    @classmethod
    def generate_unique_id(cls, prefix: str) -> str:
        cls.counter += 1
        counter_str = str(cls.counter).rjust(4, "0")
        now_suffix = datetime.now().strftime("%d%m%Y%H%M%S")
        return f"{prefix.upper()}{now_suffix}{counter_str}"


def get_object_choices(cls: Iterable) -> List[tuple]:
    return [(tag.value, tag.name) for tag in cls]