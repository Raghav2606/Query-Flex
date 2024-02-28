import tkinter as tk
from tkinter import ttk,filedialog,messagebox
import os
from PIL import Image, ImageTk
import sqlite3
import pandas as pd
import csv


def table_creater(input,query): 
    conn=sqlite3.connect('query_flex')
    cur=conn.cursor()

    for tbl_info in input:
        if tbl_info[0]!='' and tbl_info[1]!='':
            head,tail=os.path.split(tbl_info[0])
            if tail.split('.')[1].lower()=='xlsx' and tbl_info[2]!='':
                src=pd.read_excel(tbl_info[0],sheet_name=tbl_info[2])
                src.to_sql(tbl_info[1],conn,if_exists='replace',index=False)
            
            if tail.split('.')[1].lower()=='xlsx' and tbl_info[2]=='':
                src=pd.read_excel(tbl_info[0])
                src.to_sql(tbl_info[1],conn,if_exists='replace',index=False)

            if tail.split('.')[1].lower()=='csv':
                src=pd.read_csv(tbl_info[0])
                src.to_sql(tbl_info[1],conn,if_exists='replace',index=False)
    
    try:
        src_rest=cur.execute(query)
        column_names = [description[0] for description in cur.description]
        df_result = pd.DataFrame(cur.fetchall(),columns=column_names)
    except Exception as e:
        messagebox.showerror("Error", e)
    finally:        
        conn.close()
        os.remove('query_flex')
    return df_result

def clear_entries():
    for widget in widgets_frame.winfo_children():
        if isinstance(widget, ttk.Entry):
            widget.delete(0, 'end')


def populate_treeview(treeview, df):
    treeview.delete(*treeview.get_children())
    for index, row in df.iterrows():
        treeview.insert('', 'end', values=row.tolist())

def export_treeview():
    # Ask user for file location to save
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    
    if file_path:
        # Open the file in write mode
        with open(file_path, 'w', newline='') as file:
            writer = csv.writer(file)
            
            # Write column headers
            writer.writerow(get_column_names(treeview))
            
            # Traverse through each item in the treeview and export its data
            export_treeview_items(treeview, writer)

def get_column_names(treeview):
    # Get column names from Treeview
    return [treeview.heading(column)["text"] for column in treeview["columns"]]

def export_treeview_items(treeview, writer, parent=""):
    # Traverse through each item in the treeview
    for item in treeview.get_children(parent):
        values = [treeview.set(item, column) for column in treeview["columns"]]
        writer.writerow(values)
        # Recursively export child items if present
        export_treeview_items(treeview, writer, item)
     

def show_menu(event):
    # Ensure an item is selected
    global menu
    if treeview.selection():
        menu.post(event.x_root, event.y_root)

def file_exist_validation(path,status):
    print(path,status)
    if str(status).lower()=='false':
        messagebox.showerror("Error",f"{path} does not exists")


def get_values():
    global path_1, tbl1_alias, path_2, tbl2_alias,path_3, tbl3_alias,path_4, tbl4_alias,sheet_1,sheet_2,sheet_3,sheet_4
    path_1 = table_path_1.get().strip()
    tbl1_alias = table1_alias.get().strip()
    path_2 = table_path_2.get().strip()
    tbl2_alias = table2_alias.get().strip()
    path_3 = table_path_3.get().strip()
    tbl3_alias = table3_alias.get().strip()
    path_4 = table_path_4.get().strip()
    tbl4_alias = table4_alias.get().strip()
    sheet_1=Sheet_Name_1.get().strip()
    sheet_2=Sheet_Name_2.get().strip()
    sheet_3=Sheet_Name_3.get().strip()
    sheet_4=Sheet_Name_4.get().strip()

     #path_validation
    if path_1:
        path_1_exist=os.path.exists(path_1)
        file_exist_validation(path_1,path_1_exist) 
    if path_2:   
        path_2_exist=os.path.exists(path_2)
        file_exist_validation(path_2,path_2_exist)
    if path_3:
        path_3_exist=os.path.exists(path_3)
        file_exist_validation(path_3,path_3_exist)
    if path_4:
        path_4_exist=os.path.exists(path_4)
        file_exist_validation(path_4,path_4_exist)


   


def get_query():
    global treeview, table_frame,resized_image_d
    input_query = text_editor.get("1.0", "end-1c")
    tbls = [[path_1, tbl1_alias,sheet_1], [path_2, tbl2_alias,sheet_2],[path_3, tbl3_alias,sheet_3],[path_4, tbl4_alias,sheet_4]]
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
    treeview.grid(row=0, column=0, sticky='nsew')  # Use grid instead of pack
    table_frame.grid_rowconfigure(0, weight=1)  # Ensure the row expands vertically
    table_frame.grid_columnconfigure(0, weight=1)  # Ensure the column expands horizontally

    # Create horizontal scrollbar
    xscrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=treeview.xview, style='Custom.Horizontal.TScrollbar')
    xscrollbar.grid(row=1, column=0, sticky='ew')  # Place scrollbar below the Treeview
    treeview.configure(xscrollcommand=xscrollbar.set)

    # Create vertical scrollbar
    yscrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=treeview.yview, style='Custom.Vertical.TScrollbar')
    yscrollbar.grid(row=0, column=1, sticky='ns')  # Place scrollbar to the right of the Treeview
    treeview.configure(yscrollcommand=yscrollbar.set)

    export_button = ttk.Button(table_frame, text="csv",image=resized_image_d, command=export_treeview)
    export_button.grid(row=0, column=2, sticky='ns')
    
    

    for col in columns:
        treeview.heading(col, text=col)
    populate_treeview(treeview, output)

# Instantiate the instance of the window
root = tk.Tk() 

# root_directory
parent_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))
run_icon_path=fr"{parent_directory}\Icons\play-button.png"
window_icon_path=fr"{parent_directory}\Icons\WindowIcon.png"
background_image_path=fr"{parent_directory}\Icons\Background Image.jpg"


#window icon
window_icon = tk.PhotoImage(file=window_icon_path)
root.iconphoto(False, window_icon)

# Load the background image
image = Image.open(background_image_path)
background_image = ImageTk.PhotoImage(image)


# Create a label with the background image
background_label = tk.Label(root, image=background_image)
background_label.place(relwidth=1, relheight=1)

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

# Sheet_Name_1
Sheet_Name_1 = tk.StringVar()
Sheet_Name_label1 = ttk.Label(widgets_frame, text="Sheet Name:")
Sheet_Name_label1.grid(row=0, column=2, padx=5, pady=5, sticky='w')
Sheet_Name_entry_1 = ttk.Entry(widgets_frame, textvariable=Sheet_Name_1)
Sheet_Name_entry_1.grid(row=0, column=3, padx=2, pady=5, sticky='ew')

# Table Name Entry 1
table1_alias = tk.StringVar()
table_name_label1 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label1.grid(row=0, column=4, padx=5, pady=5, sticky='w')
table_entry_alias_1 = ttk.Entry(widgets_frame, textvariable=table1_alias)
table_entry_alias_1.grid(row=0, column=5, padx=5, pady=5, sticky='ew')

# File Path Entry 2
table_path_2 = tk.StringVar()
file_path_label2 = ttk.Label(widgets_frame, text="File Path:")
file_path_label2.grid(row=1, column=0, padx=5, pady=5, sticky='w')
table_entry_2 = ttk.Entry(widgets_frame, textvariable=table_path_2)
table_entry_2.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

# Sheet_Name_2
Sheet_Name_2 = tk.StringVar()
Sheet_Name_label2 = ttk.Label(widgets_frame, text="Sheet Name:")
Sheet_Name_label2.grid(row=1, column=2, padx=5, pady=5, sticky='w')
Sheet_Name_entry_2 = ttk.Entry(widgets_frame, textvariable=Sheet_Name_2)
Sheet_Name_entry_2.grid(row=1, column=3, padx=2, pady=5, sticky='ew')


# Table Name Entry 2
table2_alias = tk.StringVar()
table_name_label2 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label2.grid(row=1, column=4, padx=5, pady=5, sticky='w')
table_entry_alias_2 = ttk.Entry(widgets_frame, textvariable=table2_alias)
table_entry_alias_2.grid(row=1, column=5, padx=5, pady=5, sticky='ew')

# File Path Entry 3
table_path_3 = tk.StringVar()
file_path_label3 = ttk.Label(widgets_frame, text="File Path:")
file_path_label3.grid(row=2, column=0, padx=5, pady=5, sticky='w')
table_entry_3 = ttk.Entry(widgets_frame, textvariable=table_path_3)
table_entry_3.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

# Sheet_Name_3
Sheet_Name_3 = tk.StringVar()
Sheet_Name_label3 = ttk.Label(widgets_frame, text="Sheet Name:")
Sheet_Name_label3.grid(row=2, column=2, padx=5, pady=5, sticky='w')
Sheet_Name_entry_3 = ttk.Entry(widgets_frame, textvariable=Sheet_Name_3)
Sheet_Name_entry_3.grid(row=2, column=3, padx=2, pady=5, sticky='ew')


# Table Name Entry 3
table3_alias = tk.StringVar()
table_name_label3 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label3.grid(row=2, column=4, padx=5, pady=5, sticky='w')
table_entry_alias_3 = ttk.Entry(widgets_frame, textvariable=table3_alias)
table_entry_alias_3.grid(row=2, column=5, padx=5, pady=5, sticky='ew')

# File Path Entry 4
table_path_4 = tk.StringVar()
file_path_label4 = ttk.Label(widgets_frame, text="File Path:")
file_path_label4.grid(row=3, column=0, padx=5, pady=5, sticky='w')
table_entry_4 = ttk.Entry(widgets_frame, textvariable=table_path_4)
table_entry_4.grid(row=3, column=1, padx=5, pady=5, sticky='ew')

# Sheet_Name_4
Sheet_Name_4 = tk.StringVar()
Sheet_Name_label4 = ttk.Label(widgets_frame, text="Sheet Name:")
Sheet_Name_label4.grid(row=3, column=2, padx=5, pady=5, sticky='w')
Sheet_Name_entry_4 = ttk.Entry(widgets_frame, textvariable=Sheet_Name_4)
Sheet_Name_entry_4.grid(row=3, column=3, padx=2, pady=5, sticky='ew')

# Table Name Entry 3
table4_alias = tk.StringVar()
table_name_label4 = ttk.Label(widgets_frame, text="Table Name:")
table_name_label4.grid(row=3, column=4, padx=5, pady=5, sticky='w')
table_entry_alias_4 = ttk.Entry(widgets_frame, textvariable=table4_alias)
table_entry_alias_4.grid(row=3, column=5, padx=5, pady=5, sticky='ew')

submit_button = ttk.Button(widgets_frame, text="Submit", command=get_values)
submit_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky='nsew')


clear_button = ttk.Button(widgets_frame, text="Clear", command=clear_entries)
clear_button.grid(row=4, column=4, columnspan=2, padx=5, pady=5, sticky='nsew')

# Text Editor Frame
frame_editor = ttk.Frame(root)
frame_editor.pack(padx=50, pady=20)


# Text Editor
text_editor = tk.Text(frame_editor,width=150, height=10)
text_editor.pack(padx=5, pady=5)

# Run Button
run_image = tk.PhotoImage(file=run_icon_path) 
width, height = run_image.width(), run_image.height()
desired_width = 40  # Specify the desired width for the button image
desired_height = 40  # Specify the desired height for the button image

resized_image = run_image.subsample(width // desired_width, height // desired_height)

button_run = ttk.Button(frame_editor, text="Run",image=resized_image, command=get_query)
button_run.pack(padx=5, pady=5)

download_icon_path=fr"{parent_directory}\Icons\DownloadIcon.png"
download_icon_image = tk.PhotoImage(file=download_icon_path) 
width_d, height_d = download_icon_image.width(), download_icon_image.height()
desired_width_d = 33  # Specify the desired width for the button image
desired_height_d = 33  # Specify the desired height for the button image
global resized_image_d
resized_image_d = download_icon_image.subsample(width_d // desired_width_d, height_d // desired_height_d)

#copyright
label = tk.Label(root)

copyright_label = tk.Label(root, text="Copyright © 2024 @ Philips ISC Digtal COE", bd=1, relief=tk.RIDGE, anchor=tk.W)
copyright_label.pack(side=tk.BOTTOM, fill=tk.X)

# Main loop
root.mainloop()