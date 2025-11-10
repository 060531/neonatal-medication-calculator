.PHONY: pages serve clean
pages:
	python tools/build_pages.py --src templates --out docs

serve:
	python -m http.server --directory docs 8000

clean:
	rm -rf docs/*
