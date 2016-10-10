\renewcommand{\normalsize}{\fontsize{12pt}{14pt}\selectfont}
\renewcommand{\familydefault}{\sfdefault}
\RequirePackage[utf8]{inputenc}
\RequirePackage{ifthen,type1cm,eso-pic,marvosym,helvet}
\RequirePackage[a4paper]{geometry}
\geometry{top=1cm,bottom=1cm,outer=0mm,left=1.4cm,right=1.4cm,nofoot,nohead,includeheadfoot}
\newcommand\socPickup[8]{
\AddToShipoutPicture*{
  \setlength\unitlength{1cm}%
  \put(0,9.7){\line(1,0){21}}
  \put(0,19.7){\line(1,0){21}}
}%
{\fontsize{24pt}{30pt}\selectfont\bfseries Abholkennwort: #4\hfill\hfill\ifthenelse{\equal{#5}{payed}}{bezahlt}{nicht bezahlt}\par}
\ifthenelse{\equal{#1}{female}}{Frau}{Herr} #2\hfill{\fontsize{24pt}{30pt}\selectfont\bfseries \EUR #8\par}
Zahlungskennzeichen: #3\par
\vspace{0.5cm}
#6\par
#7\par
\vspace{0.5cm}
}
\newcommand\socShipment[9]{
\AddToShipoutPicture*{
  \setlength\unitlength{1cm}%
  \put(0.3,10.5){\line(1,0){0.2}}
  \put(0.3,14.85){\line(1,0){0.4}}
  \put(0.3,21){\line(1,0){0.2}}
}%
\vspace*{1.7cm}
\underline{\fontsize{8pt}{10pt}\selectfont André Wobst, Amselweg 22, 85716 Unterschleißheim}\par
\vspace*{0.7cm}
#5 #6\par
#7\par
#8 #9\par
\vspace{2cm}
\ifthenelse{\equal{#1}{female}}{Sehr geehrte Frau}{Sehr geehrter Herr} #2,\par
\vspace{1cm}
vielen Dank für Ihren Kartenkauf für folgendes Konzert:\par
\vspace{0.5cm}
#3\par
#4\par
\vspace{0.5cm}
Anbei übersenden wir Ihnen Ihre Karten:\par
\vspace{0.5cm}
}
\newcommand\socTicket[5]{%
#1, Reihe #2, Platz #3, Kategorie #4, \EUR #5\par
}
