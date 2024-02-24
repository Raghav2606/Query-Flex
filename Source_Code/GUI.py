import pandas
import sqlite3
import tkinter as tk
from tkinter import ttk
from PIL import Image,ImageTk
import os
import customtkinter
from main import *

def populate_treeview(treeview, df):
    treeview.delete(*treeview.get_children())
    for index, row in df.iterrows():
        treeview.insert('', 'end', values=row.tolist())

def get_values():
    global path_1, tbl1_alias, f_type_1, path_2, tbl2_alias, f_type_2
    path_1 = table_path_1.get()
    tbl1_alias = table1_alias.get()
    f_type_1 = file_type_1.get()
    path_2 = table_path_2.get()
    tbl2_alias = table2_alias.get()
    f_type_2 = file_type_2.get()

def get_query():
    global treeview
    global table_frame
    input_query = text_editor.get("1.0", "end-1c")
    tbls = list([[path_1, tbl1_alias, f_type_1], [path_2, tbl2_alias, f_type_2]])
    output = table_creater(tbls, input_query)
    print(output)
    if 'treeview' in globals():
        treeview.destroy()  # Destroy the existing Treeview
    if 'table_frame' in globals():
        table_frame.destroy()

    # Table Frame
    table_frame = ttk.Frame(root)
    table_frame.pack(fill='both', expand=True)
    # Create Treeview widget
    columns = list(output.columns)
    treeview = ttk.Treeview(table_frame, columns=columns, show='headings')
    treeview.pack(side='left', fill='both', expand=True)

    # Create horizontal scrollbar
    xscrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=treeview.xview)
    xscrollbar.pack(side='bottom', fill='x')
    treeview.configure(xscrollcommand=xscrollbar.set)
    
    # Create vertical scrollbar
    yscrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=treeview.yview)
    yscrollbar.pack(side='right', fill='y')
    treeview.configure(yscrollcommand=yscrollbar.set)

    for col in columns:
        treeview.heading(col, text=col)
    populate_treeview(treeview, output)

# Instantiate the instance of the window
root = tk.Tk() 

# root_directory
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

table_path_1 = tk.StringVar()
table1_alias = tk.StringVar()
file_type_1 = tk.StringVar()

table_path_2 = tk.StringVar()
table2_alias = tk.StringVar()
file_type_2 = tk.StringVar()

# Dimensions of the window
root.geometry("1920x1080")

# Title of the window
root.title("Query Flex")

options = ["Excel", "CSV"]

# Frame construction
frame = ttk.Frame(root)
frame.pack()
widgets_frame = ttk.LabelFrame(frame, text="Map the Tables")
widgets_frame.grid(row=0, column=0, padx=30, pady=20)

table_entry = ttk.Entry(widgets_frame, textvariable=table_path_1)
table_entry.insert(0, "File Path")
table_entry.bind("<FocusIn>", lambda e: table_entry.delete('0', 'end'))
table_entry.grid(row=0, column=0, padx=5, pady=(0, 5), sticky='ew')

table_entry_alias = ttk.Entry(widgets_frame, textvariable=table1_alias)
table_entry_alias.insert(0, "Table Name")
table_entry_alias.bind("<FocusIn>", lambda e: table_entry_alias.delete('0', 'end'))
table_entry_alias.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

file_type_combobox = ttk.Combobox(widgets_frame, values=options, textvariable=file_type_1)
file_type_combobox.grid(row=0, column=2, padx=5, pady=5, sticky='ew')

table_entry_2 = ttk.Entry(widgets_frame, textvariable=table_path_2)
table_entry_2.insert(0, "File Path")
table_entry_2.bind("<FocusIn>", lambda e: table_entry_2.delete('0', 'end'))
table_entry_2.grid(row=1, column=0, padx=5, pady=5, sticky='ew')

table_entry2_alias = ttk.Entry(widgets_frame, textvariable=table2_alias)
table_entry2_alias.insert(0, "Table Name")
table_entry2_alias.bind("<FocusIn>", lambda e: table_entry2_alias.delete('0', 'end'))
table_entry2_alias.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

file_type_combobox2 = ttk.Combobox(widgets_frame, values=options, textvariable=file_type_2)
file_type_combobox2.grid(row=1, column=2, padx=5, pady=5, sticky='ew')

button = ttk.Button(widgets_frame, text="Submit", command=get_values)
button.grid(row=3, column=0, padx=5, pady=5, sticky='nsew')                             

# Text Editor
frame_editor = ttk.Frame(root)
frame_editor.pack()
text_editor = tk.Text(frame_editor, width=150, height=10)
text_editor.grid(row=0, column=0)

button_run = ttk.Button(frame_editor, text="Run", command=get_query)
button_run.grid(row=1, column=0, padx=5, pady=5)

# place window on the computer screens, listens for events
root.mainloop()
