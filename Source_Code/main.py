import sqlite3
import pandas as pd

conn=sqlite3.connect('query_flex')
cur=conn.cursor()



def table_creater(input,query):
    for tbl_info in input:
        if tbl_info[0]!='' and tbl_info[1]!='' and tbl_info[2]!='':
            if tbl_info[2].lower()=='excel':
                src=pd.read_excel(tbl_info[0])
                src.to_sql(tbl_info[1],conn,if_exists='replace',index=False)
    
    src_rest=cur.execute(query)
    column_names = [description[0] for description in cur.description]
    df_stock_q = pd.DataFrame(cur.fetchall(),columns=column_names)
    return df_stock_q
            

           
# input=[[r"C:\Users\320128965\Downloads\MasterFile.xlsx", 'master', 'Excel'], [r"C:\Users\320128965\Downloads\Validation.xlsx", 'validate', 'Excel']]
# query="""
# select a.*,b.* from 
# master as a
# left join
# validation as b
# a.fact_order=b.factory_sales_order
# and
# a.fact_line=b.factory_sales_order_line
# """
# table_creater(input,query)
