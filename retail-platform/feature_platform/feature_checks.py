import math

def matching_records(actual,expected,key,fields):
    def index(records):
        result={}
        for row in records:
            identity=str(row[key])
            if identity in result:
                raise RuntimeError("Duplicate entity in retrieval evidence")
            result[identity]=row
        return result
    a,e=index(actual),index(expected)
    if set(a)!=set(e):
        raise RuntimeError("Retrieved entity keys differ from expected keys")
    for identity in e:
        for field in fields:
            av,ev=a[identity].get(field),e[identity].get(field)
            if ev is None:
                if av is not None:
                    raise RuntimeError("Future or unavailable feature unexpectedly present: "+field)
            elif av is None:
                raise RuntimeError("Missing feature: "+field)
            elif not(math.isfinite(float(av)) and math.isfinite(float(ev)) and
                     math.isclose(float(av),float(ev),rel_tol=1e-9,abs_tol=1e-6)):
                raise RuntimeError("Feature value mismatch: "+field)
