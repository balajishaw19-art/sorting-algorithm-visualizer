import pygame
import random
import math

pygame.init()


def get_fitted_font(font_name, text, max_width, base_size, min_size=14, step=2):
	"""
	Returns a SysFont sized so that `text` renders no wider than max_width.

	Not every computer has the same fonts installed. If 'comicsans' isn't
	found, Pygame silently substitutes a different font - and some
	substitutes (e.g. Courier New) are much wider per character. Rendering
	at a fixed size can then overflow past the edges of the window. This
	shrinks the font a little at a time until the text actually fits,
	so the title/controls text always stays fully on screen.
	"""
	size = base_size
	font = pygame.font.SysFont(font_name, size)

	while font.size(text)[0] > max_width and size > min_size:
		size -= step
		font = pygame.font.SysFont(font_name, size)

	return font


class DrawInformation:
	"""
	Holds everything needed to draw the current state of the program:
	the window, the list of numbers, and the math used to turn those
	numbers into bars on screen.

	We use a class (instead of just a bunch of loose variables) because
	the sorting functions, the draw functions, and the main loop all need
	to share this same information. Passing one object around is much
	simpler than passing 5-6 separate arguments everywhere.
	"""

	BLACK = 0, 0, 0
	WHITE = 255, 255, 255
	GREEN = 0, 255, 0
	RED = 255, 0, 0
	BACKGROUND_COLOR = WHITE

	# Bars alternate between these 3 shades of grey so that neighbouring
	# bars are visually distinguishable even when they are not highlighted.
	GRADIENTS = [
		(128, 128, 128),
		(160, 160, 160),
		(192, 192, 192)
	]

	# Base (maximum) sizes for our text - get_fitted_font() will shrink
	# these if needed so text never overflows the window's width.
	FONT_NAME = 'comicsans'
	TITLE_SIZE = 40
	TEXT_SIZE = 24

	# Padding so bars don't touch the very edge of the window and there
	# is room at the top for the title/controls text.
	SIDE_PAD = 100
	TOP_PAD = 130

	def __init__(self, width, height, lst):
		self.width = width
		self.height = height

		# self.window is the actual pygame surface we draw everything onto.
		# "self" just means "this particular DrawInformation object" -
		# it lets every method reuse the same window/list/etc.
		self.window = pygame.display.set_mode((width, height))
		pygame.display.set_caption("Sorting Algorithm Visualizer")
		self.set_list(lst)

	def set_list(self, lst):
		"""
		Called whenever we get a brand new list (start of the program,
		or after pressing Reset). It works out the math needed to convert
		list values into bar positions/heights, so draw_list() doesn't
		have to recalculate this for every single bar.
		"""
		self.lst = lst
		self.min_val = min(lst)
		self.max_val = max(lst)

		# Width of a single bar so that all bars together fill the window
		# (minus the side padding), regardless of list length.
		self.block_width = round((self.width - self.SIDE_PAD) / len(lst))
		# How many pixels tall each "1 unit" of value should be, so the
		# tallest bar fits inside the window (minus the top padding).
		self.block_height = math.floor((self.height - self.TOP_PAD) / (self.max_val - self.min_val))
		self.start_x = self.SIDE_PAD // 2


def draw(draw_info, algo_name, ascending):
	"""Draws the whole screen: background, title, controls text, and bars."""
	draw_info.window.fill(draw_info.BACKGROUND_COLOR)

	# Leave a small margin on each side so text never touches the edges.
	max_text_width = draw_info.width - 40

	title_text = f"{algo_name} - {'Ascending' if ascending else 'Descending'}"
	title_font = get_fitted_font(draw_info.FONT_NAME, title_text, max_text_width, draw_info.TITLE_SIZE, min_size=22)
	title = title_font.render(title_text, 1, draw_info.GREEN)
	draw_info.window.blit(title, (draw_info.width / 2 - title.get_width() / 2, 5))

	controls_text = "R - Reset | SPACE - Start Sorting | A - Ascending | D - Descending"
	controls_font = get_fitted_font(draw_info.FONT_NAME, controls_text, max_text_width, draw_info.TEXT_SIZE)
	controls = controls_font.render(controls_text, 1, draw_info.BLACK)
	draw_info.window.blit(controls, (draw_info.width / 2 - controls.get_width() / 2, 52))

	sorting_text = "B - Bubble Sort | I - Insertion Sort | S - Selection Sort"
	sorting_font = get_fitted_font(draw_info.FONT_NAME, sorting_text, max_text_width, draw_info.TEXT_SIZE)
	sorting = sorting_font.render(sorting_text, 1, draw_info.BLACK)
	draw_info.window.blit(sorting, (draw_info.width / 2 - sorting.get_width() / 2, 82))

	draw_list(draw_info)
	pygame.display.update()


def draw_list(draw_info, color_positions={}, clear_bg=False):
	"""
	Draws every bar in the list.

	color_positions lets a sorting function highlight specific bars
	(e.g. the two bars currently being compared/swapped) by passing in
	a dict like {index: color}. clear_bg=True is used mid-sort, so we
	only redraw the bar area (not the whole window/title) - this is
	cheaper than calling draw() again every single step.
	"""
	lst = draw_info.lst

	if clear_bg:
		clear_rect = (
			draw_info.SIDE_PAD // 2, draw_info.TOP_PAD,
			draw_info.width - draw_info.SIDE_PAD, draw_info.height - draw_info.TOP_PAD
		)
		pygame.draw.rect(draw_info.window, draw_info.BACKGROUND_COLOR, clear_rect)

	for i, val in enumerate(lst):
		x = draw_info.start_x + i * draw_info.block_width
		y = draw_info.height - (val - draw_info.min_val) * draw_info.block_height

		color = draw_info.GRADIENTS[i % 3]
		if i in color_positions:
			color = color_positions[i]

		pygame.draw.rect(draw_info.window, color, (x, y, draw_info.block_width, draw_info.height))

	if clear_bg:
		pygame.display.update()


def generate_starting_list(n, min_val, max_val):
	"""Creates a fresh list of n random integers between min_val and max_val."""
	lst = []
	for _ in range(n):
		val = random.randint(min_val, max_val)
		lst.append(val)
	return lst


def bubble_sort(draw_info, ascending=True):
	"""
	Standard bubble sort, written as a GENERATOR (it uses `yield`).

	Every time we make a swap, we redraw the list and then `yield`.
	Pausing here (instead of returning) is what lets the main loop keep
	handling window/keyboard events between each visual step, instead of
	the whole list being sorted instantly in one frame.
	"""
	lst = draw_info.lst

	for i in range(len(lst) - 1):
		for j in range(len(lst) - 1 - i):
			num1 = lst[j]
			num2 = lst[j + 1]

			if (num1 > num2 and ascending) or (num1 < num2 and not ascending):
				lst[j], lst[j + 1] = lst[j + 1], lst[j]
				draw_list(draw_info, {j: draw_info.GREEN, j + 1: draw_info.RED}, True)
				yield True

	return lst


def insertion_sort(draw_info, ascending=True):
	"""Standard insertion sort, also written as a generator (same reason as bubble_sort)."""
	lst = draw_info.lst

	for i in range(1, len(lst)):
		current = lst[i]

		while True:
			ascending_sort = i > 0 and lst[i - 1] > current and ascending
			descending_sort = i > 0 and lst[i - 1] < current and not ascending

			if not ascending_sort and not descending_sort:
				break

			lst[i] = lst[i - 1]
			i = i - 1
			lst[i] = current
			draw_list(draw_info, {i - 1: draw_info.GREEN, i: draw_info.RED}, True)
			yield True

	return lst


def selection_sort(draw_info, ascending=True):
	"""
	Selection sort - our addition on top of the instructor's project.

	Core idea: for each position i, find the smallest (or largest, if
	descending) remaining value and swap it into position i.

	Written in the same generator style as bubble_sort/insertion_sort so
	it plugs into the exact same main loop / next() mechanism.
	"""
	lst = draw_info.lst

	for i in range(len(lst) - 1):
		# Assume the current position already holds the correct value...
		selected_index = i

		for j in range(i + 1, len(lst)):
			# ...then look for a value that should come before it.
			if (lst[j] < lst[selected_index] and ascending) or (lst[j] > lst[selected_index] and not ascending):
				selected_index = j

			# Highlight: green = current "best found so far", red = value being checked
			draw_list(draw_info, {selected_index: draw_info.GREEN, j: draw_info.RED}, True)
			yield True

		if selected_index != i:
			lst[i], lst[selected_index] = lst[selected_index], lst[i]
			draw_list(draw_info, {i: draw_info.GREEN, selected_index: draw_info.RED}, True)
			yield True

	return lst


def main():
	run = True
	clock = pygame.time.Clock()

	n = 50
	min_val = 0
	max_val = 100

	lst = generate_starting_list(n, min_val, max_val)
	draw_info = DrawInformation(900, 600, lst)
	sorting = False
	ascending = True

	sorting_algorithm = bubble_sort
	sorting_algo_name = "Bubble Sort"
	sorting_algorithm_generator = None

	while run:
		clock.tick(60)

		if sorting:
			# Each call to next() runs the generator until its next `yield`,
			# i.e. it performs exactly one visual "step" of the sort and
			# then hands control back here. When the generator function
			# finally reaches its `return`, Python raises StopIteration
			# automatically - that's how we know sorting has finished.
			try:
				next(sorting_algorithm_generator)
			except StopIteration:
				sorting = False
		else:
			draw(draw_info, sorting_algo_name, ascending)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

			if event.type != pygame.KEYDOWN:
				continue

			if event.key == pygame.K_r:
				lst = generate_starting_list(n, min_val, max_val)
				draw_info.set_list(lst)
				sorting = False
			elif event.key == pygame.K_SPACE and sorting == False:
				sorting = True
				# Calling a generator function does NOT run its code yet -
				# it just creates a generator object. Code only runs when
				# next() is called on it (above).
				sorting_algorithm_generator = sorting_algorithm(draw_info, ascending)
			elif event.key == pygame.K_a and not sorting:
				ascending = True
			elif event.key == pygame.K_d and not sorting:
				ascending = False
			elif event.key == pygame.K_i and not sorting:
				sorting_algorithm = insertion_sort
				sorting_algo_name = "Insertion Sort"
			elif event.key == pygame.K_b and not sorting:
				sorting_algorithm = bubble_sort
				sorting_algo_name = "Bubble Sort"
			elif event.key == pygame.K_s and not sorting:
				sorting_algorithm = selection_sort
				sorting_algo_name = "Selection Sort"

	pygame.quit()


if __name__ == "__main__":
	main()
