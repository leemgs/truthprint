.PHONY: all acl nature check audit refs artifact clean

all:
	pdflatex -interaction=nonstopmode -halt-on-error main.tex
	pdflatex -interaction=nonstopmode -halt-on-error main.tex

acl:
	python3 make_acl_source.py
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
	bibtex acl_main
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex
	pdflatex -interaction=nonstopmode -halt-on-error acl_main.tex

nature:
	cd nature && python3 make_nature_assets.py && python3 make_nature_refs.py
	cd nature && pdflatex -interaction=nonstopmode -halt-on-error nature_main.tex
	cd nature && pdflatex -interaction=nonstopmode -halt-on-error nature_main.tex
	@! grep -E 'Float too large|Overfull|undefined' nature/nature_main.log
	python3 tools/ink_audit.py nature/nature_main.pdf --line-numbers | tail -1

check:
	python3 make_acl_source.py --check
	@! grep -E 'Geunsik|leemgs@gmail|Independent researcher|IEEEtran|IEEEkeywords|markboth' acl_main.tex
	@! grep -E 'Float too large|Overfull|undefined|Citation .* undefined' acl_main.log
	python3 tools/check_submission.py acl_main.pdf

audit: check
	python3 tools/ink_audit.py acl_main.pdf

refs:
	python3 tools/check_refs.py

artifact: acl
	python3 ../tools/make_anonymous_artifact.py --self-test

clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.synctex.gz
