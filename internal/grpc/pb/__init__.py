import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from .babata_openai_pb2 import *  # noqa
from .babata_openai_pb2_grpc import *  # noqa
