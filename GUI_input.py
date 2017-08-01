import tkinter as tk
from main import main
import time
if __name__ == '__main__':
	root = tk.Tk()
	root.title('Sudoku input')

	canvas = tk.Canvas(root, width=501, height=501,borderwidth=0,bg='white',highlightthickness=0)

	def validate_entry(text):
		try:
			int(text)
		except ValueError:
			return False
		if len(text) > 1:
			return False
		if text=='0':
			return False
		return True

	def find_solution():
		input_string=''.join([e.get() if e.get() != '' else '0' for e in entries])
		root.destroy()
		time.sleep(1.5)
		main(input_string,True)

	v=root.register(validate_entry)

	entries=[tk.Entry(canvas,width=1,validate='key',validatecommand=(v,'%P')) for i in range(81)]
	for e in entries:
		e.bind('<FocusIn>',lambda event:event.widget.delete(0,tk.END))


	canvas.create_rectangle(50, 50, 500, 500, width=2)

	for i in range(1, 10):
		canvas.create_text(25 + 50 * i, 30, text=str(i))
		canvas.create_text(30, 25 + 50 * i, text=str(i))
		canvas.create_line(50 + 50 * i, 50, 50 + 50 * i, 500, width=2 if i % 3 == 0 else 1)
		canvas.create_line(50, 50 + 50 * i, 500, 50 + 50 * i, width=2 if i % 3 == 0 else 1)

	for i in range(81):
		canvas.create_window(75 + 50 * (i % 9), 75 + 50 * (i // 9) ,window=entries[i])

	canvas.pack()
	tk.Button(root,text='Solve',command=find_solution).pack()
	root.attributes('-topmost', True)
	root.grab_set()
	root.wm_protocol('WM_DELETE_WINDOW', root.destroy)
	root.geometry('550x550+%d+%d' % ((root.winfo_screenwidth() - 550) // 2, (root.winfo_screenheight() - 550) // 2))
	root.mainloop()


