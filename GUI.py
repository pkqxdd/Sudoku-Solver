import multiprocessing as mp
import numpy as np
import threading
from queue import Queue
from functools import singledispatch, update_wrapper

try:
	import tkinter as tk  # Python3
except ImportError:
	import Tkinter as tk  # Python2

def centerwindow(window,h,w):
	sh = window.winfo_screenheight()
	sw = window.winfo_screenwidth()
	window.geometry('+' + str((sw - w) // 2) + '+' + str((sh - h) // 2))

def getwinfo(widget):
	widget.update()
	print('height= %s, width= %s'% (widget.winfo_height(), widget.winfo_width()))


def methdispatch(func):
	#copied from https://stackoverflow.com/questions/24601722/how-can-i-use-functools-singledispatch-with-instance-methods
	dispatcher = singledispatch(func)

	def wrapper(*args, **kw):
		return dispatcher.dispatch(args[1].__class__)(*args, **kw)

	wrapper.register = dispatcher.register
	update_wrapper(wrapper, func)
	return wrapper


@singledispatch
def visualize_board(input):
	raise TypeError(str(type(input)) + ' input is not a matrix or string')


@visualize_board.register(str)
def _visualize_board(input_string):
	# create board
	root = tk.Tk()
	root.title('Sudoku')
	canvas = tk.Canvas(root, width=550, height=550)
	canvas.create_rectangle(50, 50, 500, 500, width=2)
	for i in range(1, 10):
		canvas.create_text(25 + 50 * i, 30, text=str(i))
		canvas.create_text(30, 25 + 50 * i, text=str(i))
		canvas.create_line(50 + 50 * i, 50, 50 + 50 * i, 500, width=2 if i % 3 == 0 else 1)
		canvas.create_line(50, 50 + 50 * i, 500, 50 + 50 * i, width=2 if i % 3 == 0 else 1)

	for i in range(81):
		if input_string[i] != '0':
			canvas.create_text(75 + 50 * (i % 9), 75 + 50 * (i // 9), text=input_string[i], fill='black')

	canvas.pack()
	root.attributes('-topmost', True)
	root.grab_set()
	root.wm_protocol('WM_DELETE_WINDOW', root.destroy)
	root.geometry('550x550+%d+%d' % ((root.winfo_screenwidth() - 550) // 2, (root.winfo_screenheight() - 550) // 2))
	root.mainloop()


@visualize_board.register(np.ndarray)
@visualize_board.register(list)
@visualize_board.register(tuple)
def _visualize_board(input):
	# create board
	root = tk.Tk()
	root.title('Sudoku')
	canvas = tk.Canvas(root, width=550, height=550)
	canvas.create_rectangle(50, 50, 500, 500, width=2)
	for i in range(1, 10):
		canvas.create_text(25 + 50 * i, 30, text=str(i))
		canvas.create_text(30, 25 + 50 * i, text='ABCDEFGHI'[i-1])
		canvas.create_line(50 + 50 * i, 50, 50 + 50 * i, 500, width=2 if i % 3 == 0 else 1)
		canvas.create_line(50, 50 + 50 * i, 500, 50 + 50 * i, width=2 if i % 3 == 0 else 1)

	if isinstance(input[0][0], (str, int)):
		for i in range(9):
			for j in range(9):
				if input[i][j] != 0:
					canvas.create_text(75 + 50 * j, 75 + 50 * i, text=str(input[i][j]))

	else:
		for i in range(9):
			for j in range(9):
				if input[i][j].value != 0:
					canvas.create_text(75 + 50 * j, 75 + 50 * i, text=str(input[i][j].value))

	canvas.pack()
	root.attributes('-topmost', True)
	root.grab_set()
	root.geometry('550x550+%d+%d' % ((root.winfo_screenwidth() - 550) // 2, (root.winfo_screenheight() - 550) // 2))
	root.wm_protocol('WM_DELETE_WINDOW',root.destroy)
	root.mainloop()

del _visualize_board

class VisualizedBoard:

	def __init__(self, user_input, pipe,color='black'):
		'''input_string: a string has a length of at least 81 that represent the board from top-left to bottom right.
		empty cell is 0'''
		self.pipe = pipe
		self.q = Queue()
		self.last_word=None
		self.board_config=user_input
		# create board
		self.root = tk.Tk()
		self.canvas = tk.Canvas(self.root, width=500, height=500)
		self.canvas.create_rectangle(50, 50, 500, 500, width=2)
		for i in range(1, 10):
			self.canvas.create_text(25 + 50 * i, 30, text=str(i))
			self.canvas.create_text(30, 25 + 50 * i, text='ABCDEFGHI'[i-1])
			self.canvas.create_line(50 + 50 * i, 50, 50 + 50 * i, 500, width=2 if i % 3 == 0 else 1)
			self.canvas.create_line(50, 50 + 50 * i, 500, 50 + 50 * i, width=2 if i % 3 == 0 else 1)

		self.draw(user_input,color)

		threading.Thread(target=self.listen, args=()).start()
		threading.Thread(target=self.update_from_queue,args=()).start()

		self.canvas.pack()
		self.root.attributes('-topmost', True)
		self.root.bind('<Enter>', lambda event: (self.root.unbind('<Enter'), self.root.attributes('-topmost', False)))

		self.root.geometry(
				'550x550+%d+%d' % ((self.root.winfo_screenwidth() - 550) // 2, (self.root.winfo_screenheight() - 550) // 2))
		self.root.wm_protocol('WM_DELETE_WINDOW', lambda: (self.root.destroy()))


		self.root.title('Sudoku')
		self.root.mainloop()

	@methdispatch
	def draw(self,user_input,color):
		raise TypeError("I don't know how to draw a graph from this type: " + str(type(input)))

	@draw.register(str)
	def _(self,user_input,color):
		for i in range(81):
			if user_input[i] != '0':
				self.canvas.create_text(75 + 50 * (i % 9), 75 + 50 * (i // 9),
				                        tags=str((i // 9 + 1, i % 9 + 1)).replace(' ', ''), text=user_input[i],
				                        fill=color)

	@draw.register(np.ndarray)
	@draw.register(np.matrix)
	@draw.register(list)
	@draw.register(tuple)
	def _(self,user_input,color):
		if isinstance(user_input[0][0], (str, int)):
			for i in range(9):
				for j in range(9):
					if user_input[i][j] != 0:
						self.canvas.create_text(75 + 50 * j, 75 + 50 * i, text=str(user_input[i][j]),fill=color)
		else:
			for i in range(9):
				for j in range(9):
					if user_input[i][j].value != 0:
						self.canvas.create_text(75 + 50 * j, 75 + 50 * i, text=str(user_input[i][j].value),
						                        fill=color)

	def update(self, coordinate, value, color='magenta'):
		"""
				:parameter coordinate: a tuple (x,y)
				:parameter value: single digit
				:returns: None
		"""
		try:
			assert isinstance(coordinate, tuple)
		except AssertionError:
			print('Update Failed. Coordinate should be a tuple (x,y)')

		coordinate_tag = str(coordinate).replace(' ', '')
		self.canvas.delete(coordinate_tag)
		if value != 0 and value != '0':
			self.canvas.create_text(25 + 50 * coordinate[0], 25 + 50 * coordinate[1], tags=coordinate_tag,
			                        text=str(value), fill=color)
		self.canvas.update()

	def update_from_queue(self):
		try:
			while True:
				d=self.q.get()
				if d=='terminate' or d=='NoSolution': break
				self.update(*d)
			if d=='NoSolution':
				self.canvas.delete('all')
				self.canvas.create_rectangle(50, 50, 500, 500, width=2)
				for i in range(1, 10):
					self.canvas.create_text(25 + 50 * i, 30, text=str(i))
					self.canvas.create_text(30, 25 + 50 * i, text=str(i))
					self.canvas.create_line(50 + 50 * i, 50, 50 + 50 * i, 500, width=2 if i % 3 == 0 else 1)
					self.canvas.create_line(50, 50 + 50 * i, 500, 50 + 50 * i, width=2 if i % 3 == 0 else 1)
				self.draw(self.board_config,'black')
		except RuntimeError:
			raise SystemExit
		except TypeError:
			pass
	def new_board(self, input_string):
		self.root.destroy()
		return VisualizedBoard(input_string, self.pipe)

	def listen(self):
		try:
			while True:
				msg = self.pipe.recv()
				self.last_word=msg
				self.q.put(msg) #Becuase update is slow, put it in a queue so it will not block
		except EOFError: # BoardConnection.disconnect is called.
			self.pipe.close()
			self.q.put('terminate')
			if self.last_word == 'NoSolution':
				top=tk.Toplevel()
				top.attributes('-topmost',True)
				centerwindow(top,47, 274)
				tk.Label(top,
				         text='No Solution Found',fg='red',font=('Times',36)).pack()
				tk.Button(top,text='Ok',command=top.destroy).pack()

			elif len(self.last_word) == 81:
				def go_to_solution():
					self.root.iconify()
					top=tk.Toplevel()
					top.title('Sudoku')
					canvas = tk.Canvas(top, width=500, height=500)
					canvas.create_rectangle(50, 50, 500, 500, width=2)
					for i in range(1, 10):
						canvas.create_text(25 + 50 * i, 30, text=str(i))
						canvas.create_text(30, 25 + 50 * i, text=str(i))
						canvas.create_line(50 + 50 * i, 50, 50 + 50 * i, 500, width=2 if i % 3 == 0 else 1)
						canvas.create_line(50, 50 + 50 * i, 500, 50 + 50 * i, width=2 if i % 3 == 0 else 1)

					for i in range(81):
						if self.last_word[i] != '0':
							canvas.create_text(75 + 50 * (i % 9), 75 + 50 * (i // 9), text=self.last_word[i],
							                   fill='black')

					canvas.pack()
					tk.Button(top, text='Back', command=top.destroy).pack()
					top.attributes('-topmost', True)
					top.grab_set()
					top.geometry('550x550+%d+%d' % (
					(top.winfo_screenwidth() - 550) // 2, (top.winfo_screenheight() - 550) // 2))

					self.canvas.update()
					self.root.wait_window(top)
					f.pack_forget()
					self.root.deiconify()

				f=tk.Frame(self.root)
				tk.Label(f,
				         text='Solution found. Continue showing steps.').grid(row=0,column=0)
				tk.Label(f,text='This process normally should take no more than 10 seconds.').grid(row=1)
				tk.Button(f,text='Jump to solution',command=go_to_solution).grid(row=0,column=1,rowspan=2)
				f.pack()
			else:
				top=tk.Toplevel()
				top.attributes('-topmost',True)
				tk.Label(top,
				         text='Something went wrong. Please contact the developer\n with the board configuration to solve this issue',
				         fg='red').pack()
				e=tk.Text(top,width=80)
				e.insert(0.0,self.board_config)

				e.pack()
		except (tk.TclError, RuntimeError):
			try:
				while True: #Simply consumes all the data in the pipe so the other end will not block
					self.pipe.recv()
			except EOFError:
				raise SystemExit


class BoardConnection:
	def __init__(self, input_string):
		ctx = mp.get_context('spawn')
		self.receive, self.pipe = ctx.Pipe(False)
		self.process = ctx.Process(target=VisualizedBoard, args=(input_string, self.receive))
		self.process.start()

	def update(self, coordinate, value, color='magenta'):
		"""
		:parameter coordinate: a tuple (x,y)
		:parameter value: single digit
		:returns: None
		"""
		self.pipe.send((coordinate, value, color))

	def disconnect(self):
		self.pipe.close()

	def close(self):
		self.pipe.close()
		self.process.terminate()


