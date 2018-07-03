import factory


def dump_random_state():
    """
    Dump factory's random state.  This is useful for debugging flaky tests.
    If a test fails, use set_random_state to try to reproduce it
    """
    print("Dumping random state: {}".format(factory.random.get_random_state()))
