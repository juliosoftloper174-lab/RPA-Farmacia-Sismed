from time import sleep

from uiautomation import ComboBoxControl, ControlType

sleep(3)
cbo_dato = ComboBoxControl(Name="CboDato")
print(cbo_dato)

combo = cbo_dato
children = combo.GetChildren()
items = tuple(
    child for child in children if child.ControlType == ControlType.ListItemControl
)
selected = tuple(
    item.Name.strip() for item in items if item.GetSelectionItemPattern().IsSelected
)
if len(selected) != 1:
    raise RuntimeError("Exactly one item should be selected")

selected_label = selected[0]

print(selected_label)  # -> "CONTADO"

pass
