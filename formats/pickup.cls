\renewcommand{\normalsize}{\fontsize{12pt}{14pt}\selectfont}
\renewcommand{\familydefault}{\sfdefault}
\RequirePackage[utf8]{inputenc}
\RequirePackage{ifthen,type1cm,eso-pic,marvosym}
\RequirePackage[a4paper]{geometry}
\geometry{top=1cm,bottom=1cm,outer=0mm,left=1cm,right=1cm,nofoot,nohead,includeheadfoot}
\AddToShipoutPicture{
  \setlength\unitlength{1cm}%
  \put(0,8.5){\line(1,0){21}}
  \put(0,17.5){\line(1,0){21}}
}
\newcommand\socPickup[8]{
{\fontsize{24pt}{30pt}\selectfont\bfseries Abholkennwort: #4\hfill\hfill\ifthenelse{\equal{#5}{payed}}{bezahlt}{nicht bezahlt}\par}
\ifthenelse{\equal{#1}{female}}{Frau}{Herr} #2\hfill{\fontsize{24pt}{30pt}\selectfont\bfseries \EUR #8\par}
Zahlungskennzeichen: #3\par
\vspace{1cm}
#6\par
#7\par
\vspace{1cm}
}
\newcommand\socTicket[5]{%
#1, Reihe #2, Platz #3, Kategorie #4, \EUR #5\par
}
