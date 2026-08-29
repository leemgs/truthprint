.PHONY: all acl check clean

all:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex

acl:
	python3 make_acl_source.py
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex

check:
	python3 make_acl_source.py --check
	@! grep -E 'Geunsik|leemgs@gmail|Independent researcher|IEEEtran|IEEEkeywords|markboth' acl_main.tex

clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
