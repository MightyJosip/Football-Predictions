# LINK 1: http://www.collective-behavior.com/publ/ELO.pdf
# LINK 2: https://www.pinnacle.com/en/betting-articles/Soccer/how-to-calculate-poisson-distribution/MD62MLXUMKMXZ6A8
# LINK 3: http://clubelo.com/
# LINK 4: https://www.flashscores.co.uk/football/england/premier-league-2018-2019/standings/
# LINK 5: https://www.desmos.com/calculator/blcoia6ew0

import os
import numpy as np
import copy
import pickle
import time
from typing import Dict, Union

"""
These are constants that depends on the league. Games = number of games every team in league plays,
h_f_a = amount of elo added to team that plays on home field. c, d, k and lambda = constants used for elo
calculating, you probably don't want to change them, but in case you do you can find the info about them on the link
in line 1. Draw constants are used to calculate the draw chance. I got this numbers by calculating the integral of
draw function and setting it equal to average draw chance * elo interval where you calculate it (you can see more info
on graphical calculator linked on LINK 5)
"""
CONSTANTS = {'games': 38, 'number_of_clubs': 20, 'home_field_advantage': 66.7, 'c': 10, 'd': 400, 'k_base': 10,
             'lambda': 1, 'draw_max': 0.27, 'draw_variance': 250, 'home_att': 596/380, 'away_att': 476/380}

"""
These are the constants to set the size of cmd where you run this program (274 letters width and 67 height). I decided
to use this numbers to make screen "fullscreen", but on your PC it could be different, feel free to play with this,
don't think you can f*ck up something with changing this (you only need to be careful not to put width less than the
max len of one line because then the output will look ugly, but it will function normally)
"""
SCREEN_WIDTH = 274
SCREEN_HEIGHT = 67
os.system('mode con: cols={} lines={}'.format(SCREEN_WIDTH, SCREEN_HEIGHT))

"""
This is number of the calculations of the standing program will do. First I thought to use 14000605 for meme value 
(more info on this link: https://knowyourmeme.com/memes/i-saw-14000605-futures), but then I realised it would take my 
pc around 160 hours to calculate it (have really old and slow processor) all so I lowered this number to 1000000 
"""
MAX = 1000000


class Club:
    """ Class that represents the club. It has to have name (as we all do), elo (because this is the main parameter for
        calculations), and also 4 attributes for storing number of goals scored last season (used for Poisson
        distribution), the rest of attributes are used to store stats of the standings I am currently calculating and
        the placings is used to store end season result (if team finishes first then add one to the first element etc.)
        and later with this information calculate the percentage for each position"""
    home_goals_scored: int
    name: str
    elo: float

    def __init__(self, name: str, elo: int, home_goals_scored: int, home_goals_received: int, away_goals_scored: int,
                 away_goals_received: int) -> None:
        self.name = name
        self.elo = elo
        self.home_goals_scored = home_goals_scored
        self.home_goals_received = home_goals_received
        self.away_goals_scored = away_goals_scored
        self.away_goals_received = away_goals_received
        self.games = 0
        self.points = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.goals_scored = 0
        self.goals_received = 0
        self.placings = [0] * CONSTANTS['number_of_clubs']

    def __repr__(self) -> str:
        """
        Method to create string for printing the club stats, you can remove elo print (I used it for debugging process,
        but you can print it anyways)
        :return: output string
        """
        text = '| {} | {} | {} | {} | {} | {} | {} | {:.2f}'.format(self.name.center(35).ljust(35),
                                                                    str(self.games)[:2].center(10).ljust(10),
                                                                    str(self.points)[:5].center(10).ljust(10),
                                                                    str(self.wins)[:5].center(10).ljust(10),
                                                                    str(self.draws)[:5].center(10).ljust(10),
                                                                    str(self.losses)[:5].center(10).ljust(10),
                                                                    '{}:{}'.format(str(self.goals_scored)[:5],
                                                                                   str(self.goals_received)[:5])
                                                                    .center(15)
                                                                    .ljust(15),
                                                                    round(self.elo, 2))
        return text

    def add_result(self, points: int, goals_scored: int, goals_received: int, new_elo: float = None):
        """
        Method used after I calculate the outcome of the match, it updates points, goals, number of games and also the
        elo (but only if it actually calculated the new elo - and it is doing that right now)
        """
        self.points += points
        if points == 3:
            self.wins += 1
        elif points == 1:
            self.draws += 1
        else:
            self.losses += 1
        self.goals_scored += goals_scored
        self.goals_received += goals_received
        self.games += 1
        if self.elo is not None:
            self.elo = new_elo


class Standings:
    """
    Class used to represent the standings. It takes name and dictionary of clubs as parameters. Name is just the name of
    the league, it doesn't have any other use. clubs is the dictionary where you put clubs and then this class add 
    results of the games in it. It is the parent class that is used for full standings.
    """
    def __init__(self, name: str, clubs: Dict[str, Club]):
        self.name = name
        self.clubs = clubs

    def __repr__(self):
        text = ''
        text += '=' * SCREEN_WIDTH
        text += self.name.center(SCREEN_WIDTH)
        text += '=' * SCREEN_WIDTH
        text += '{} | {} | {} | {} | {} | {} | {} | {} | {}'.format('#',
                                                                    'Club name'.center(35).ljust(35),
                                                                    'Games'.center(10).ljust(10),
                                                                    'Points'.center(10).ljust(10),
                                                                    'Wins'.center(10).ljust(10),
                                                                    'Draws'.center(10).ljust(10),
                                                                    'Losses'.center(10).ljust(10),
                                                                    'Goals'.center(15).ljust(15),
                                                                    'ELO'.center(7).ljust(7)
                                                                    ).center(SCREEN_WIDTH)
        text += '=' * SCREEN_WIDTH
        place = 1
        self.sort_standings()
        for club in self.clubs:
            text += '{} {}'.format(str(place).rjust(2), self.clubs[club]).center(SCREEN_WIDTH)
            text += '-' * SCREEN_WIDTH
            place += 1
        return text

    def percentages(self):
        text = ''
        text += '=' * SCREEN_WIDTH
        text += self.name.center(SCREEN_WIDTH)
        text += '=' * SCREEN_WIDTH
        place = 1
        top = 'Club\\Position'.center(35) + '|'
        for i in range(1, 21):
            top += '{0:^10}'.format(i) + '|'
        text += top.center(SCREEN_WIDTH)
        text += '-' * SCREEN_WIDTH
        for club in self.clubs:
            places = self.clubs[club].name.center(35) + '|'
            for i in range(20):
                if i != 19:
                    places += '{:.4%}'.format(self.clubs[club].placings[i] / MAX).center(10) + '|'
                else:
                    places += '{:.4%}'.format(self.clubs[club].placings[i] / MAX).center(10) + '|'
            text += places.center(SCREEN_WIDTH)
            text += '-' * SCREEN_WIDTH
            place += 1
        return text

    def sort_standings(self) -> None:
        """
        Method that sorts the dictionary by points/goal difference
        """
        dictionary = {list(self.clubs.keys())[list(self.clubs.values()).index(i)]: i
                      for i in sorted(self.clubs.values(), key=lambda x: (x.points, x.goals_scored - x.goals_received,
                                                                          x.goals_scored), reverse=True)}
        self.clubs = dictionary


class StandingsFull(Standings):
    """
    Class used to represent the full standings. Since i run millions of calculations, I use this class to store the
    average of calculations.
    """
    def __init__(self, name, clubs):
        super().__init__(name, clubs)
        self.standing_calculated = 0

    def include(self, other: Standings) -> None:
        """
        Method that adds one standing to the full standings
        :param other: Standing that is being added
        """
        for club in self.clubs:
            self.clubs[club].games = 38
            self.clubs[club].points += other.clubs[club].points
            self.clubs[club].wins += other.clubs[club].wins
            self.clubs[club].draws += other.clubs[club].draws
            self.clubs[club].losses += other.clubs[club].losses
            self.clubs[club].goals_scored += other.clubs[club].goals_scored
            self.clubs[club].goals_received += other.clubs[club].goals_received
            self.clubs[club].elo += other.clubs[club].elo
        self.standing_calculated += 1

    def get_average(self):
        """
        Method that calculates the average of all standings
        """
        for club in self.clubs:
            self.clubs[club].points /= self.standing_calculated
            self.clubs[club].wins /= self.standing_calculated
            self.clubs[club].draws /= self.standing_calculated
            self.clubs[club].losses /= self.standing_calculated
            self.clubs[club].goals_scored /= self.standing_calculated
            self.clubs[club].goals_received /= self.standing_calculated
            self.clubs[club].elo /= self.standing_calculated


def calculate_probabilities(home: Club, away: Club) -> tuple:
    """
    Function that is being used to calculate the probabilities of each possible outcome of the match. It takes 2 clubs
    that play the match and then uses formulas to calculate the probabilities (floats between 0 and 1). You can find
    more info about this code on LINK 1 section 2 (explanation) and LINK 5 (graphical simulation of this function)
    :param home: Club that is playing on home field
    :param away: Club that is playing on away field
    :return: tuple that contains the probabilities (home_win, draw, away_win)
    """
    hfa = CONSTANTS['home_field_advantage']
    difference_in_elo = home.elo + hfa - away.elo
    draw_chance = CONSTANTS['draw_max'] * np.power(np.e, (-difference_in_elo ** 2 /
                                                          (2 * CONSTANTS['draw_variance'] ** 2)))
    home_win = 1 / (1 + np.power(CONSTANTS['c'], - difference_in_elo / CONSTANTS['d'])) * (1 - draw_chance)
    away_win = 1 / (1 + np.power(CONSTANTS['c'], difference_in_elo / CONSTANTS['d'])) * (1 - draw_chance)
    return home_win, draw_chance, away_win


def add_result(home: Club, away: Club) -> str:
    """
    Function that decides the winner of the match based on calculated probabilities. It returns the string that
    represents the outcome
    :param home: Club that is playing on home field
    :param away: Club that is playing on away field
    :return: String for outcome (1 == Home team won, X == draw, 2 == Away team won)
    """
    possible_outcomes = ['1', 'X', '2']
    probabilities = calculate_probabilities(home, away)
    return np.random.choice(possible_outcomes, p=probabilities)


def calculate_poisson(home_average: float, away_average: float) -> tuple:
    """
    Function chat decides how much goals will each team score (for this I use poisson distribution
    (more info on LINK 3)). It takes the average number of goals teams scored when playing on the home field/away field
    and returns the tuple which contains the integers (number of goals)
    :param home_average: average number of goals home team scored on its field
    :param away_average: average number of goals away team scored on other field
    :return: tuple (home_team_scored_goals, away_team_scored_goals)
    """
    home_poisson = np.random.poisson(home_average)
    away_poisson = np.random.poisson(away_average)
    return home_poisson, away_poisson


def add_goals(home: Club, away: Club, result: str) -> tuple:
    """
    Another function to add goals, but this time it adds goals based on the outcome of the match, for example if home
    team won the game but poisson decided that the result should be 0:0, then I calculate another poisson while I am not
    etting the right outcome. This is the function that is being used in main program to decide goals scored
    :param home: Club playing on the home field
    :param away: Club playing on the away field
    :param result: Who won
    :return: tuple (home_team_scored_goals, away_team_scored_goals)
    """
    games = CONSTANTS['games'] / 2
    home_att = (home.home_goals_scored / games) / CONSTANTS['home_att']
    away_def = (away.away_goals_received / games) / CONSTANTS['home_att']
    home_average = home_att * away_def * CONSTANTS['home_att']
    away_att = (away.away_goals_scored / games) / CONSTANTS['away_att']
    home_def = (away.home_goals_received / games) / CONSTANTS['away_att']
    away_average = away_att * home_def * CONSTANTS['away_att']
    home_scored, away_scored = calculate_poisson(home_average, away_average)
    if result == '1':
        while home_scored <= away_scored:
            home_scored, away_scored = calculate_poisson(home_average, away_average)
    elif result == 'X':
        while home_scored != away_scored:
            home_scored, away_scored = calculate_poisson(home_average, away_average)
    elif result == '2':
        while home_scored >= away_scored:
            home_scored, away_scored = calculate_poisson(home_average, away_average)
    return home_scored, away_scored


def elo_change(home: Club, away: Club, goal_difference: int) -> tuple:
    """
    Function that calculates the new elo of the clubs after the game (for more info about this calculation view LINK 1)
    :param home: Club playing on the home field
    :param away: Club playing on the away field
    :param goal_difference: home team scored goals - away team scored goals
    :return: tuple (new elo for home club, new elo for away club)
    """
    home_elo_before = home.elo + CONSTANTS['home_field_advantage']
    away_elo_before = away.elo
    home_positive_result = 1 / (1 + np.power(CONSTANTS['c'], (away_elo_before - home_elo_before) / CONSTANTS['d']))
    if goal_difference == 0:
        elo_score = 0.5
    elif goal_difference > 0:
        elo_score = 1
    else:
        elo_score = 0
    delta = abs(goal_difference)
    k = CONSTANTS['k_base'] * np.power((1 + delta), CONSTANTS['lambda'])
    elo_home_new = home.elo + k * (elo_score - home_positive_result)
    elo_away_new = away.elo + k * (home_positive_result - elo_score)
    return elo_home_new, elo_away_new


def play_game(home: Club, away: Club) -> None:
    """
    Function that runs the simulation of the game. First it calculates the winner, than the amount of goals each team
    scored, new elo for both clubs and than writes the result to the data of the clubs
    :param home: Club playing on the home field
    :param away: Club playing on the away field
    """
    outcome = add_result(home, away)
    goals = add_goals(home, away, outcome)
    new_elo = elo_change(home, away, goals[0] - goals[1])
    if outcome == '1':
        home.add_result(3, goals[0], goals[1], new_elo[0])
        away.add_result(0, goals[1], goals[0], new_elo[1])
    if outcome == 'X':
        home.add_result(1, goals[0], goals[1], new_elo[0])
        away.add_result(1, goals[1], goals[0], new_elo[1])
    if outcome == '2':
        home.add_result(0, goals[0], goals[1], new_elo[0])
        away.add_result(3, goals[1], goals[0], new_elo[1])


def play_all_games(teams: Dict[str, Club]) -> None:
    """
    Function that plays all games of the one league. This method SUCKSSSS, but it works!!! In future updates I will
     probably add scraper for webpage so I dont need to write so much text
    :param teams: dictionary of teams
    """

    # 1st Leg
    play_game(teams['Liverpool'], teams['Norwich'])
    play_game(teams['West Ham'], teams['Manchester City'])
    play_game(teams['Crystal Palace'], teams['Everton'])
    play_game(teams['Burnley'], teams['Southampton'])
    play_game(teams['Watford'], teams['Brighton'])
    play_game(teams['Bournemouth'], teams['Sheffield'])
    play_game(teams['Tottenham'], teams['Aston Villa'])
    play_game(teams['Leicester'], teams['Wolverhampton'])
    play_game(teams['Newcastle'], teams['Arsenal'])
    play_game(teams['Manchester United'], teams['Chelsea'])
    # 2st Leg
    play_game(teams['Arsenal'], teams['Burnley'])
    play_game(teams['Southampton'], teams['Liverpool'])
    play_game(teams['Brighton'], teams['West Ham'])
    play_game(teams['Everton'], teams['Watford'])
    play_game(teams['Norwich'], teams['Newcastle'])
    play_game(teams['Aston Villa'], teams['Bournemouth'])
    play_game(teams['Manchester City'], teams['Tottenham'])
    play_game(teams['Sheffield'], teams['Crystal Palace'])
    play_game(teams['Chelsea'], teams['Leicester'])
    play_game(teams['Wolverhampton'], teams['Manchester United'])
    # 3st Leg
    play_game(teams['Aston Villa'], teams['Everton'])
    play_game(teams['Norwich'], teams['Chelsea'])
    play_game(teams['Brighton'], teams['Southampton'])
    play_game(teams['Manchester United'], teams['Crystal Palace'])
    play_game(teams['Wolverhampton'], teams['Burnley'])
    play_game(teams['Watford'], teams['West Ham'])
    play_game(teams['Sheffield'], teams['Leicester'])
    play_game(teams['Liverpool'], teams['Arsenal'])
    play_game(teams['Bournemouth'], teams['Manchester City'])
    play_game(teams['Tottenham'], teams['Newcastle'])
    # 4st Leg
    play_game(teams['Southampton'], teams['Manchester United'])
    play_game(teams['Crystal Palace'], teams['Aston Villa'])
    play_game(teams['Chelsea'], teams['Sheffield'])
    play_game(teams['Newcastle'], teams['Watford'])
    play_game(teams['Manchester City'], teams['Brighton'])
    play_game(teams['West Ham'], teams['Norwich'])
    play_game(teams['Leicester'], teams['Bournemouth'])
    play_game(teams['Burnley'], teams['Liverpool'])
    play_game(teams['Everton'], teams['Wolverhampton'])
    play_game(teams['Arsenal'], teams['Tottenham'])
    # 5st Leg
    play_game(teams['Liverpool'], teams['Newcastle'])
    play_game(teams['Manchester United'], teams['Leicester'])
    play_game(teams['Sheffield'], teams['Southampton'])
    play_game(teams['Brighton'], teams['Burnley'])
    play_game(teams['Wolverhampton'], teams['Chelsea'])
    play_game(teams['Tottenham'], teams['Crystal Palace'])
    play_game(teams['Norwich'], teams['Manchester City'])
    play_game(teams['Bournemouth'], teams['Everton'])
    play_game(teams['Watford'], teams['Arsenal'])
    play_game(teams['Aston Villa'], teams['West Ham'])
    # 6st Leg
    play_game(teams['Southampton'], teams['Bournemouth'])
    play_game(teams['Leicester'], teams['Tottenham'])
    play_game(teams['Burnley'], teams['Norwich'])
    play_game(teams['Everton'], teams['Sheffield'])
    play_game(teams['Crystal Palace'], teams['Wolverhampton'])
    play_game(teams['Manchester City'], teams['Watford'])
    play_game(teams['Newcastle'], teams['Brighton'])
    play_game(teams['West Ham'], teams['Manchester United'])
    play_game(teams['Arsenal'], teams['Aston Villa'])
    play_game(teams['Chelsea'], teams['Liverpool'])
    # 7st Leg
    play_game(teams['Sheffield'], teams['Liverpool'])
    play_game(teams['Crystal Palace'], teams['Norwich'])
    play_game(teams['Aston Villa'], teams['Burnley'])
    play_game(teams['Bournemouth'], teams['West Ham'])
    play_game(teams['Wolverhampton'], teams['Watford'])
    play_game(teams['Tottenham'], teams['Southampton'])
    play_game(teams['Chelsea'], teams['Brighton'])
    play_game(teams['Leicester'], teams['Newcastle'])
    play_game(teams['Everton'], teams['Manchester City'])
    play_game(teams['Manchester United'], teams['Arsenal'])
    # 8st Leg
    play_game(teams['Norwich'], teams['Aston Villa'])
    play_game(teams['Southampton'], teams['Chelsea'])
    play_game(teams['West Ham'], teams['Crystal Palace'])
    play_game(teams['Watford'], teams['Sheffield'])
    play_game(teams['Burnley'], teams['Everton'])
    play_game(teams['Manchester City'], teams['Wolverhampton'])
    play_game(teams['Brighton'], teams['Tottenham'])
    play_game(teams['Liverpool'], teams['Leicester'])
    play_game(teams['Arsenal'], teams['Bournemouth'])
    play_game(teams['Newcastle'], teams['Manchester United'])
    # 9st Leg
    play_game(teams['Aston Villa'], teams['Brighton'])
    play_game(teams['Tottenham'], teams['Watford'])
    play_game(teams['Manchester United'], teams['Liverpool'])
    play_game(teams['Wolverhampton'], teams['Southampton'])
    play_game(teams['Crystal Palace'], teams['Manchester City'])
    play_game(teams['Everton'], teams['West Ham'])
    play_game(teams['Chelsea'], teams['Newcastle'])
    play_game(teams['Sheffield'], teams['Arsenal'])
    play_game(teams['Bournemouth'], teams['Norwich'])
    play_game(teams['Leicester'], teams['Burnley'])
    # 10st Leg
    play_game(teams['Arsenal'], teams['Crystal Palace'])
    play_game(teams['Manchester City'], teams['Aston Villa'])
    play_game(teams['Southampton'], teams['Leicester'])
    play_game(teams['Liverpool'], teams['Tottenham'])
    play_game(teams['Newcastle'], teams['Wolverhampton'])
    play_game(teams['Watford'], teams['Bournemouth'])
    play_game(teams['Brighton'], teams['Everton'])
    play_game(teams['West Ham'], teams['Sheffield'])
    play_game(teams['Norwich'], teams['Manchester United'])
    play_game(teams['Burnley'], teams['Chelsea'])
    # 11st Leg
    play_game(teams['West Ham'], teams['Newcastle'])
    play_game(teams['Aston Villa'], teams['Liverpool'])
    play_game(teams['Watford'], teams['Chelsea'])
    play_game(teams['Arsenal'], teams['Wolverhampton'])
    play_game(teams['Everton'], teams['Tottenham'])
    play_game(teams['Bournemouth'], teams['Manchester United'])
    play_game(teams['Crystal Palace'], teams['Leicester'])
    play_game(teams['Sheffield'], teams['Burnley'])
    play_game(teams['Brighton'], teams['Norwich'])
    play_game(teams['Manchester City'], teams['Southampton'])
    # 12st Leg
    play_game(teams['Burnley'], teams['West Ham'])
    play_game(teams['Wolverhampton'], teams['Aston Villa'])
    play_game(teams['Leicester'], teams['Arsenal'])
    play_game(teams['Newcastle'], teams['Bournemouth'])
    play_game(teams['Southampton'], teams['Everton'])
    play_game(teams['Liverpool'], teams['Manchester City'])
    play_game(teams['Norwich'], teams['Watford'])
    play_game(teams['Chelsea'], teams['Crystal Palace'])
    play_game(teams['Manchester United'], teams['Brighton'])
    play_game(teams['Tottenham'], teams['Sheffield'])
    # 13st Leg
    play_game(teams['West Ham'], teams['Tottenham'])
    play_game(teams['Arsenal'], teams['Southampton'])
    play_game(teams['Brighton'], teams['Leicester'])
    play_game(teams['Watford'], teams['Burnley'])
    play_game(teams['Sheffield'], teams['Manchester United'])
    play_game(teams['Crystal Palace'], teams['Liverpool'])
    play_game(teams['Bournemouth'], teams['Wolverhampton'])
    play_game(teams['Everton'], teams['Norwich'])
    play_game(teams['Aston Villa'], teams['Newcastle'])
    play_game(teams['Manchester City'], teams['Chelsea'])
    # 14st Leg
    play_game(teams['Liverpool'], teams['Brighton'])
    play_game(teams['Newcastle'], teams['Manchester City'])
    play_game(teams['Norwich'], teams['Arsenal'])
    play_game(teams['Burnley'], teams['Crystal Palace'])
    play_game(teams['Leicester'], teams['Everton'])
    play_game(teams['Southampton'], teams['Watford'])
    play_game(teams['Chelsea'], teams['West Ham'])
    play_game(teams['Tottenham'], teams['Bournemouth'])
    play_game(teams['Manchester United'], teams['Aston Villa'])
    play_game(teams['Wolverhampton'], teams['Sheffield'])
    # 15st Leg
    play_game(teams['Leicester'], teams['Watford'])
    play_game(teams['Sheffield'], teams['Newcastle'])
    play_game(teams['Wolverhampton'], teams['West Ham'])
    play_game(teams['Burnley'], teams['Manchester City'])
    play_game(teams['Arsenal'], teams['Brighton'])
    play_game(teams['Manchester United'], teams['Tottenham'])
    play_game(teams['Chelsea'], teams['Aston Villa'])
    play_game(teams['Southampton'], teams['Norwich'])
    play_game(teams['Crystal Palace'], teams['Bournemouth'])
    play_game(teams['Liverpool'], teams['Everton'])
    # 16st Leg
    play_game(teams['Aston Villa'], teams['Leicester'])
    play_game(teams['Brighton'], teams['Wolverhampton'])
    play_game(teams['Bournemouth'], teams['Liverpool'])
    play_game(teams['Manchester City'], teams['Manchester United'])
    play_game(teams['Tottenham'], teams['Burnley'])
    play_game(teams['Watford'], teams['Crystal Palace'])
    play_game(teams['Everton'], teams['Chelsea'])
    play_game(teams['Newcastle'], teams['Southampton'])
    play_game(teams['West Ham'], teams['Arsenal'])
    play_game(teams['Norwich'], teams['Sheffield'])
    # 17st Leg
    play_game(teams['Liverpool'], teams['Watford'])
    play_game(teams['Chelsea'], teams['Bournemouth'])
    play_game(teams['Sheffield'], teams['Aston Villa'])
    play_game(teams['Leicester'], teams['Norwich'])
    play_game(teams['Burnley'], teams['Newcastle'])
    play_game(teams['Crystal Palace'], teams['Brighton'])
    play_game(teams['Arsenal'], teams['Manchester City'])
    play_game(teams['Southampton'], teams['West Ham'])
    play_game(teams['Manchester United'], teams['Everton'])
    play_game(teams['Wolverhampton'], teams['Tottenham'])
    # 18st Leg
    play_game(teams['Tottenham'], teams['Chelsea'])
    play_game(teams['West Ham'], teams['Liverpool'])
    play_game(teams['Newcastle'], teams['Crystal Palace'])
    play_game(teams['Aston Villa'], teams['Southampton'])
    play_game(teams['Watford'], teams['Manchester United'])
    play_game(teams['Norwich'], teams['Wolverhampton'])
    play_game(teams['Everton'], teams['Arsenal'])
    play_game(teams['Brighton'], teams['Sheffield'])
    play_game(teams['Manchester City'], teams['Leicester'])
    play_game(teams['Bournemouth'], teams['Burnley'])
    # 19st Leg
    play_game(teams['Bournemouth'], teams['Arsenal'])
    play_game(teams['Manchester United'], teams['Newcastle'])
    play_game(teams['Sheffield'], teams['Watford'])
    play_game(teams['Chelsea'], teams['Southampton'])
    play_game(teams['Aston Villa'], teams['Norwich'])
    play_game(teams['Tottenham'], teams['Brighton'])
    play_game(teams['Crystal Palace'], teams['West Ham'])
    play_game(teams['Wolverhampton'], teams['Manchester City'])
    play_game(teams['Everton'], teams['Burnley'])
    play_game(teams['Leicester'], teams['Liverpool'])
    # 20 Leg
    play_game(teams['Arsenal'], teams['Chelsea'])
    play_game(teams['Southampton'], teams['Crystal Palace'])
    play_game(teams['Norwich'], teams['Tottenham'])
    play_game(teams['Brighton'], teams['Bournemouth'])
    play_game(teams['Burnley'], teams['Manchester United'])
    play_game(teams['West Ham'], teams['Leicester'])
    play_game(teams['Manchester City'], teams['Sheffield'])
    play_game(teams['Newcastle'], teams['Everton'])
    play_game(teams['Watford'], teams['Aston Villa'])
    play_game(teams['Liverpool'], teams['Wolverhampton'])
    # 21 Leg
    play_game(teams['Newcastle'], teams['Leicester'])
    play_game(teams['Brighton'], teams['Chelsea'])
    play_game(teams['West Ham'], teams['Bournemouth'])
    play_game(teams['Watford'], teams['Wolverhampton'])
    play_game(teams['Liverpool'], teams['Sheffield'])
    play_game(teams['Arsenal'], teams['Manchester United'])
    play_game(teams['Manchester City'], teams['Everton'])
    play_game(teams['Southampton'], teams['Tottenham'])
    play_game(teams['Burnley'], teams['Aston Villa'])
    play_game(teams['Norwich'], teams['Crystal Palace'])
    # 22 Leg
    play_game(teams['Everton'], teams['Brighton'])
    play_game(teams['Sheffield'], teams['West Ham'])
    play_game(teams['Leicester'], teams['Southampton'])
    play_game(teams['Aston Villa'], teams['Manchester City'])
    play_game(teams['Manchester United'], teams['Norwich'])
    play_game(teams['Bournemouth'], teams['Watford'])
    play_game(teams['Chelsea'], teams['Burnley'])
    play_game(teams['Crystal Palace'], teams['Arsenal'])
    play_game(teams['Wolverhampton'], teams['Newcastle'])
    play_game(teams['Tottenham'], teams['Liverpool'])
    # 23 Leg
    play_game(teams['Watford'], teams['Tottenham'])
    play_game(teams['Newcastle'], teams['Chelsea'])
    play_game(teams['Brighton'], teams['Aston Villa'])
    play_game(teams['Burnley'], teams['Leicester'])
    play_game(teams['Manchester City'], teams['Crystal Palace'])
    play_game(teams['West Ham'], teams['Everton'])
    play_game(teams['Arsenal'], teams['Sheffield'])
    play_game(teams['Liverpool'], teams['Manchester United'])
    play_game(teams['Norwich'], teams['Bournemouth'])
    play_game(teams['Southampton'], teams['Wolverhampton'])
    # 24 Leg
    play_game(teams['Bournemouth'], teams['Brighton'])
    play_game(teams['Wolverhampton'], teams['Liverpool'])
    play_game(teams['Aston Villa'], teams['Watford'])
    play_game(teams['Leicester'], teams['West Ham'])
    play_game(teams['Sheffield'], teams['Manchester City'])
    play_game(teams['Everton'], teams['Newcastle'])
    play_game(teams['Manchester United'], teams['Burnley'])
    play_game(teams['Chelsea'], teams['Arsenal'])
    play_game(teams['Tottenham'], teams['Norwich'])
    play_game(teams['Crystal Palace'], teams['Southampton'])
    # 25 Leg
    play_game(teams['Tottenham'], teams['Manchester City'])
    play_game(teams['Burnley'], teams['Arsenal'])
    play_game(teams['Newcastle'], teams['Norwich'])
    play_game(teams['Manchester United'], teams['Wolverhampton'])
    play_game(teams['Crystal Palace'], teams['Sheffield'])
    play_game(teams['West Ham'], teams['Brighton'])
    play_game(teams['Leicester'], teams['Chelsea'])
    play_game(teams['Bournemouth'], teams['Aston Villa'])
    play_game(teams['Watford'], teams['Everton'])
    play_game(teams['Liverpool'], teams['Southampton'])
    # 26 Leg
    play_game(teams['Aston Villa'], teams['Tottenham'])
    play_game(teams['Brighton'], teams['Watford'])
    play_game(teams['Southampton'], teams['Burnley'])
    play_game(teams['Everton'], teams['Crystal Palace'])
    play_game(teams['Norwich'], teams['Liverpool'])
    play_game(teams['Wolverhampton'], teams['Leicester'])
    play_game(teams['Chelsea'], teams['Manchester United'])
    play_game(teams['Manchester City'], teams['West Ham'])
    play_game(teams['Arsenal'], teams['Newcastle'])
    play_game(teams['Sheffield'], teams['Bournemouth'])
    # 27 Leg
    play_game(teams['Crystal Palace'], teams['Newcastle'])
    play_game(teams['Arsenal'], teams['Everton'])
    play_game(teams['Burnley'], teams['Bournemouth'])
    play_game(teams['Leicester'], teams['Manchester City'])
    play_game(teams['Sheffield'], teams['Brighton'])
    play_game(teams['Wolverhampton'], teams['Norwich'])
    play_game(teams['Liverpool'], teams['West Ham'])
    play_game(teams['Southampton'], teams['Aston Villa'])
    play_game(teams['Manchester United'], teams['Watford'])
    play_game(teams['Chelsea'], teams['Tottenham'])
    # 28 Leg
    play_game(teams['Bournemouth'], teams['Chelsea'])
    play_game(teams['Newcastle'], teams['Burnley'])
    play_game(teams['Norwich'], teams['Leicester'])
    play_game(teams['West Ham'], teams['Southampton'])
    play_game(teams['Brighton'], teams['Crystal Palace'])
    play_game(teams['Everton'], teams['Manchester United'])
    play_game(teams['Tottenham'], teams['Wolverhampton'])
    play_game(teams['Aston Villa'], teams['Sheffield'])
    play_game(teams['Manchester City'], teams['Arsenal'])
    play_game(teams['Watford'], teams['Liverpool'])
    # 29 Leg
    play_game(teams['Wolverhampton'], teams['Brighton'])
    play_game(teams['Burnley'], teams['Tottenham'])
    play_game(teams['Arsenal'], teams['West Ham'])
    play_game(teams['Leicester'], teams['Aston Villa'])
    play_game(teams['Southampton'], teams['Newcastle'])
    play_game(teams['Liverpool'], teams['Bournemouth'])
    play_game(teams['Sheffield'], teams['Norwich'])
    play_game(teams['Crystal Palace'], teams['Watford'])
    play_game(teams['Chelsea'], teams['Everton'])
    play_game(teams['Manchester United'], teams['Manchester City'])
    # 30 Leg
    play_game(teams['West Ham'], teams['Wolverhampton'])
    play_game(teams['Brighton'], teams['Arsenal'])
    play_game(teams['Tottenham'], teams['Manchester United'])
    play_game(teams['Everton'], teams['Liverpool'])
    play_game(teams['Norwich'], teams['Southampton'])
    play_game(teams['Newcastle'], teams['Sheffield'])
    play_game(teams['Watford'], teams['Leicester'])
    play_game(teams['Manchester City'], teams['Burnley'])
    play_game(teams['Aston Villa'], teams['Chelsea'])
    play_game(teams['Bournemouth'], teams['Crystal Palace'])
    # 31 Leg
    play_game(teams['Norwich'], teams['Everton'])
    play_game(teams['Leicester'], teams['Brighton'])
    play_game(teams['Chelsea'], teams['Manchester City'])
    play_game(teams['Southampton'], teams['Arsenal'])
    play_game(teams['Newcastle'], teams['Aston Villa'])
    play_game(teams['Manchester United'], teams['Sheffield'])
    play_game(teams['Tottenham'], teams['West Ham'])
    play_game(teams['Burnley'], teams['Watford'])
    play_game(teams['Wolverhampton'], teams['Bournemouth'])
    play_game(teams['Liverpool'], teams['Crystal Palace'])
    # 32 Leg
    play_game(teams['Manchester City'], teams['Liverpool'])
    play_game(teams['Aston Villa'], teams['Wolverhampton'])
    play_game(teams['Brighton'], teams['Manchester United'])
    play_game(teams['Arsenal'], teams['Norwich'])
    play_game(teams['Crystal Palace'], teams['Burnley'])
    play_game(teams['Watford'], teams['Southampton'])
    play_game(teams['Sheffield'], teams['Tottenham'])
    play_game(teams['Bournemouth'], teams['Newcastle'])
    play_game(teams['West Ham'], teams['Chelsea'])
    play_game(teams['Everton'], teams['Leicester'])
    # 33 Leg
    play_game(teams['Southampton'], teams['Manchester City'])
    play_game(teams['Leicester'], teams['Crystal Palace'])
    play_game(teams['Wolverhampton'], teams['Arsenal'])
    play_game(teams['Liverpool'], teams['Aston Villa'])
    play_game(teams['Newcastle'], teams['West Ham'])
    play_game(teams['Burnley'], teams['Sheffield'])
    play_game(teams['Chelsea'], teams['Watford'])
    play_game(teams['Norwich'], teams['Brighton'])
    play_game(teams['Tottenham'], teams['Everton'])
    play_game(teams['Manchester United'], teams['Bournemouth'])
    # 34 Leg
    play_game(teams['Arsenal'], teams['Leicester'])
    play_game(teams['Brighton'], teams['Liverpool'])
    play_game(teams['Sheffield'], teams['Wolverhampton'])
    play_game(teams['Everton'], teams['Southampton'])
    play_game(teams['Aston Villa'], teams['Manchester United'])
    play_game(teams['Manchester City'], teams['Newcastle'])
    play_game(teams['Bournemouth'], teams['Tottenham'])
    play_game(teams['West Ham'], teams['Burnley'])
    play_game(teams['Watford'], teams['Norwich'])
    play_game(teams['Crystal Palace'], teams['Chelsea'])
    # 35 Leg
    play_game(teams['Manchester United'], teams['Southampton'])
    play_game(teams['Liverpool'], teams['Burnley'])
    play_game(teams['Wolverhampton'], teams['Everton'])
    play_game(teams['Sheffield'], teams['Chelsea'])
    play_game(teams['Bournemouth'], teams['Leicester'])
    play_game(teams['Brighton'], teams['Manchester City'])
    play_game(teams['Watford'], teams['Newcastle'])
    play_game(teams['Norwich'], teams['West Ham'])
    play_game(teams['Tottenham'], teams['Arsenal'])
    play_game(teams['Aston Villa'], teams['Crystal Palace'])
    # 36 Leg
    play_game(teams['Everton'], teams['Aston Villa'])
    play_game(teams['Chelsea'], teams['Norwich'])
    play_game(teams['Southampton'], teams['Brighton'])
    play_game(teams['Burnley'], teams['Wolverhampton'])
    play_game(teams['Manchester City'], teams['Bournemouth'])
    play_game(teams['Crystal Palace'], teams['Manchester United'])
    play_game(teams['Leicester'], teams['Sheffield'])
    play_game(teams['West Ham'], teams['Watford'])
    play_game(teams['Arsenal'], teams['Liverpool'])
    play_game(teams['Newcastle'], teams['Tottenham'])
    # 37 Leg
    play_game(teams['Tottenham'], teams['Leicester'])
    play_game(teams['Bournemouth'], teams['Southampton'])
    play_game(teams['Norwich'], teams['Burnley'])
    play_game(teams['Aston Villa'], teams['Arsenal'])
    play_game(teams['Wolverhampton'], teams['Crystal Palace'])
    play_game(teams['Manchester United'], teams['West Ham'])
    play_game(teams['Sheffield'], teams['Everton'])
    play_game(teams['Watford'], teams['Manchester City'])
    play_game(teams['Brighton'], teams['Newcastle'])
    play_game(teams['Liverpool'], teams['Chelsea'])
    # 38 Leg
    play_game(teams['Burnley'], teams['Brighton'])
    play_game(teams['Leicester'], teams['Manchester United'])
    play_game(teams['Chelsea'], teams['Wolverhampton'])
    play_game(teams['Crystal Palace'], teams['Tottenham'])
    play_game(teams['Newcastle'], teams['Liverpool'])
    play_game(teams['West Ham'], teams['Aston Villa'])
    play_game(teams['Manchester City'], teams['Norwich'])
    play_game(teams['Arsenal'], teams['Watford'])
    play_game(teams['Southampton'], teams['Sheffield'])
    play_game(teams['Everton'], teams['Bournemouth'])


def save_data(file: str, data: Union[Dict[str, Club], int]) -> None:
    """
    Function that saves the data to pickle file
    :param file: file name
    :param data: dictionary to save
    """
    with open(file, 'wb') as handle:
        pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load_data(file: str) -> Dict[str, Club]:
    """
    Function that loads the data about previously calculates standings
    :param file: file name
    :return: dictionary that contains the data about teams
    """
    with open(file, 'rb') as handle:
        return pickle.load(handle)


"""
Dictionary used to store all clubs in the league, for each league you have to manually write that information

Info: Name, ELO at the start of the league, Home goals scored, Home goals received, Away goals scored and
Away goals received (all of that last season last season)
"""
clubs_in_league = {}
clubs_in_league['Liverpool'] = Club('Liverpool', 2043, 55, 10, 34, 12)
clubs_in_league['Manchester City'] = Club('Manchester City', 2037, 57, 12, 38, 11)
clubs_in_league['Tottenham'] = Club('Tottenham', 1891, 34, 16, 33, 23)
clubs_in_league['Chelsea'] = Club('Chelsea', 1883, 39, 12, 24, 27)
clubs_in_league['Arsenal'] = Club('Arsenal', 1866, 42, 16, 31, 35)
clubs_in_league['Manchester United'] = Club('Manchester United', 1838, 33, 25, 32, 29)
clubs_in_league['Everton'] = Club('Everton', 1769, 30, 21, 24, 25)
clubs_in_league['Crystal Palace'] = Club('Crystal Palace', 1742, 19, 23, 32, 30)
clubs_in_league['Leicester'] = Club('Leicester', 1738, 24, 20, 27, 28)
clubs_in_league['West Ham'] = Club('West Ham', 1729, 32, 27, 20, 28)
clubs_in_league['Wolverhampton'] = Club('Wolverhampton', 1719, 28, 21, 19, 25)
clubs_in_league['Newcastle'] = Club('Newcastle', 1715, 24, 25, 18, 23)
clubs_in_league['Bournemouth'] = Club('Bournemouth', 1690, 30, 25, 26, 45)
clubs_in_league['Watford'] = Club('Watford', 1685, 26, 28, 26, 31)
clubs_in_league['Burnley'] = Club('Burnley', 1681, 24, 32, 21, 36)
clubs_in_league['Southampton'] = Club('Southampton', 1673, 27, 30, 18, 35)
clubs_in_league['Brighton'] = Club('Brighton', 1616, 19, 28, 16, 32)
# this clubs didn't play in Premier League so I took goals of teams that were relegated and added 3 to scored goals
# if elo difference was > 20
clubs_in_league['Norwich'] = Club('Norwich', 1631, 23, 38, 16, 31)
clubs_in_league['Sheffield'] = Club('Sheffield', 1619, 25, 36, 15, 45)
clubs_in_league['Aston Villa'] = Club('Aston Villa', 1612, 18, 31, 15, 45)


def main() -> None:
    """
    Main function of the program. First it make all variables needed for it to run, then it loads the previous results
    if there are any, than program starts the calculations, saves calculations on disc and calculate remaining time.
    Once the program is done it prints out the results and user can write anyting to close the program
    """
    teams = copy.deepcopy(clubs_in_league)
    standings_all = StandingsFull(name='Premier League', clubs=teams)
    standings_all.standing_calculated = 0
    if os.path.isfile('data1.pickle') and os.path.isfile('data2.pickle'):
        standings_all.standing_calculated = load_data('data2.pickle')
        standings_all.clubs = load_data('data1.pickle')
    start_time = time.time_ns()
    while standings_all.standing_calculated < MAX:
        teams = copy.deepcopy(clubs_in_league)
        standings = Standings(name='Premier League', clubs=teams)
        play_all_games(standings.clubs)
        standings.sort_standings()
        for j in range(20):
            standings_all.clubs[list(standings.clubs.keys())[j]].placings[j] += 1
        standings_all.include(standings)
        if not standings_all.standing_calculated % 1000:
            save_data('data1.pickle', standings_all.clubs)
            save_data('data2.pickle', standings_all.standing_calculated)
            end_time = time.time_ns()
            remaining_time = (MAX - standings_all.standing_calculated) * (end_time - start_time) / (10 ** 12)
            print('Calculated {} outcomes. ({:9.4%} of total number).'.format(standings_all.standing_calculated,
                                                                              (standings_all.standing_calculated/MAX)),
                  end=' ')
            m, s = divmod(remaining_time, 60)
            h, m = divmod(m, 60)
            print("Estimated remaining time: ({:02d} hours, {:02d} minutes, {:02d} seconds)".format(int(h), int(m),
                                                                                                    int(s)))
            start_time = time.time_ns()
    save_data('data1.pickle', standings_all.clubs)
    save_data('data2.pickle', standings_all.standing_calculated)
    standings_all.sort_standings()
    standings_all.get_average()
    os.system('cls')
    print(standings_all)
    input()


def print_results():
    """
    Function used only for printing the result of calculations
    """
    teams = copy.deepcopy(clubs_in_league)
    standings_all = StandingsFull(name='Premier League', clubs=teams)
    standings_all.standing_calculated = 0
    if os.path.isfile('data1.pickle') and os.path.isfile('data2.pickle'):
        standings_all.standing_calculated = load_data('data2.pickle')
        standings_all.clubs = load_data('data1.pickle')
    standings_all.sort_standings()
    standings_all.get_average()
    print(standings_all)
    # print(standings_all.percentages())
    input()


if __name__ == '__main__':
    """ Use main() if you want to start calculations, otherwise use print_results() """
    print_results()
