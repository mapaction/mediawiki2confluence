PIPENVRUN  := pipenv run
SOURCE_DIR := m2c
TEST_DIR   := tests

gitsync:
	@git pull upstream master --tags && git push origin master --tags
.PHONY: gitsync

repl:
	@ipython -i $(SOURCE_DIR)/cli.py

lint:
	@$(PIPENVRUN) pylama $(SOURCE_DIR)
.PHONY: lint

sort:
	@find $(SOURCE_DIR) -name "*.py" | xargs $(PIPENVRUN) isort -c --diff -sp=setup.cfg
.PHONY: sort

test:
	@$(PIPENVRUN) pytest $(TEST_DIR)
.PHONY: test

proof: lint sort test
.PHONY: proof
