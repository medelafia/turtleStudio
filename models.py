from sqlalchemy import Column, Integer, String , CHAR
from database import Base

class Student(Base):
    __tablename__ = 'students'
    id = Column(String(20), primary_key=True )
    firstName = Column(String(50), unique=False)
    lastName = Column(String(50), unique=False)
    email = Column(String(120), unique=True)
    password = Column(String(25) , unique = False ) 
    score = Column(Integer , unique = False)
    level = Column(CHAR) 

    def __init__(self, firstName , lastName , email , password , score=0 , level="A"):
        self.firstName = firstName 
        self.lastName = lastName 
        self.email = email 
        self.password = password 
        self.score = score 
        self.level = level 

    def __repr__(self):
        return f'<User {self.name!r}>'
