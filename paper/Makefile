.PHONY: all acl clean

all:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex

acl:
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex

clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
