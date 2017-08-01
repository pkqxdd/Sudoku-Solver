#!/usr/local/bin/python3.6
import argparse
from main import main
from GUI_input import GUI_input

parser=argparse.ArgumentParser(description='Find a solution of a Sudoku board')
parser.add_argument('Board',metavar='Board',type=str,help='A string of 81 digits representing the board')
parser.add_argument('--show-process',action='store_true',default=False,dest='display',help='If given, the process of finding a solution will be displayed.')

args=parser.parse_args()
b=args.Board
display=args.display

if __name__ == '__main__':

	if b == 'GUI':
		GUI_input()
	else:
		try:
			int(b)
			if not len(b)==81:
				raise ValueError
		except ValueError:
			raise ValueError('The board must be a string with 81 digits')


		print('Solution:',main(b,display))
