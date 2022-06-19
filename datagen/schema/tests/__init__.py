class AssertBetweenMixin:
    @staticmethod
    def assertBetween(value, low, high):  # NOSONAR
        if not (low <= value <= high):
            raise AssertionError(f"{value} is not between {low} and {high}")
