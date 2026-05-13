"""Example file with relative imports converted to absolute."""

from mypackage.models import User as UserModel
from mypackage.utils import *
from mypackage.utils import helper_function


def process_user(user_id):
    """Process a user."""
    user = UserModel(user_id)
    result = helper_function(user)
    return result


class Processor:
    """Processor class with absolute imports."""

    def __init__(self):
        from mypackage.core import BaseProcessor

        self.base = BaseProcessor()

    def process(self):
        from mypackage.utils import format_data

        return format_data(self.base.data)
