import sqlite3
import pandas as pd
import os


conn=sqlite3.connect('query_flex')
cur=conn.cursor()



def table_creater(input,query):
    for tbl_info in input:
        if tbl_info[0]!='' and tbl_info[1]!='':
            head,tail=os.path.split(tbl_info[0])
            if tail.split('.')[1].lower()=='xlsx':
                src=pd.read_excel(tbl_info[0])
                src.to_sql(tbl_info[1],conn,if_exists='replace',index=False)

            if tail.split('.')[1].lower()=='csv':
                src=pd.read_csv(tbl_info[0])
                src.to_sql(tbl_info[1],conn,if_exists='replace',index=False)
    
    src_rest=cur.execute(query)
    column_names = [description[0] for description in cur.description]
    df_stock_q = pd.DataFrame(cur.fetchall(),columns=column_names)
    return df_stock_q
            

           
# input=[[r"C:\Users\320128965\Downloads\MasterFile.xlsx", 'master'],[r"C:\Users\320128965\Downloads\SalesOrder with False.csv", 'validate']]
# query="""
# select * from master
# """
# print(table_creater(input,query))
