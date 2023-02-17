import hashlib
from typing import Optional, Union


def digest_input(input: Optional[Union[str, bytes]]) -> Optional[str]:
    digest = None
    # ignore input if None or if empty string
    if input:
        if isinstance(input, str):
            input = input.encode()
        hash = hashlib.md5(input)
        digest = hash.hexdigest()
    return digest
