TEST ?= ""

PHONY: get_requirements messages tests unit_tests func_tests serve serve_init_db

get_requirements:
	./weblib/static/get_requirements.sh

messages:
	./script/make_messages.sh

tests:
	./script/test.sh tests $(TEST)

unit_tests:
	./script/test.sh unit $(TEST)

func_tests:
	./script/test.sh func $(TEST)

serve:
	./script/serve.sh

serve_create_db:
	./script/serve.sh create_db

serve_init_db:
	./script/serve.sh init_db

tag:
	./script/tag.sh
