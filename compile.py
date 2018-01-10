#!/usr/bin/python3.6

import re, base64, json, sys, types, subprocess
from os import devnull
from urllib.request import Request, urlopen, urlretrieve

def urlretrieve(urlfile, fpath):
    f = open(fpath, "w")
    f.write(urlfile.read().decode())
    f.close()

partsDir = './resume-parts/'
dataDir = partsDir + 'data/'

def loadDataFile(name, dir=dataDir):
    with open(dir + name + '.json', 'r') as file:
        data = file.read()
        file.close()
    return json.loads(data)

config = loadDataFile('config', './')

# TODO: Replace with git submodule/ssh key
githubUser = loadDataFile('githubUser', './secrets/')

def getArgValue(argName):
    value = None
    argStart = '--' + argName + '='
    for arg in sys.argv:
        if (arg.startswith(argStart)):
            value = arg[len(argStart):]
    if (value == None):
        value = config[argName]
    if (value == None):
        print ('No value found for setting \'{}\'. Check config.json to make sure a default exists, or supply one on the command line.'.format(argName))
    return value

repoUrl = getArgValue('repo-url')
latexEngine = getArgValue('engine')

def downloadFiles():
    auth = 'Basic ' + base64.b64encode('{}:{}'.format(githubUser['user'], githubUser['pass']).encode('ascii')).decode()

    req = Request(repoUrl + 'header.json')
    req.add_header('Authorization', auth)
    res = urlopen(req)
    fileNames = json.loads(res.read().decode())['files']

    for name in fileNames:
        print ("downloading " + name)
        req = Request(repoUrl + name)
        req.add_header('Authorization', auth)
        urlretrieve(urlopen(req), dataDir + name)

prog = re.compile("<(latex|web):(.*):\\1>")
formatGroup = 1
contentGroup = 2
def formatTextForLatex(text):
    match = prog.search(text)
    while match != None:
        content = match.group(contentGroup) if match.group(formatGroup) == 'latex' else ''
        text = text[:match.start()] + content + text[match.end():]
        match = prog.search(text)
    return text

class TexFile:
    def __init__(self, name, header=None):
        self.data = loadDataFile(name)
        self.name = name
        self.lines = []
        self.currentIndent = ''
        if (header != None):
            self.resHeading(header)

    def save(self, fileName=None):
        fileName = (self.name if fileName == None else fileName)
        self.newLine()
        data = '\n'.join(self.lines)
        with open(partsDir + fileName + '.tex', 'w') as file:
            file.write(data)
            file.close()

    def indent(self):
        self.currentIndent += '\t'
        return self

    def unindent(self):
        self.currentIndent = self.currentIndent[:-1]
        return self

    def newLine(self):
        return self.append('')

    def append(self, line):
        self.lines.append(self.currentIndent + formatTextForLatex(line))
        return self

    def resHeading(self, heading):
        return self.append('\\resheading{{{}}}\n'.format(heading))

    def beginDescription(self):
        return self.append('\\begin{description}[labelindent=12pt]')

    def endDescription(self):
        return self.append('\\end{description}')
    
    def descriptionItem(self, heading, item):
        return self.append('\\item[{}:]'.format(heading)).append(item)

    def beginItemizeLeftMargin(self):
        return self.append('\\begin{itemize}[leftmargin=*]')

    def endItemize(self):
        return self.append('\\end{itemize}')

    def resSubHeading(self, institution, location, position, dates, items):
        self.append('\\item[]').indent()
        self.append('\\ressubheading{{{}}}{{{}}}{{{}}}{{{}}}'.format(institution, location, position, dates))
        self.append('\\begin{itemize}').indent()
        for i, item in enumerate(items):
            self.append('\\resitem{{{}}}'.format(item))
        return self.unindent().endItemize().unindent()

    def nItemList(self, heading, items, singletonsOneLine=False):
        self.indent()
        if (len(items) == 1 and singletonsOneLine):
            self.newLine().descriptionItem(heading, items[0])
        else:
            self.newLine().append('\\nitem{{{}}}'.format(heading)).beginItemizeLeftMargin().indent()
            for item in items:
                self.append('\\ritem{{{}}}'.format(item))
            self.unindent().endItemize()
        return self.unindent()
    
    def header(self, column1, column2):
        self.append('\\begin{tabular*}{7.5in}{l@{\\extracolsep{\\fill}}r}').indent()
        for i in range(0, max(len(column1), len(column2))):
            line = ''
            if i < len(column1):
                line += column1[i]
            if i < len(column2):
                line += ' & ' + column2[i]
            self.append(line + '\\\\')
        return self.unindent().append('\\end{tabular*}').append('\\\\').append('\\vspace{0.1in}')


def genWebHeader():
    print('generating header_web.tex')
    web = TexFile('contact')
    column1 = ['\\textbf{{\large {}}}'.format(web.data['name'])]
    column2 = [web.data['email'],
        '\\href{{http://{0}}}{{{0}}}'.format(web.data['website']),
        '\\href{{https://www.linkedin.com/in/{0}}}{{\\linkedinsocialsymbol {0}}}'.format(web.data['linkedin']),
        '\\href{{https://www.github.com/{0}}}{{\\githubsocialsymbol {0}}}'.format(web.data['github'])]
    web.header(column1, column2).save('header_web')

def genFullHeader():
    print('generating header_full.tex')
    full = TexFile('contact')
    column1 = ['\\textbf{{\large {}}}'.format(full.data['name']),
        full.data['address'],
        full.data['city'] + ', ' + full.data['postal']]
    column2 = [full.data['phone'],
        full.data['email'],
        '\\href{{http://{0}}}{{{0}}}'.format(full.data['website']),
        '\\href{{https://www.linkedin.com/in/{0}}}{{\\linkedinsocialsymbol {0}}}'.format(full.data['linkedin']),
        '\\href{{https://www.github.com/{0}}}{{\\githubsocialsymbol {0}}}'.format(full.data['github'])]
    full.header(column1, column2).save('header_full')

def genExperience():
    print ('generating experience.tex file')
    exp = TexFile('experience', 'Work Experience').beginItemizeLeftMargin()
    for item in exp.data:
        exp.resSubHeading(item['company'], item['location'], item['position'],
            item['dates'], item['descriptionBullets'])
    exp.endItemize().save()

def genEducation():
    print ('generating education.tex file')
    edu = TexFile('education', 'Education').beginItemizeLeftMargin()
    for item in edu.data:
        edu.resSubHeading(item['school'], item['location'], item['degree'],
            item['dates'], item['descriptionBullets'])
    edu.endItemize().save()

numberList = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten']
def genSkills():
    print ('generating skills.tex file')
    skills = TexFile('skills', 'Technical Experience').beginDescription()
    
    projectItems = []
    for project in skills.data['projects']:
        projectItems.append('\\textbf{{{}:}} {}'.format(project['name'], project['description']))
    skills.nItemList('Projects', projectItems)

    progItems = []
    for prog in skills.data['programming']:
        yearsOverride = prog.get('yearsOverride', None)
        years = yearsOverride if yearsOverride != None else numberList[prog['years']] + ' years'
        description = '{} experience, {}'.format(years, prog['description'])
        progItems.append('\\textbf{{{}:}} {}'.format(prog['language'], description))
    skills.nItemList('Programming', progItems)

    softItems = []
    for level in skills.data['software']:
        item = '\\textbf{{{} with:}} '.format(level['level'])
        softwareList = level['software']
        for i, software in enumerate(softwareList):
            item = item + software + ('.' if i == len(softwareList) - 1 else (', ' if i < len(softwareList) - 2 else ', and '))
        softItems.append(item)
    skills.nItemList('Software', softItems)

    skills.nItemList('Miscellaneous', skills.data['misc'], True)

    skills.endDescription().save()

placeList = ['Zeroth', 'First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth']
def genAchievements():
    print ('generating achievements.tex file')
    achieve = TexFile('achievements', 'Achievements').beginDescription()

    compItems = []
    for comp in achieve.data['competitions']:
        place = placeList[comp['place']]
        teamSize = numberList[comp['teamSize']].lower()
        compItems.append('{} place, {}, on a team of {}.'.format(place, comp['name'], teamSize))
    achieve.nItemList('Competitions', compItems, True)

    achieve.nItemList('Academic', achieve.data['academic'], True)
    achieve.endDescription().save()

def genActivities():
    print ('generating activities.tex file')
    activities = TexFile('activities', 'Extracurricular Activities').beginDescription().indent()

    for activity in activities.data:
        activities.descriptionItem(activity['title'], activity['description'])

    activities.unindent().endDescription().save()

def genLatex():
    genWebHeader()
    genFullHeader()
    genExperience()
    genEducation()
    genSkills()
    genAchievements()
    genActivities()

hasCompiled = False
def beforeCompile():
    global hasCompiled
    if (not hasCompiled):
        hasCompiled = True
        if '--local' not in sys.argv:
            subprocess.call('rm {}/*.json'.format(dataDir), shell=True)
            downloadFiles()
        if '--existing' not in sys.argv:
            genLatex()

quiet = False
commands = {}
def execCommand(commandName):
    command = commands.get(commandName)
    if command == None:
        print('Unknown command: ' + commandName)
    else:
        if (isinstance(command, list)):
            print ('executing command: {} ({})'.format(commandName, ', '.join(command)))
            for name in command:
                execCommand(name)
        else:
            if command.startswith(latexEngine):
                beforeCompile()
            print ('executing command: {} ({})'.format(commandName, command))
            global quiet
            stdout = None if not quiet else open(devnull, 'w')
            subprocess.call(command, shell=True, stdout=stdout)

if '--help' in sys.argv:
    with open('help.txt', 'r') as file:
        print(file.read())
        file.close()
else:
    exit = False
    commands['my-command'] = []
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            commands['my-command'].append(arg)
    if len(commands['my-command']) == 0:
        exit = True
        print ('Expecting at least one command. Use option `--help` for more information.')

    if not exit:
        if '--quiet' in sys.argv:
            quiet = True

        outDir = getArgValue('outdir')
        pdfDir = getArgValue('pdfdir')
        compileLatex = '{} -shell-escape -output-directory={} -jobname={{}} {{}}.tex'.format(latexEngine, outDir)
        
        commands['all'] = ['do-resume', 'do-cover-letters', 'copy']
        
        commands['resume'] = ['do-resume', 'copy']
        commands['do-resume'] = ['do-web', 'do-full']
        
        commands['web'] = ['do-web', 'copy']
        commands['do-web'] = compileLatex.format('resume-web', 'resume')
        
        commands['full'] = ['do-full', 'copy']
        commands['do-full'] = compileLatex.format('resume-full', 'resume')
        
        commands['cover-letters'] = ['do-cover-letters', 'copy']
        commands['do-cover-letters'] = compileLatex.format('lockheed-martin-job', 'coverletter')
        
        commands['copy'] = 'cp {}/*.pdf {}/'.format(outDir, pdfDir)

        uploadMachine = getArgValue('upload-machine')
        uploadPath = getArgValue('upload-path')
        uploadFile = getArgValue('upload-file')
        commands['upload'] = 'scp {}/{}.pdf {}:{}'.format(pdfDir, uploadFile, uploadMachine, uploadPath)

        execCommand('my-command')
