import jinja2


def ppjson(value, indent=2):
    """Jinja2 filter for pretty-printing JSON"""
    import json

    return json.dumps(value, indent=indent)


# Registers jinja2 filters
jinja2.filters.FILTERS['ppjson'] = ppjson
