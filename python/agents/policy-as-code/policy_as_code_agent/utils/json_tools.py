def traverse(obj, sample_values, path=''):
    """
    Recursively traverses a JSON object to populate the sample_values dictionary.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f'{path}.{k}' if path else k
            traverse(v, sample_values, new_path)
    elif isinstance(obj, list):
        if obj:
            traverse(obj[0], sample_values, f'{path}[]')
    elif path not in sample_values:
        sample_values[path] = obj