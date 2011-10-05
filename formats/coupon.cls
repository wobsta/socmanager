\nonstopmode
\renewcommand\normalsize{\fontsize{10}{12}\selectfont}
\setlength\textwidth{6.5in}
\setlength\textheight{8in}
\pagenumbering{arabic}
\RequirePackage{graphicx,ifthen,marvosym}
\RequirePackage{helvet}
\RequirePackage[paperwidth=210mm,paperheight=297mm]{geometry}
\geometry{top=0mm,bottom=0mm,outer=0mm,left=0mm,right=0mm,nofoot,nohead,includeheadfoot}
\RequirePackage[a4,center]{crop}%
\renewcommand{\familydefault}{\sfdefault}
\setlength\unitlength{1mm}
\setlength\parindent{0pt}
\setlength\lineskip{0pt}
\linethickness{0.01mm}
\raggedbottom
\newcommand\socCoupon[2]{%
\begin{picture}(105,49.5)
\put(10,35){\parbox[t]{8.5cm}{\raggedright NEU! Dieser Gutschein ist auch online einl\"osbar.\par
\vspace{2mm}
Online-Gutscheincode: #1\par
\vspace{2mm}
\fontsize{8}{9.5}\selectfont
Hinweis: Mehrere Gutscheine k\"onnen gleichzeitig eingel\"ost werden, indem man mehrere Gutscheincodes mit Komma getrennt in das Gutscheinfeld eintr\"agt.\par
}}
\put(0,0){\line(1,0){105}}
\put(0,0){\line(0,1){49.5}}
\put(105,49.5){\line(-1,0){105}}
\put(105,49.5){\line(0,-1){49.5}}
\end{picture}%
\hspace{0pt plus 1pt}%
}
