"""
# extension module

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com
@created: 2017-02-20
@updated: 2018-01-23 (for python 3)

"""
import hashlib
import json
import os
import re
import jsonpickle

from clsfr.utils.logger import get_logger

LOGGER = get_logger(__name__)


class DictEncoder(json.JSONEncoder):
    """
    Default encoder for json.dumps
    """
    def default(self, o):  # pylint: disable=method-hidden
        """default encoder"""
        return o.__dict__


class JsonEncoder(json.JSONEncoder):
    """
    Default encoder for python set. Example: json.dumps(obj, cls=JsonEncoder)
    """
    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, set):
            return list(o)
        return o.__dict__


def check_duplicate_key(pairs):
    """
    Check duplicate key in pairs
    """
    result = dict()
    for key, val in pairs:
        if key in result:
            raise KeyError("Duplicate key specified: %s" % key)
        result[key] = val
    return result


# noinspection PyTypeChecker
def check_valid_md5(data):
    """
    Check if input data is a valid md5 hash string
    """
    if not isinstance(data, str):
        return False
    # note: some other regular expressions -
    #       r'\b[a-f\d]{32}\b|\b[A-F\d]{32}\b'
    #       r'(?i)(?<![a-z0-9])[a-f0-9]{32}(?![a-z0-9])'
    reiter = re.finditer(r'\b(?!^[\d]*$)(?!^[a-fA-F]*$)([a-f\d]{32}|[A-F\d]{32})\b', data)
    result = [match.group(1) for match in reiter]
    return bool(result)


def del_attr(obj, attr):
    """
    Delete an attribute from object, or a key from dict, if exists.
    """
    value = None
    if isinstance(attr, int):
        if isinstance(obj, list) and attr < len(obj) and attr >= 0:
            # LOGGER.debug('deleting index [%s] of %s', attr, obj)
            value = obj[attr]
            del obj[attr]
    elif isinstance(attr, str):
        if isinstance(obj, dict) and attr in obj:
            # LOGGER.debug('deleting key [%s] of %s', attr, obj)
            value = obj[attr]
            del obj[attr]
        elif hasattr(obj, attr):
            # LOGGER.debug('deleting attr [%s] of %s', attr, obj)
            value = getattr(obj, attr)
            delattr(obj, attr)
    elif isinstance(attr, list) and len(attr) > 0:
        if len(attr) > 1:
            prop = get_attr(obj, attr[0])
            return del_attr(prop, attr[1:])
        else:
            prop = attr[0]
            # LOGGER.debug('deleting attr [%s] of %s', prop, obj)
            return del_attr(obj, prop)
    else:
        value = None
        # LOGGER.debug('cannot delete `%s` of %s', attr, obj)
    return value


def get_attr(obj, *args):
    """
    Get nested attributes
    """
    data = obj
    for key in args:
        if not isinstance(data, dict) and hasattr(data, '__dict__'):
            data = data.__dict__
        # noinspection PyTypeChecker
        # LOGGER.debug('getting key [%s] of %s', key, data)
        if isinstance(key, str) and isinstance(data, dict):
            data = data.get(key, None)
        elif isinstance(key, int) and isinstance(data, list):
            data = data[key] if key >= 0 and key < len(data) else None
        else:
            data = None  # bad key type
    # LOGGER.debug('returning data: %s', data)
    return data


def get_camel_title_word(target_str, keep_capitals=True):
    """
    Get camel title (each word starts with upper case letter)
    Note:
        Use `keep_capitals=False` converting "One USA" to "OneUsa"
    """
    str_words = re.sub(r'[^\w\s]', ' ', str(target_str)).replace('_', ' ')
    if keep_capitals:
        str_words = ' '.join(
            w if w.isupper() else w.title() for w in str_words.split())
    else:
        str_words = ' '.join(
            w if len(w) == 1 else w.capitalize() for w in str_words.split())
    return str_words.replace(' ', '')


def get_hash(string_input="", salt="", hash_type="sha256", large_size=1024 * 1024 * 1024):
    """
    Get hash for @string_input, with @salt, by one of following hash types
        md5, sha1, sha256, sha512, or <file> (using sha256 for <file>)
    """
    # noinspection PyTypeChecker,PyTypeChecker
    if not isinstance(string_input, str) or \
       not isinstance(salt, str) or not string_input:
        return ""

    hash_default = hashlib.sha256
    hash_methods = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hash_default,
        "sha512": hashlib.sha512,
        "<file>": hash_default,
    }
    hash_func = hash_methods.get(str(hash_type).lower(), hash_default)
    file_path = string_input
    # file_size = 0

    data = string_input
    if hash_type == "<file>":
        data = ""
        try:
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                if file_size >= large_size:  # in bytes
                    with open(file_path, 'rb') as data_file:
                        for chunk in iter(lambda: data_file.read(4096), b""):
                            hash_func().update(chunk)
                    result = hash_func().hexdigest()
                    return result
                with open(file_path, 'rb') as data_file:
                    data = data_file.read()
        except Exception as ex:
            print("Error: {}".format(ex))
            return ""

    content = (salt + str(data)).encode('utf-8')
    return hash_func(content).hexdigest() if data else ""


def get_json(obj, indent=4):
    """
    Get formatted JSON dump string
    """
    return json.dumps(obj, sort_keys=True, indent=indent)


def pickle_object(obj, *rm_keys):
    """
    Convert an object to serialized JSON object
    """
    json_obj = json.loads(jsonpickle.encode(obj))

    for key in rm_keys:
        json_obj.pop(key, None)

    return json_obj


def pickle_to_str(obj, *rm_keys):
    """
    Convert an object to JSON string of serialized JSON object
    """
    json_obj = pickle_object(obj, *rm_keys)

    return json.dumps(json_obj)
