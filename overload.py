_funcs = {}

def dispatch(*types, default=False):
    def dispatch(func):
        name = func.__module__+"."+func.__qualname__
        if name not in _funcs:
            _funcs[name] = [{}, None]
        if not default:
            _funcs[name][0][types] = func
        else:
            _funcs[name][1] = func
        def dispatch(*args, **kwargs):
            funcs = _funcs[name]
            for f in funcs[0]:
                if f != "default":
                    akws = (*args, *kwargs.values())
                    if all((isinstance(a, t) if t != None else True for t,a in zip(f, akws))):
                        return funcs[0][f](*args, **kwargs)
            if funcs[1]:
                return funcs[1](*args, **kwargs)
            raise NotImplementedError()
        return dispatch
    return dispatch
