from __future__ import annotations

from html.parser import HTMLParser

from .models import FormField, FormQuestion, Option


class _FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.labels: dict[str, str] = {}
        self.controls: list[dict] = []
        self._label_for = ""
        self._label_parts: list[str] = []
        self._in_label = False
        self._select: dict | None = None
        self._option_parts: list[str] = []
        self._in_option = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag == "label":
            self._in_label = True
            self._label_for = data.get("for", "")
            self._label_parts = []
        elif tag == "option" and self._select is not None:
            self._in_option = True
            self._option_parts = []
            self._select.setdefault("_option_values", []).append(data.get("value", ""))
        elif tag in {"input", "textarea", "select"}:
            control = {
                "tag": tag,
                "id": data.get("id", ""),
                "name": data.get("name", "") or data.get("id", ""),
                "type": data.get("type", "text"),
                "required": "required" in data or data.get("aria-required") == "true",
                "class": data.get("class", ""),
                "role": data.get("role", ""),
            }
            self.controls.append(control)
            if tag == "select":
                self._select = control
                control["_option_values"] = []
                control["_option_labels"] = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "label" and self._in_label:
            text = " ".join("".join(self._label_parts).split())
            if self._label_for:
                self.labels[self._label_for] = text
            self._in_label = False
        elif tag == "option" and self._in_option and self._select is not None:
            self._select.setdefault("_option_labels", []).append(" ".join("".join(self._option_parts).split()))
            self._in_option = False
        elif tag == "select":
            self._select = None

    def handle_data(self, data: str) -> None:
        if self._in_label:
            self._label_parts.append(data)
        if self._in_option:
            self._option_parts.append(data)


def questions_from_html(html: str) -> tuple[FormQuestion, ...]:
    parser = _FormParser()
    parser.feed(html)
    questions: list[FormQuestion] = []
    for control in parser.controls:
        name = control["name"]
        if not name or control["type"] in {"hidden", "submit", "button"}:
            continue
        label = parser.labels.get(control["id"], "") or name
        required = control["required"] or "*" in label
        kind = "text"
        options: tuple[Option, ...] = ()
        if control["tag"] == "textarea":
            kind = "textarea"
        elif control["tag"] == "select":
            kind = "select"
            labels = control.get("_option_labels") or []
            values = control.get("_option_values") or []
            built = []
            for index, option_label in enumerate(labels):
                if not option_label or option_label.lower() == "select...":
                    continue
                value = values[index] if index < len(values) else option_label
                built.append(Option(value or option_label, option_label))
            options = tuple(built)
        elif control["type"] == "file":
            kind = "file"
        elif control["type"] == "checkbox":
            kind = "checkbox"
        elif "select__input" in control["class"] or control["role"] == "combobox":
            kind = "select"
        questions.append(FormQuestion(label.replace("*", "").strip(), required, (FormField(name, kind, options),)))
    return tuple(questions)
