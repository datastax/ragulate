from typing import Any, Dict, List, Optional

class Column:
    field: str | None
    children: Dict[str, "Column"]
    type: List[str]
    hide: bool | None
    width: int
    style: Dict[str, str] | None

    def __init__(
        self,
        field: Optional[str] = None,
        children: Optional[Dict[str, "Column"]] = None,
        type: Optional[List[str]] = None,
        hide: Optional[bool] = False,
        width: Optional[int] = 0,
        style: Optional[Dict[str, str]] = None,
    ):
        self.field = field
        self.children = children if children is not None else {}
        self.type = type if type is not None else []
        self.hide = hide
        self.width = width if width is not None else 0
        self.style = style

    def get_props(self, headerName: str) -> Dict[str, Any]:
        props: Dict[str, Any] = {
            "headerName": headerName,
            "field": self.field,
            "type": self.type,
        }
        if self.hide:
            props["hide"] = True
        if self.width > 0:
            props["width"] = self.width
        if self.style is not None:
            props["cellStyle"] = {k: v for k, v in self.style.items()}
        return props


def get_column_defs(columns: Dict[str, Column]) -> List[Dict[str, Any]]:
    columnDefs: List[Dict[str, Any]] = []

    for headerName, column in columns.items():
        if len(column.children) == 0:
            columnDefs.append(column.get_props(headerName=headerName))
        else:
            columnDefs.append(
                {
                    "headerName": headerName,
                    "children": get_column_defs(columns=column.children),
                }
            )
    return columnDefs