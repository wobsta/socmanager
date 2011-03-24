\DeclareOption*{\input{\CurrentOption.clo}}
\ProcessOptions\relax
\renewcommand{\normalsize}{\fontsize{7pt}{7pt}\selectfont}
\renewcommand{\familydefault}{\sfdefault}
\RequirePackage{ifthen,graphicx,color,type1cm}
\RequirePackage[a4paper]{geometry}
\geometry{top=0mm,bottom=0mm,outer=0mm,left=0mm,right=0mm,nofoot,nohead,includeheadfoot}
\setlength{\unitlength}{1cm}
\newcounter{count@A}
\newcounter{count@B}
\newcounter{count@C}
\definecolor{Astrong}{cmyk}{1,0,1,0}
\definecolor{Bstrong}{cmyk}{0,1,1,0}
\definecolor{Cstrong}{cmyk}{1,1,0,0}
\definecolor{Alight}{cmyk}{0.2,0,0.2,0}
\definecolor{Blight}{cmyk}{0,0.2,0.2,0}
\definecolor{Clight}{cmyk}{0.2,0.2,0,0}
\definecolor{grey}{cmyk}{0,0,0,0.4}
\newcommand\socSeat[5]{%
  \color{#4#5}%
  \ifthenelse{\equal{#5}{strong}}{\stepcounter{count@#4}}{}%
  \ifthenelse{\equal{\@nameuse{dat@#1@#2@#3@t}}{pew}}{%
    \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{-0.2cm}\raisebox{-0.15cm}[0pt][0pt]{\line(1,0){0.4}}}}%
    \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{-0.2cm}\raisebox{-0.15cm}[0pt][0pt]{\line(0,1){0.3}}}}%
    \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{0.2cm}\raisebox{0.15cm}[0pt][0pt]{\line(-1,0){0.4}}}}%
    \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{0.2cm}\raisebox{0.15cm}[0pt][0pt]{\line(0,-1){0.3}}}}%
  }{%
    \ifthenelse{\equal{\@nameuse{dat@#1@#2@#3@t}}{pewsmall}}{%
      \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{-0.15cm}\raisebox{-0.15cm}[0pt][0pt]{\line(1,0){0.3}}}}%
      \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{-0.15cm}\raisebox{-0.15cm}[0pt][0pt]{\line(0,1){0.3}}}}%
      \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{0.15cm}\raisebox{0.15cm}[0pt][0pt]{\line(-1,0){0.3}}}}%
      \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{0.15cm}\raisebox{0.15cm}[0pt][0pt]{\line(0,-1){0.3}}}}%
    }{%
      \ifthenelse{\equal{\@nameuse{dat@#1@#2@#3@t}}{chair}}{%
        \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\circle{0.3}}%
      }{%
        \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\circle{0.3}}%
        \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{-0.15cm}\raisebox{-0.15cm}[0pt][0pt]{\line(0,1){0.3}}}}%
        \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\hspace{0.15cm}\raisebox{0.15cm}[0pt][0pt]{\line(0,-1){0.3}}}}%
      }%
    }%
  }%
  \put(\@nameuse{dat@#1@#2@#3@x},\@nameuse{dat@#1@#2@#3@y}){\rotatebox{\@nameuse{dat@#1@#2@#3@d}}{\raisebox{-0.07cm}[0pt][0pt]{\makebox[0pt]{#3}}}}%
}
\AtBeginDocument{\noindent\begin{picture}(21,29.7)(0,0)}
\AtEndDocument{\end{picture}}
\newcommand\socTitle[2]{
  \put(10.5,28.3){\fontsize{16pt}{16pt}\selectfont\bfseries\makebox[0pt]{#1}}
  \put(10.5,27.5){\fontsize{16pt}{16pt}\selectfont\bfseries\makebox[0pt]{#2}}
  \put(10.8,21.5){\fontsize{16pt}{16pt}\selectfont\bfseries Chor und Orchester}
  \put(11.2,13.5){\fontsize{36pt}{36pt}\selectfont\bfseries\color{grey}Mitte}
  \put(07.3,15.3){\fontsize{36pt}{36pt}\selectfont\bfseries\color{grey}\rotatebox{-90}{Links}}
  \put(16.9,11.7){\fontsize{36pt}{36pt}\selectfont\bfseries\color{grey}\rotatebox{90}{Rechts}}
  \put(09.2,02.3){\fontsize{36pt}{36pt}\selectfont\bfseries\color{grey}Empore Mitte}
  \put(03.4,17.3){\fontsize{36pt}{36pt}\selectfont\bfseries\color{grey}\rotatebox{-90}{Empore Links}}
  \put(15.2,17.4){Reihe 1}
  \put(15.2,16.9){Reihe 2}
  \put(15.2,16.4){Reihe 3}
  \put(15.2,15.9){Reihe 4}
  \put(15.2,15.4){Reihe 5}
  \put(15.2,14.9){Reihe 6}
  \put(15.2,14.4){Reihe 7}
  \put(15.2,13.9){Reihe 8}
  \put(15.2,13.4){Reihe 9}
  \put(15.2,12.9){Reihe 10}
  \put(15.2,12.4){Reihe 11}
  \put(15.2,11.9){Reihe 12}
  \put(15.2,11.4){Reihe 13}
  \put(15.2,10.9){Reihe 14}
  \put(15.2,10.4){Reihe 15}
  \put(15.2,09.9){Reihe 16}
  \put(15.2,09.4){Reihe 17}
  \put(15.2,08.9){Reihe 18}
  \put(15.2,08.4){Reihe 19}
  \put(15.2,07.9){Reihe 20}
  \put(12.4,06.4){Reihe 21}
  \put(12.4,05.9){Reihe 22}
  \put(12.4,05.4){Reihe 23}
  \put(12.4,04.9){Reihe 24}
  \put(09.1,21.2){\rotatebox{-90}{Reihe 1}}
  \put(08.1,23.3){\rotatebox{-90}{Reihe 2}}
  \put(07.6,23.3){\rotatebox{-90}{Reihe 3}}
  \put(07.1,26.2){\rotatebox{-90}{Reihe 4}}
  \put(06.6,26.2){\rotatebox{-90}{Reihe 5}}
  \put(17.3,21.1){\rotatebox{90}{Reihe 1}}
  \put(17.8,21.1){\rotatebox{90}{Reihe 2}}
  \put(17.5,17.5){\rotatebox{90}{Reihe 3}}
  \put(16.8,13.1){\rotatebox{90}{Reihe 4}}
  \put(17.3,13.1){\rotatebox{90}{Reihe 5}}
  \put(17.8,13.1){\rotatebox{90}{Reihe 6}}
  \put(18.2,12.4){Reihe 7}
  \put(18.2,11.9){Reihe 8}
  \put(18.2,11.4){Reihe 9}
  \put(18.2,10.9){Reihe 10}
  \put(18.2,10.4){Reihe 11}
  \put(18.2,09.9){Reihe 12}
  \put(18.2,09.4){Reihe 13}
  \put(18.2,08.9){Reihe 14}
  \put(18.2,08.4){Reihe 15}
  \put(18.2,03.4){Reihe 1}
  \put(18.2,02.9){Reihe 2}
  \put(18.2,02.4){Reihe 3}
  \put(18.2,01.9){Reihe 4}
  \put(18.2,01.4){Reihe 5}
  \put(05.1,26.2){\rotatebox{-90}{Reihe 1}}
  \put(04.4,26.2){\rotatebox{-90}{Reihe 2}}
  \put(03.9,26.2){\rotatebox{-90}{Reihe 3}}
  \put(03.4,26.2){\rotatebox{-90}{Reihe 4}}
  \put(02.9,26.2){\rotatebox{-90}{Reihe 5}}
  \put(05.9,04.3){\linethickness{0.5mm}\line(0,1){22}}
  \put(05.9,04.3){\linethickness{0.5mm}\line(1,0){13.3}}
  \put(08.8,01.35){\line(0,1){0.4}}
  \put(11.2,01.35){\line(0,1){0.4}}
  \put(13.2,01.35){\line(0,1){0.4}}
  \put(15.2,01.35){\line(0,1){0.4}}
  \put(01.8,03.0){\color{Astrong}\fontsize{10pt}{10pt}\selectfont Kategorie A}%
  \put(01.8,02.5){\color{Bstrong}\fontsize{10pt}{10pt}\selectfont Kategorie B}%
  \put(01.8,02.0){\color{Cstrong}\fontsize{10pt}{10pt}\selectfont Kategorie C}%
}
\newcommand\socStat{
  \put(03.55,03.0){\color{Astrong}\fontsize{10pt}{10pt}\selectfont: \arabic{count@A} Pl\"atze}%
  \put(03.55,02.5){\color{Bstrong}\fontsize{10pt}{10pt}\selectfont: \arabic{count@B} Pl\"atze}%
  \put(03.55,02.0){\color{Cstrong}\fontsize{10pt}{10pt}\selectfont: \arabic{count@C} Pl\"atze}%
}
