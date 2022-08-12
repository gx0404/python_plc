# package
# __init__.py
from enum import Enum
from snap7.types import Areas
from typing import Dict

io_type_dict: dict[str, Areas] = {"input": Areas.PE, "mw": Areas.MK, "m_bool": Areas.MK, "db": Areas.DB, "output": Areas.PA}
