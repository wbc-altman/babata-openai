default: format


format:
	black .
	ruff format .
	ruff check --fix .

http-serve:
	uvicorn --host 0.0.0.0 --port 3000 --loop uvloop api.main:app

grpc-serve:
	python -m internal.grpc.main

test:
	pytest tests

proto:
	dir=internal/grpc/pb && \
	python -m grpc_tools.protoc -I=$${dir} --python_out=$${dir} --grpc_python_out=$${dir} --mypy_out=$${dir} --mypy_grpc_out=$${dir} $${dir}/babata_openai.proto
