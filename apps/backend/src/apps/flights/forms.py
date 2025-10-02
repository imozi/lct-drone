"""
Формы для приложения flights.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class ExcelUploadForm(forms.Form):
    """Форма для загрузки Excel файлов с планами полетов."""

    excel_file = forms.FileField(
        label=_("Excel файл"),
        help_text=_(
            "Загрузите Excel файл с данными о планах полетов. "
            "Поддерживаемые форматы: .xlsx, .xls. Максимальный размер: 50MB."
        ),
        widget=forms.FileInput(
            attrs={"accept": ".xlsx,.xls", "class": "form-control-file"}
        ),
    )

    def clean_excel_file(self):
        """Валидация загружаемого Excel файла."""
        excel_file = self.cleaned_data.get("excel_file")

        if not excel_file:
            raise ValidationError(_("Выберите файл для загрузки."))
        if excel_file.size > 52428800:
            raise ValidationError(_("Размер файла не должен превышать 50MB."))
        allowed_extensions = [".xlsx", ".xls"]
        file_extension = "." + excel_file.name.split(".")[-1].lower()

        if file_extension not in allowed_extensions:
            raise ValidationError(
                _(
                    "Неподдерживаемый формат файла. "
                    "Разрешены только файлы: .xlsx, .xls"
                )
            )

        return excel_file
