.PHONY: All
$(VERBOSE).SILENT:
help:
	@echo "clean - removes all .pyc files"
	

clean:
	find . -type d -name __pycache__ -exec rm -r {} \+
