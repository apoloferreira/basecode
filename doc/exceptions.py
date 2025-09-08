
class RecordNotFoundError(Exception):
    """Exception raised when a record does not exist in the table."""
    pass

class PrimaryKeyDuplicatedError(Exception):
    """Exception raised when a record is duplicated in the table."""
    pass
