import importlib.util


def has_mod(name):
    return importlib.util.find_spec(name) is not None


print("has_sentencepiece", has_mod("sentencepiece"))
print("has_protobuf", has_mod("google.protobuf"))
print("has_tiktoken", has_mod("tiktoken"))

try:
    import transformers

    print("transformers", transformers.__version__)
    from transformers.utils.import_utils import (
        is_sentencepiece_available,
        is_protobuf_available,
    )

    print("is_sentencepiece_available", is_sentencepiece_available())
    print("is_protobuf_available", is_protobuf_available())
except Exception as e:
    print("transformers_check_error", repr(e))
