\nonstopmode
\renewcommand\normalsize{\fontsize{10}{12}\selectfont}
\pagenumbering{arabic}
\RequirePackage{ifthen,xstring}
\RequirePackage{times}
\RequirePackage[a4paper]{geometry}
\geometry{top=10mm,bottom=10mm,outer=0mm,left=20mm,right=20mm,head=12pt,headsep=5mm,foot=10mm,includeheadfoot}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhead{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[L]{Schw\"abischer Oratorienchor}
\fancyfoot[C]{\thepage}
\fancyfoot[R]{http://www.schwaebischer-oratorienchor.de/}
\raggedbottom
\setlength\parindent{0mm}
\setlength\parskip{3mm}
\newcounter{memberCount}
\newenvironment{members}{}{}
\newenvironment{memberGroup}{}{}
\newenvironment{member}{}{%
\parbox{\linewidth}{\raggedright
\hangafter1\hangindent8mm
\stepcounter{memberCount}\makebox[8mm][l]{\arabic{memberCount}.}%
\member@Lastname, \member@Firstname
\ifthenelse{\equal{\member@Street}{}}{}{; \member@Street}%
\ifthenelse{\equal{\member@Zip\member@City}{}}{}{; \member@Zip{} \member@City}%
\ifthenelse{\equal{\member@Birthday}{}}{}{; \member@Birthday}%
\ifthenelse{\equal{\member@Email}{}}{}{; \member@Email}%
\ifthenelse{\equal{\member@Phone}{}}{}{; \member@Phone}%
\ifthenelse{\equal{\member@Tags}{}}{}{; \member@Tags}%
\ifthenelse{\equal{\member@Note}{}}{}{; \StrSubstitute{\member@Note}{:\string n}{: }[\Result]\StrSubstitute{\Result}{\string n}{, }}
}\par
}
\newcommand\datetime[1]{\fancyfoot[L]{erstellt am #1 Uhr}}
\newcommand\info[1]{\fancyhead[R]{#1}}
\newcommand\memberId[1]{\gdef\member@Id{#1}}
\newcommand\memberLogin[1]{\gdef\member@Login{#1}}
\newcommand\memberGender[1]{\gdef\member@Gender{#1}}
\newcommand\memberTitle[1]{\gdef\member@Title{#1}}
\newcommand\memberFirstname[1]{\gdef\member@Firstname{#1}}
\newcommand\memberLastname[1]{\gdef\member@Lastname{#1}}
\newcommand\memberCo[1]{\gdef\member@Co{#1}}
\newcommand\memberStreet[1]{\gdef\member@Street{#1}}
\newcommand\memberZip[1]{\gdef\member@Zip{#1}}
\newcommand\memberCity[1]{\gdef\member@City{#1}}
\newcommand\memberLateral[1]{\gdef\member@Lateral{#1}}
\newcommand\memberLongitudinal[1]{\gdef\member@Longitudinal{#1}}
\newcommand\memberEmail[1]{\gdef\member@Email{#1}}
\newcommand\memberPhone[1]{\gdef\member@Phone{#1}}
\newcommand\memberBirthday[1]{\gdef\member@Birthday{#1}}
\newcommand\memberNote[1]{\gdef\member@Note{#1}}
\newcommand\memberTags[1]{\gdef\member@Tags{#1}}
