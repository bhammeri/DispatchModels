from itertools import chain


def to_dict(model_instance):
    meta = model_instance._meta

    data = {}

    for field in chain(meta.concrete_fields, meta.private_fields):
        data[field.name] = field.value_from_object(model_instance)

    for field in meta.many_to_many:
        data[field.name] = [rel.id for rel in field.value_from_object(model_instance)]

    return data