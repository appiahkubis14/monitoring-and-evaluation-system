from enum import Enum


class genderType(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class vehicleTypes(Enum):
    HATCHBACK = "hatchback"
    PICKUP = "pickup"
    SUV = "suv"
    SEDAN = "sedan"
    THREE_WHEELER = "three wheeler"
    TRAILER = "trailer"
    TRAILER_HEAD = "trailer_head"
    TRUCK = "truck"
    TWO_WHEELER = "two wheeler"

class vehicleDocuments(Enum):
    INSURANCE = "insurance"
    ROAD_WORTHINESS = "road worthiness"
    REGISTRATION_CERTIFICATE = "registration certificate"

class jobStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in progress"
    
class units(Enum):
    EACH = "each"
    KG =  "kg"
    LTR = "ltr"
    PERCENTAGE = "percentage"

class status(Enum):
    CLOSED = "closed"
    ISSUED = "issued"

class jobType(Enum):
    COCOA_DEPOT_PORT = "cocoa depot to port"
    COCOA_PORT_CPC = "cocoa port to cpc"
    FERTILIZER_COCOBOD = "fertilizer - cocobod"
    OTHERS = "others"

class parameterType(Enum):
    MICROBIOLOGY = "microbiology"
    PHYSIO_CHEMICAL = "physio chemical"
    SENSORY = "sensory"
    VISUAL  = "visual"

class parameterClass(Enum):
    CONSTANT = "constant"
    EXPRESSION = "expression"
    VALUE = "value"

class valueType(Enum):
    TEXT = "text"
    NUMERIC = "numeric"

class testStandard(Enum):
    ISO21527 = "ISO21527"
    ISO21528 = "ISO21528"
    ISO6888  = "ISO6888"