\renewcommand{\normalsize}{\fontsize{7pt}{7pt}\selectfont}
\renewcommand{\familydefault}{\sfdefault}
\RequirePackage{ifthen,type1cm,color}
\RequirePackage[a4paper]{geometry}
\geometry{top=0mm,bottom=0mm,outer=0mm,left=0mm,right=0mm,nofoot,nohead,includeheadfoot}
\setlength\unitlength{1cm}
\setlength\parindent{0pt}
\setlength\lineskip{0pt}
\DeclareOption*{\input{\CurrentOption.clo}}
\ProcessOptions\relax
\newcommand\socSeat[5]{%
\begin{picture}(5.25,4.95)
%\put(0,0){\line(1,0){5.25}}
%\put(0,0){\line(0,1){4.95}}
%\put(0,4.95){\line(1,0){5.25}}
%\put(5.25,0){\line(0,1){4.95}}
\put(0,3.6){\makebox[5.25cm]{\fontsize{15}{15}\selectfont\textbf{#1}}}
\put(0.8,2.7){\fontsize{15}{15}\selectfont\textbf{Reihe:}}
\put(4.45,2.3){\makebox[0cm][r]{\fontsize{30}{30}\selectfont\textbf{#2}}}
\put(0.8,0.75){\fontsize{15}{15}\selectfont\textbf{Platz:}}
\put(4.55,0.7){\makebox[0cm][r]{\fontsize{50}{50}\selectfont\textbf{#3}}}
\end{picture}%
\hspace{0pt plus 1pt}%
}
\renewcommand\socTitle[2]{}
\renewcommand\socStat{}
