from django.db import models
import json
import gzip


def compress_serialize(value, compresslevel=9):
    """
    1. Dumps using JSON
    2. encode as byte string using UTF-8
    3. compress using gzip
    :param value:
    :return:
    """
    value = json.dumps(value)
    value = value.encode(encoding='UTF-8', errors='strict')
    value = gzip.compress(value, compresslevel=compresslevel)
    return value


def decompress_deserialize(value):
    """
    1. decompress
    2. decode from bytes to string
    3. load using json
    :param value:
    :return:
    """
    value = gzip.decompress(value)
    value = value.decode(encoding='UTF-8', errors='strict')
    value = json.loads(value)
    return value


class CompressedJSONField(models.BinaryField):
    """
    Serializes the stored value as JSON and then compresses it.
    Stores it as binary field.

    https://gist.github.com/tomfa/665f8a655a9218e0b4e9bd394d459934
    """

    def from_db_value(self, value, expression, connection):
        """
        Converting values to Python objects.
        :param value:
        :param expression:
        :param connection:
        :return:
        """
        if value is None:
            return value

        return decompress_deserialize(value)

    def to_python(self, value):
        """
        Converting values to Python objects.
        :param value:
        :return:
        """
        if type(value) is not bytes:
            return value

        return decompress_deserialize(value)

    def pre_save(self, model_instance, add):
        """
        Converting Python objects to query values
        :param value:
        :param connection:
        :param prepared:
        :return:
        """
        value = getattr(model_instance, self.attname)

        return compress_serialize(value)
