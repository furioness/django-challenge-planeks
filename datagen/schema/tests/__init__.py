class AssertBetweenMixin(object):
    def assertBetween(self, value, low, high):
        if not (low <= value <= high):
            raise AssertionError(f"{value} is not between {low} and {high}")
