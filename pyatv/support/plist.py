import biplist

from typing import (
    Any,
    Dict,
    Union,
)

def encode_plist_body(data: Any):
    """Encode a binary plist payload."""
    return biplist.writePlistToString(data)
    # return plistlib.dumps(
    #     data,
    #     fmt=plistlib.FMT_BINARY,  # pylint: disable=no-member
    # )


def decode_plist_body(body: Union[str, bytes, Dict[Any, Any]]) -> Any:
    """Decode a binary plist payload."""
    try:
        if isinstance(body, Dict):
            return body
        return biplist.readPlistFromString(body)
#        return plistlib.loads(body if isinstance(body, bytes) else body.encode("utf-8"))
#    except plistlib.InvalidFileException:
    except (biplist.InvalidPlistException, biplist.NotBinaryPlistException):
        return None