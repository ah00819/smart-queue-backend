from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.utils.translation import ngettext_lazy
from django.utils.deconstruct import deconstructible


# later instead use pillow to compress and store the image
def validate_file_size(file):
    max_size_kb = 800

    if file.size > max_size_kb * 1024:
        raise ValidationError(f"Files cannot be larger than {max_size_kb}KB!")


@deconstructible
class ExactLengthValidator(BaseValidator):
    message = ngettext_lazy(
        "Ensure this value has exactly %(limit_value)d character (it has %(show_value)d).",
        "Ensure this value has exactly %(limit_value)d characters (it has %(show_value)d).",
        "limit_value",
    )
    code = "exact_length"

    def compare(self, a, b):
        return a != b

    def clean(self, x):
        return len(x)
