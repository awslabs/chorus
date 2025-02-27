"""
Helper functions and model classes for working with JSON Schema.
"""

from enum import Enum
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from pydantic import BaseModel
from pydantic import Field

JsonData = Optional[Union[str, int, float, bool, List[Any], Dict[str, Any]]]


class JsonTypes(str, Enum):
    """
    JSON Schema types (https://json-schema.org/understanding-json-schema/reference/type.html).
    """

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    OBJECT = "object"
    ARRAY = "array"
    BOOLEAN = "boolean"
    NULL = "null"


class StringFormats(str, Enum):
    """
    String built-in formats (https://json-schema.org/understanding-json-schema/reference/string.html#built-in-formats).
    """

    # dates and times
    DATE_TIME = "date-time"  # 2018-11-13T20:20:39+00:00
    TIME = "time"  # 20:20:39+00:00
    DATE = "date"  # 2018-11-13
    DURATION = "duration"  # P3DT1M --> 3 days and 1 minute (https://datatracker.ietf.org/doc/html/rfc3339#appendix-A)
    # email addresses
    EMAIL = "email"
    IDN_EMAIL = "idn-email"
    # host names
    HOSTNAME = "hostname"
    IDN_HOSTNAME = "idn-hostname"
    # ip addresses
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    # resource identifiers
    UUID = "uuid"
    URI = "uri"
    URI_REFERENCE = "uri-reference"
    IRI = "iri"
    IRI_REFERENCE = "iri-reference"
    # URI template
    URI_TEMPLATE = "uri-template"
    # JSON pointer
    JSON_POINTER = "json-pointer"
    RELATIVE_JSON_POINTER = "relative-json-pointer"
    # regular expressions
    REGEX = "regex"


class JsonSchema(BaseModel):
    """
    2020-12 JSON Schema specification (https://json-schema.org/specification.html).
    See https://json-schema.org/understanding-json-schema/index.html for more details.
    """

    # type, either `string`, `number` (int/float), `integer`, `object`, `array`, `boolean` or `null`
    data_type: Optional[Union[JsonTypes, List[JsonTypes]]] = Field(default=None, alias="type")

    # human-readable name for instances described by the schema
    title: Optional[str] = None
    # human-readable description of the purpose of the instance described by this schema
    description: Optional[str] = None
    # default used as a hint about how to create an instance
    default: Optional[Any] = None
    # chorus_examples of valid JSON values that validate against this schema
    examples: Optional[List[Any]] = None

    # ----- validation keywords available for all types ------
    # used to restrict a value to a fixed set of values (must contain at least one element, may accept different types)
    enum: Optional[List[Any]] = None
    # used to restrict to one valid value
    const: Optional[Any] = None

    # ----- meta-data annotations added for completeness, but are unlikely to be used -----
    # if True, indicates applications should refrain from using this parameter
    deprecated: Optional[bool] = None
    # indicates that the value should not be modified (e.g. PUT requests will result in 400)
    read_only: Optional[bool] = Field(default=None, alias="readOnly")
    # indicates the value may be set, but will remain hidden (e.g. can PUT but not subsequently GET)
    write_only: Optional[bool] = Field(default=None, alias="writeOnly")

    # ----- string-specific keywords -----
    min_length: Optional[int] = Field(default=None, alias="minLength")
    max_length: Optional[int] = Field(default=None, alias="maxLength")
    # restrict to a particular regular expression
    pattern: Optional[str] = None
    # semantic identification of basic string types (e.g. date, email, uuid, etc.)
    format: Optional[StringFormats] = None

    # ----- numeric-specific keywords -----
    multiple_of: Optional[int] = Field(default=None, alias="multipleOf")

    minimum: Optional[int] = None
    maximum: Optional[int] = None
    exclusive_minimum: Optional[bool] = Field(default=None, alias="exclusiveMinimum")
    exclusive_maximum: Optional[bool] = Field(default=None, alias="exclusiveMaximum")

    # ----- object-specific keywords -----
    # key-value pairs on an object
    properties: Optional[Dict[str, "JsonSchema"]] = None
    # validation for parameters whose names are matched with regex
    pattern_properties: Optional[Dict[str, "JsonSchema"]] = Field(
        default=None, alias="patternProperties"
    )
    # if false, no additional properties are allowed
    additional_properties: Optional[Union["JsonSchema", bool]] = Field(
        default=None, alias="additionalProperties"
    )
    # list of required properties
    required: Optional[List[str]] = Field(default_factory=list)
    # property name validation against regex
    property_names: Optional["JsonSchema"] = Field(default=None, alias="propertyNames")
    # minimum and maximum number of properties allowed
    min_properties: Optional[int] = Field(default=None, alias="minProperties")
    max_properties: Optional[int] = Field(default=None, alias="maxProperties")

    # ----- array-specific keywords -----
    # item validation (e.g. for a list where position does not have particular semantics)
    items: Optional[Union["JsonSchema", bool]] = (
        None  # when False, disallows additional items beyond `prefix_items`
    )
    # used to validate that the array contains one of the supplied schema
    contains: Optional["JsonSchema"] = None
    # specify how many times a schema should match a `contains` constraint
    min_contains: Optional[int] = Field(default=None, alias="minContains")
    max_contains: Optional[int] = Field(default=None, alias="maxContains")
    # tuple validation (where ordinal index is meaningful)
    prefix_items: Optional[List["JsonSchema"]] = Field(default=None, alias="prefixItems")
    # length of array
    min_items: Optional[int] = Field(default=None, alias="minItems")
    max_items: Optional[int] = Field(default=None, alias="maxItems")
    # uniqueness of elements in the array
    unique_items: Optional[bool] = Field(default=None, alias="uniqueItems")

    # ----- schema composition keywords -----
    all_of: Optional[List["JsonSchema"]] = Field(default=None, alias="allOf")
    one_of: Optional[List["JsonSchema"]] = Field(default=None, alias="oneOf")
    any_of: Optional[List["JsonSchema"]] = Field(default=None, alias="anyOf")
    not_of: Optional[List["JsonSchema"]] = Field(default=None, alias="not")
