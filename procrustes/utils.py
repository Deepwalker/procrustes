# (c) Svarga project under terms of the new BSD license


def pop_prefixed_args(data, prefix):
    res = {}
    for key in data.keys():
        if key.startswith(prefix):
            res[key[len(prefix):]] = data.pop(key)
    return res

