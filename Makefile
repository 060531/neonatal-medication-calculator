.RECIPEPREFIX := >
APP=app.py
DB=instance/app.db
SHELL=/bin/sh

.PHONY: current check uniq sanity

current:
> FLASK_APP=$(APP) flask db current -v

check:
> sqlite3 $(DB) < scripts/check.sql

uniq:
> FLASK_APP=$(APP) flask shell < scripts/test_unique.py

sanity: current check uniq
