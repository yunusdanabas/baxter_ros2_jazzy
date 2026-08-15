# Build the manual. Requires TeX Live with tikz, pgfplots, listings, tcolorbox.
#
#   make          build baxter_manual.pdf
#   make figures  regenerate the derived figures (needs a built workspace)
#   make clean    remove build artifacts, keep the PDF
#   make distclean remove the PDF too

MAIN := baxter_manual

.PHONY: all figures clean distclean

all: $(MAIN).pdf

# -halt-on-error so a broken figure fails the build instead of dropping into
# the interactive prompt and hanging a CI job.
$(MAIN).pdf: $(MAIN).tex preamble.tex $(wildcard chapters/*.tex) $(wildcard figures/*.tex)
	latexmk -pdf -halt-on-error -interaction=nonstopmode $(MAIN).tex

figures:
	bash figures/generate.sh

clean:
	latexmk -c $(MAIN).tex
	rm -f $(MAIN).bbl

distclean: clean
	rm -f $(MAIN).pdf
