gitsync:
	@git pull upstream master --tags && git push origin master --tags
.PHONY: gitsync
