PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PORT ?= 8765
export PATH := $(if $(wildcard .venv/bin),$(CURDIR)/.venv/bin:,)$(PATH)   # pyz80 do ambiente local
ROM := build/posto-umbra.rom

.PHONY: site serve final

$(ROM):
	$(PYTHON) tools/build.py

site: $(ROM)
	$(PYTHON) tools/build_site.py

serve: site
	@echo "Hotsite em http://localhost:$(PORT)/ (Ctrl+C para parar)"
	@$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory build/site

# Atalho de desenvolvimento: Espaço no título abre direto a tela final.
final:
	$(PYTHON) tools/build.py --final
	$(PYTHON) tools/build_site.py --rom build/posto-umbra-final.rom --release final
	@echo "Tela final em http://localhost:$(PORT)/ (Espaço no título; Ctrl+C para parar)"
	@$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory build/site
