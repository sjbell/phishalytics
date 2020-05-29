from __future__ import division
from pyfiglet import Figlet

from asciimatics.effects import Scroll, Mirage, Wipe, Cycle, Matrix, \
		BannerText, Stars, Print, RandomNoise
from asciimatics.particles import DropScreen
from asciimatics.renderers import FigletText, SpeechBubble, Rainbow, Fire
from asciimatics.widgets import Background
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def _credits(screen):
		scenes = []

		effects = [
				Matrix(screen, stop_frame=200),
				Print(screen,
							FigletText("Catch Me", "banner3"),
							screen.height - 31, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=50,
							stop_frame=200),
				Print(screen,
							FigletText("(On Time)", "banner3"),
							screen.height - 21, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=75,
							stop_frame=200),
				Print(screen,
							FigletText("If You Can", "banner3"),
							screen.height - 11, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=100,
							stop_frame=200)
		]
		scenes.append(Scene(effects, 250, clear=False))

		effects = [
			Background(screen, bg=Screen.COLOUR_BLACK),
				Print(screen,
							FigletText("Understanding the", "banner"),
							screen.height - 31, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=0,
							stop_frame=200),
				Print(screen,
							FigletText("Effectiveness of", "banner"),
							screen.height - 21, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=25,
							stop_frame=200),
				Print(screen,
							FigletText("Twitter URL Blacklist", "banner"),
							screen.height - 11, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=50,
							stop_frame=200)
		]
		scenes.append(Scene(effects, 250, clear=False))
		

		effects = [
			Background(screen, bg=Screen.COLOUR_BLACK),
				Print(screen,
							FigletText("Authors:", "banner"),
							screen.height - 21,
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=0,
							stop_frame=50,
							clear=1),
				Print(screen,
							FigletText("Simon Bell", "banner"),
							screen.height - 21,
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=50,
							stop_frame=100,
							clear=1),
				Print(screen,
							FigletText("Lorenzo Cavallaro", "banner"),
							screen.height - 21, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							clear=1,
							start_frame=100,
							stop_frame=150),
				Print(screen,
							FigletText("Kenny Paterson", "banner"),
							screen.height - 21, 
							colour=Screen.COLOUR_WHITE,
							bg=Screen.COLOUR_WHITE,
							speed=1,
							start_frame=150,
							stop_frame=200),
		]
		scenes.append(Scene(effects))

		effects = [
			Background(screen, bg=Screen.COLOUR_BLACK),
				BannerText(
						screen,
						FigletText(
								"Live  measurement  experiments  in  progress", font='banner3', width=400),
						#screen.height // 2 - 3,
						screen.height -21,
						Screen.COLOUR_GREEN)
		]
		scenes.append(Scene(effects))

		screen.play(scenes, stop_on_resize=True)

if __name__ == "__main__":
		while True:
				try:
						Screen.wrapper(_credits)
						sys.exit(0)
				except ResizeScreenError:
						pass
