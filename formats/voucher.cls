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
\newbox\memberBox
\newenvironment{members}{}{}
\newenvironment{memberGroup}{}{}
\newenvironment{member}{}{%
\begin{picture}(105,49.5)
\put(10,40){\parbox[t]{8.5cm}{Schw\"abischer Oratorienchor\par
Gutschein f\"ur eine Chor-Freikarte\par
\vspace{1mm}
\@info\par
\vspace{1mm}
Kategorie B, \EUR{} 22\par
\vspace{1mm}
{\fontsize{8}{9.5}\selectfont\raggedright
auch nutzbar beim Kauf von Karten einer anderen Kategorie\par
einl\"osbar \textbf{nur im Vorverkauf} w\"ahrend der Chorproben sowie im Online-Kartenverkauf, aber \textbf{nicht an der Abendkasse}\par}
\vspace{3mm}
\member@Firstname{} \member@Lastname}}
%\put(0,0){\line(1,0){105}}
%\put(0,0){\line(0,1){49.5}}
%\put(105,49.5){\line(-1,0){105}}
%\put(105,49.5){\line(0,-1){49.5}}
\end{picture}%
\hspace{0pt plus 1pt}%
}
\newcommand\datetime[1]{}
\newcommand\info[1]{\gdef\@info{#1}}
\newcommand\memberId[1]{}
\newcommand\memberLogin[1]{}
\newcommand\memberGender[1]{}
\newcommand\memberTitle[1]{}
\newcommand\memberFirstname[1]{\gdef\member@Firstname{#1}}
\newcommand\memberLastname[1]{\gdef\member@Lastname{#1}}
\newcommand\memberCo[1]{\gdef\member@Co{#1}}
\newcommand\memberStreet[1]{\gdef\member@Street{#1}}
\newcommand\memberZip[1]{\gdef\member@Zip{#1}}
\newcommand\memberCity[1]{\gdef\member@City{#1}}
\newcommand\memberLateral[1]{}
\newcommand\memberLongitudinal[1]{}
\newcommand\memberEmail[1]{}
\newcommand\memberPhone[1]{}
\newcommand\memberBirthday[1]{}
\newcommand\memberNote[1]{}
\newcommand\memberTags[1]{}
