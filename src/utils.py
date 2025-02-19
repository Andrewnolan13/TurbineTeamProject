from typing import get_type_hints

def enforce_types(func):
    def wrapper(*args, **kwargs):
        hints = get_type_hints(func)
        # Enforce argument types
        for name, value in zip(func.__code__.co_varnames, args):
            if name in hints and not isinstance(value, hints[name]):
                raise TypeError(f"Argument {name} must be {hints[name]}, got {type(value).__name__}")

        # Call the function
        result = func(*args, **kwargs)

        # Enforce return type
        if "return" in hints and not isinstance(result, hints["return"]):
            raise TypeError(f"Return value must be {hints['return']}, got {type(result).__name__}")

        return result

    return wrapper