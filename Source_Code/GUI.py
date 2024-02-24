import tkinter as tk
from tkinter import ttk
import os
from main import table_creater 
import customtkinter 

def clear_entries():
    for widget in widgets_frame.winfo_children():
        if isinstance(widget, ttk.Entry):
            widget.delete(0, 'end')


def populate_treeview(treeview, df):
    treeview.delete(*treeview.get_children())
    for index, row in df.iterrows():
        treeview.insert('', 'end', values=row.tolist())

def get_values():
    global path_1, tbl1_alias, path_2, tbl2_alias,path_3, tbl3_alias,path_4, tbl4_alias
    path_1 = table_path_1.get()
    tbl1_alias = table1_alias.get()
    path_2 = table_path_2.get()
    tbl2_alias = table2_alias.get()
    path_3 = table_path_3.get()
    tbl3_alias = table3_alias.get()
    path_4 = table_path_4.get()
    tbl4_alias = table4_alias.get()

def get_query():
    global treeview, table_frame
    input_query = text_editor.get("1.0", "end-1c")
    tbls = [[path_1, tbl1_alias], [path_2, tbl2_alias],[path_3, tbl3_alias],[path_4, tbl4_alias]]
    output = table_creater(tbls, input_query)
    if 'treeview' in globals():
        treeview.destroy()  # Destroy the existing Treeview
    if 'table_frame' in globals():
        table_frame.destroy()

    # Table Frame
    table_frame = ttk.Frame(root)
    table_frame.pack(fill='both', expand=True)
    # Create Treeview widget
    columns = list(output.columns)
    treeview = ttk.Treeview(table_frame, columns=columns, show='headings', style='Custom.Treeview')
    treeview.pack(side='left', fill='both', expand=True)

    # Create horizontal scrollbar
    xscrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=treeview.xview, style='Custom.Horizontal.TScrollbar')
    xscrollbar.pack(side='bottom', fill='x')
    treeview.configure(xscrollcommand=xscrollbar.set)
    
    # Create vertical scrollbar
    yscrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=treeview.yview, style='Custom.Vertical.TScrollbar')
    yscrollbar.pack(side='right', fill='y')
    treeview.configure(yscrollcommand=yscrollbar.set)

    for col in columns:
        treeview.heading(col, text=col)
    populate_treeview(treeview, output)

# Instantiate the instance of the window
root = tk.Tk() 

# root_directory
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
run_icon_path=rf"{parent_directory}\Icons\play-button.png"
window_icon_path=rf"{parent_directory}\Icons\WindowIcon.png"

#window icon
window_icon = tk.PhotoImage(file=window_icon_path)
root.iconphoto(False, window_icon)

# Dimensions of the window
root.geometry("800x400")

# Title of the window
root.title("Query Flex")

# Set custom theme colors
style = ttk.Style()
style.theme_use('xpnative') 

# Define custom colors
style.configure('Custom.Treeview', background='#cfe7f1', foreground='#035a6d')
style.map('Custom.Treeview', background=[('selected', '#035a6d')])

style.configure('Custom.Horizontal.TScrollbar', background='#cfe7f1', troughcolor='#cfe7f1', bordercolor='#cfe7f1')
style.configure('Custom.Vertical.TScrollbar', background='#cfe7f1', troughcolor='#cfe7f1', bordercolor='#cfe7f1')

# Frame construction
frame = ttk.Frame(root)
frame.pack(padx=50, pady=20)

# Widgets frame
widgets_frame = ttk.LabelFrame(frame, text="Map the Tables")
widgets_frame.grid(row=0, column=0, padx=10, pady=10)

# File Path Entry 1
table_path_1 = tk.StringVar()
file_path_label1 = ttk.Label(widgets_frame, text="File Path:")
file_path_label1.grid(row=0, column=0, padx=5, pady=5, sticky='w')
table_entry_1 = ttk.Entry(widgets_frame, textvariable=table_path_1)
table_entry_1.grid(row=0, column=1, padx=2, pady=5, sticky='ew')

# Table Name Entry 1
table1_alias = tk.StringVar()
table_name_label1 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label1.grid(row=0, column=2, padx=5, pady=5, sticky='w')
table_entry_alias_1 = ttk.Entry(widgets_frame, textvariable=table1_alias)
table_entry_alias_1.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

# File Path Entry 2
table_path_2 = tk.StringVar()
file_path_label2 = ttk.Label(widgets_frame, text="File Path:")
file_path_label2.grid(row=1, column=0, padx=5, pady=5, sticky='w')
table_entry_2 = ttk.Entry(widgets_frame, textvariable=table_path_2)
table_entry_2.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

# Table Name Entry 2
table2_alias = tk.StringVar()
table_name_label2 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label2.grid(row=1, column=2, padx=5, pady=5, sticky='w')
table_entry_alias_2 = ttk.Entry(widgets_frame, textvariable=table2_alias)
table_entry_alias_2.grid(row=1, column=3, padx=5, pady=5, sticky='ew')

# File Path Entry 3
table_path_3 = tk.StringVar()
file_path_label3 = ttk.Label(widgets_frame, text="File Path:")
file_path_label3.grid(row=2, column=0, padx=5, pady=5, sticky='w')
table_entry_3 = ttk.Entry(widgets_frame, textvariable=table_path_3)
table_entry_3.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

# Table Name Entry 3
table3_alias = tk.StringVar()
table_name_label3 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label3.grid(row=2, column=2, padx=5, pady=5, sticky='w')
table_entry_alias_3 = ttk.Entry(widgets_frame, textvariable=table3_alias)
table_entry_alias_3.grid(row=2, column=3, padx=5, pady=5, sticky='ew')

# File Path Entry 4
table_path_4 = tk.StringVar()
file_path_label4 = ttk.Label(widgets_frame, text="File Path:")
file_path_label4.grid(row=3, column=0, padx=5, pady=5, sticky='w')
table_entry_4 = ttk.Entry(widgets_frame, textvariable=table_path_4)
table_entry_4.grid(row=3, column=1, padx=5, pady=5, sticky='ew')

# Table Name Entry 3
table4_alias = tk.StringVar()
table_name_label4 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label4.grid(row=3, column=2, padx=5, pady=5, sticky='w')
table_entry_alias_4 = ttk.Entry(widgets_frame, textvariable=table4_alias)
table_entry_alias_4.grid(row=3, column=3, padx=5, pady=5, sticky='ew')

submit_button = customtkinter.CTkButton(widgets_frame, text="Submit", command=get_values,text_color="white")
submit_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')


clear_button = customtkinter.CTkButton(widgets_frame, text="Clear", command=clear_entries,text_color="white")
clear_button.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky='nsew')

# Text Editor Frame
frame_editor = ttk.Frame(root)
frame_editor.pack(padx=50, pady=20)


# Text Editor
text_editor = tk.Text(frame_editor,width=150, height=10)
text_editor.pack(padx=5, pady=5)

# Run Button
# Resize the image to fit the button
run_image = tk.PhotoImage(file=run_icon_path) 
width, height = run_image.width(), run_image.height()
desired_width = 40  # Specify the desired width for the button image
desired_height = 40  # Specify the desired height for the button image

resized_image = run_image.subsample(width // desired_width, height // desired_height)

button_run = ttk.Button(frame_editor, text="Run",image=resized_image, command=get_query)
button_run.pack(padx=5, pady=5)


# Create a Treeview widget (to be filled later)
table_frame = ttk.Frame(root)
table_frame.pack(fill='both', expand=True, padx=50, pady=20)

treeview = ttk.Treeview(table_frame, columns=[], show='headings', style='Custom.Treeview')
treeview.pack(side='left', fill='both', expand=True)

# Create horizontal scrollbar
xscrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=treeview.xview, style='Custom.Horizontal.TScrollbar')
xscrollbar.pack(side='bottom', fill='x')
treeview.configure(xscrollcommand=xscrollbar.set)
    
# Create vertical scrollbar
yscrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=treeview.yview, style='Custom.Vertical.TScrollbar')
yscrollbar.pack(side='right', fill='y')
treeview.configure(yscrollcommand=yscrollbar.set)

# Main loop
root.mainloop()
