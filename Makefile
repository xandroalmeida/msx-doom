PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PORT ?= 8765
ROM := build/posto-umbra.rom

.PHONY: site serve

$(ROM):
	$(PYTHON) tools/build.py

site: $(ROM)
	$(PYTHON) tools/build_site.py

serve: site
	@echo "Hotsite em http://localhost:$(PORT)/ (Ctrl+C para parar)"
	@$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory build/site
