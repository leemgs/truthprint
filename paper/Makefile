.PHONY: all acl check audit refs clean

all:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex

acl:
	python3 make_acl_source.py
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
	bibtex acl_main
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex

check:
	python3 make_acl_source.py --check
	@! grep -E 'Geunsik|leemgs@gmail|Independent researcher|IEEEtran|IEEEkeywords|markboth' acl_main.tex
	@! grep -E 'Float too large|Overfull|undefined|Citation .* undefined' acl_main.log

audit: check
	python3 tools/ink_audit.py acl_main.pdf

refs:
	python3 tools/check_refs.py

clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
