%
% sphinxhowto.cls for Sphinx (http://sphinx-doc.org/)
%

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{sphinxhowto}[2009/06/02 Document class (Sphinx HOWTO)]

% 'oneside' option overriding the 'twoside' default
\newif\if@oneside
\DeclareOption{oneside}{\@onesidetrue}
% Pass remaining document options to the parent class.
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{\sphinxdocclass}}
\ProcessOptions\relax

% Default to two-side document
\if@oneside
% nothing to do (oneside is the default)
\else
\PassOptionsToClass{twoside}{\sphinxdocclass}
\fi

\LoadClass{\sphinxdocclass}

% Set some sane defaults for section numbering depth and TOC depth.  You can
% reset these counters in your preamble.
%
\setcounter{secnumdepth}{2}

% Change the title page to look a bit better, and fit in with the fncychap
% ``Bjarne'' style a bit better.
%
\renewcommand{\maketitle}{
  \rule{\textwidth}{1pt}
  \ifsphinxpdfoutput
    \begingroup
    % These \defs are required to deal with multi-line authors; it
    % changes \\ to ', ' (comma-space), making it pass muster for
    % generating document info in the PDF file.
    \def\\{, }
    \def\and{and }
    \pdfinfo{
      /Author (\@author)
      /Title (\@title)
    }
    \endgroup
  \fi
  \begin{flushright}
    \sphinxlogo%
    {\rm\Huge\py@HeaderFamily \@title} \par
    {\em\large\py@HeaderFamily \py@release\releaseinfo} \par
    \vspace{25pt}
    {\Large\py@HeaderFamily
      \begin{tabular}[t]{c}
        \@author
      \end{tabular}} \par
    \vspace{25pt}
    \@date \par
    \py@authoraddress \par
  \end{flushright}
  \@thanks
  \setcounter{footnote}{0}
  \let\thanks\relax\let\maketitle\relax
  %\gdef\@thanks{}\gdef\@author{}\gdef\@title{}
}

\let\py@OldTableofcontents=\tableofcontents
\renewcommand{\tableofcontents}{
  \begingroup
    \parskip = 0mm
    \py@OldTableofcontents
  \endgroup
  \rule{\textwidth}{1pt}
  \vspace{12pt}
}  

\@ifundefined{fancyhf}{
  \pagestyle{plain}}{
  \pagestyle{normal}}		% start this way; change for
\pagenumbering{arabic}		% ToC & chapters

\thispagestyle{empty}

% Fix the bibliography environment to add an entry to the Table of
% Contents.
% For an article document class this environment is a section,
% so no page break before it.
\let\py@OldThebibliography=\thebibliography
\renewcommand{\thebibliography}[1]{
  \phantomsection
  \py@OldThebibliography{1}
  \addcontentsline{toc}{section}{\bibname}
}
