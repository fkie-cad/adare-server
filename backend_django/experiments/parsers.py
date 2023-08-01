import copy

from rest_framework import parsers
import json


class MultiPartJSONParser(parsers.MultiPartParser):
    """
        Parses JSON-serialized data in multipart/form-data requests.
    """

    def parse(self, stream, *args, **kwargs):
        data = super().parse(stream, *args, **kwargs)

        data_data = copy.copy(data.data)

        for key, value in data.data.items():
            if key == 'metadata' and isinstance(value, str) and value.startswith('{'):
                data_data = json.loads(value)

        new_data = copy.copy(data)
        new_data.data = data_data

        return new_data
