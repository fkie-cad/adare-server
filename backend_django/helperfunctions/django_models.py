def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def get_or_create(classmodel, get_dict: dict, create_dict: dict):
    obj = get_or_none(classmodel, **get_dict)
    if not obj:
        obj = classmodel.objects.create(**create_dict)
    return obj