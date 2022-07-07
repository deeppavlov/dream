import copy


def make_name_string(dict_, final=False, do_epoch=False, set_epoch=None):
    if final:
        if not do_epoch:
            string = "{}_{}_{}".format(dict_.lr, dict_.optim, dict_.bs)
        elif set_epoch is not None:
            string = "{}_{}_{}_{}".format(dict_.lr, dict_.optim, dict_.bs, set_epoch)
        else:
            string = "{}_{}_{}_{}".format(dict_.lr, dict_.optim, dict_.bs, dict_.epoch)

        return string

    string = ""

    for k, v in dict_.items():
        if type(v) == DD:
            continue
        if isinstance(v, list):
            val = "#".join(is_bool(str(vv)) for vv in v)
        else:
            val = is_bool(v)
        if string:
            string += "-"
        string += "{}_{}".format(k, val)

    return string


def is_bool(v):
    check_is_bool = {"False": "F", "True": "T"}
    return check_is_bool.get(str(v), v)


# Taken from Jobman 0.1
class DD(dict):
    def __getattr__(self, attr):
        if attr == "__getstate__":
            return super(DD, self).__getstate__
        elif attr == "__setstate__":
            return super(DD, self).__setstate__
        elif attr == "__slots__":
            return super(DD, self).__slots__
        return self[attr]

    def __setattr__(self, attr, value):
        # Safety check to ensure consistent behavior with __getattr__.
        assert attr not in ("__getstate__", "__setstate__", "__slots__")
        #         if attr.startswith('__'):
        #             return super(DD, self).__setattr__(attr, value)
        self[attr] = value

    def __str__(self):
        return "DD%s" % dict(self)

    def __repr__(self):
        return str(self)

    def __deepcopy__(self, memo):
        z = DD()
        for k, kv in self.items():
            z[k] = copy.deepcopy(kv, memo)
        return z
