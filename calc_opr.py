import sys
import urllib2
from bs4 import BeautifulSoup as bs
import numpy as np
import dbm
import pprint

class StrMemo(object):
    def __init__(self, db_filename, f):
        self.__db = dbm.open(db_filename, 'c')
        self.__f = f

    def __call__(self, arg):
        if not self.__db.has_key(arg):
            self.__db.setdefault(arg, self.__f(arg))
        return self.__db.get(arg)


def makeTeamMapping(data):
    mapping = {}
    for r1, r2, b1, b2, _, _ in data:
        if r1 not in mapping:
            mapping[r1] = len(mapping)
        if r2 not in mapping:
            mapping[r2] = len(mapping)
        if b1 not in mapping:
            mapping[b1] = len(mapping)
        if b2 not in mapping:
            mapping[b2] = len(mapping)
    return mapping

def makePairingMatrix(data, team_map):
    N = len(team_map)
    mat = np.matrix([[0 for _ in range(N)]
                     for _ in range(N)])
    for r1, r2, b1, b2, _, _ in data:
        r1 = team_map[r1]
        r2 = team_map[r2]
        b1 = team_map[b1]
        b2 = team_map[b2]

        mat[r1,r2] += 1
        mat[r2,r1] += 1
        mat[b1,b2] += 1
        mat[b2,b1] += 1

        mat[r1,r1] += 1
        mat[r2,r2] += 1
        mat[b1,b1] += 1
        mat[b2,b2] += 1

    return mat

def makeTeamScores(data, team_map):
    N = len(team_map)
    mat = np.array([0 for _ in range(N)])
    for r1, r2, b1, b2, red, blue in data:
        r1 = team_map[r1]
        r2 = team_map[r2]
        b1 = team_map[b1]
        b2 = team_map[b2]

        mat[r1] += red
        mat[r2] += red
        mat[b1] += blue
        mat[b2] += blue
    return mat

def countWins(data, team_map):
    wins = dict()
    for r1, r2, b1, b2, red, blue in data:
        if int(red) > int(blue):
            wins[r1] = 1 + wins.get(r1, 0)
            wins[r2] = 1 + wins.get(r2, 0)
        else:
            wins[b1] = 1 + wins.get(b1, 0)
            wins[b2] = 1 + wins.get(b2, 0)

    return wins

def debugPairings(team_map, pairings):
    rev = dict((v,k) for (k,v) in team_map.items())
    print('\t%s' % '\t'.join(str(rev[i]) for i in range(len(pairings))))
    for i in range(len(pairings)):
        print '%s\t%s' % (rev[i], '\t'.join(str(pairings[i,j])
                                            for j in range(len(pairings))))

def calcOPR(data):
    team_map = makeTeamMapping(data)
    pairings = makePairingMatrix(data, team_map)
    # debugPairings(team_map, pairings)
    team_scores = makeTeamScores(data, team_map)
    team_wins = countWins(data, team_map)
    return team_map, team_wins, team_scores * pairings.I


def getData(table):
    for tr in table.findAll('tr'):
        if tr is not None:
            tds = list(tr.findAll('td'))
            if any(td.text.startswith('Quals') for td in tds):
                yield [int(td.text.strip()) for td in tds[2:]]

def hasQual(table):
    return any(th.text == 'Qualification Matches'
               for th in table.findAll('th'))

def get(url):
    return urllib2.urlopen(url).read()

def collate(table):
    data = list(getData(table))
    nicePrintTourneyData(data)
    teams, wins, opr = calcOPR(data)
    by_scores = reversed(sorted((opr[0, team_num], team)
                                for team, team_num in teams.items()))
    for score, team in by_scores:
        yield (score, team, wins.get(team, 0))

def nicePrintTourneyData(data):
    for i in range(len(data)):
        for j in range(len(data[i])):
            sys.stdout.write("%i, " % data[i][j])
        print

def main():
    get_url = StrMemo('yellow', get)
    for tournament_url in sys.argv[1:]:
        html = get_url(tournament_url)
        soup = bs(html, "html.parser")
        teams = []
        for table in soup.findAll('table'):
            if hasQual(table):
                try:
                    teams.extend(collate(table))
                except np.linalg.linalg.LinAlgError:
                    pass # derp
                break
        # for i, (score, team, wins) in enumerate(reversed(sorted(teams))):
        #     print '#%d\t%f\t%s\t%d' % (1 + i, score, team, wins)

if '__main__' == __name__:
    main()
