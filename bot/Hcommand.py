from functools import wraps

class Command:
    def __init__():
        print("WIP")

    def register(count):
        def true_register(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                for i in range(count):
                    print "Before decorated function"
                r = f(*args, **kwargs)
                for i in range(count):
                    print "After decorated function"
                return r
            return wrapped
        return true_register
