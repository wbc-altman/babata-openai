import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

protos = str(Path(__file__).parent / "protos")
sys.path.append(protos)


import grpc  # noqa

babata_openai_protos, babata_openai_services = grpc.protos_and_services(
    "protos/babata_openai.proto"
)
