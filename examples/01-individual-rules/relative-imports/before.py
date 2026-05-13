"""Example file with relative imports that should be converted to absolute."""

from ..models import User as UserModel
from .utils import *
from .utils import helper_function


def process_user(user_id):
    """Process a user."""
    user = UserModel(user_id)
    result = helper_function(user)
    return result


class Processor:
    """Processor class with relative imports."""

    def __init__(self):
        from ..core import BaseProcessor

        self.base = BaseProcessor()

    def process(self):
        from .utils import format_data

        return format_data(self.base.data)
