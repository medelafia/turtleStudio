import mysql.connector 


mydb = mysql.connector.connect(
  host="127.0.0.1",
  user="root",
  password="Med@29072003" , 
  port=3306
)

print(mydb) 

mydb.close() 