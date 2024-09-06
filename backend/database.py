import os
import sqlite3
from sqlalchemy.orm import DeclarativeBase, Session, relationship
from sqlalchemy import Column, String, Boolean, Integer, create_engine, Text, ForeignKey


class Base(DeclarativeBase):
    pass

class Record(Base):
    __tablename__ = "records"

    id = Column(Integer(), primary_key=True)
    record = Column(String(500))
    mode = Column(String(100))
    bucket_id = Column(Integer(), ForeignKey('buckets.id', ondelete='CASCADE'))

class Bucket(Base):
    __tablename__ = "buckets"

    id = Column(Integer(), primary_key=True)
    name = Column(String(500))
    records = relationship('Record', backref='bucket', cascade='all, delete')

BASE_DIR = os.getcwd()
connection_string = "sqlite:///"+os.path.join(BASE_DIR, 'site.db')
engine = create_engine(connection_string, echo=True)
Base.metadata.create_all(engine)
session = Session(engine)
bucket = Bucket(name='dnc_list')
bucket.records.append(Record(
    record = '1234567890',
    mode='phone',
    ))
bucket.records.append(Record(
    record = '123 street usa',
    mode='address',
    ))

session.merge(bucket)
session.commit()

bucket = session.query(Bucket).filter(Bucket.id==1).first()
session.delete(bucket)
session.commit()

# TODO: Use ORM instead of directly quering
class ListStackerDBBase:

    def __init__(self, database_path):
        self.database_path = database_path
        self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
        self.c = self.conn.cursor()
        self.create_db_tables()

    def create_db_tables(self):

        self.create_table('Phone')
        self.create_table('Address')

    def create_table(self, table_name):
        self.c.execute(f'''CREATE TABLE IF NOT EXISTS {table_name}
                        ({table_name} TEXT)''')
        self.conn.commit()

    def insert_records_from_dataframe(self, table_name, dataframe):
        try:
            # Loop through the DataFrame rows
            data_column = table_name
            for _, row in dataframe.iterrows():
                data_value = row[data_column]
                if data_value:
                    # This condition will not append any null values to db so that means that 
                    # no null value record will be removed based on db matching 
                    self.c.execute(f'''
                                        INSERT INTO {table_name} ({data_column})
                                        SELECT ?
                                        WHERE NOT EXISTS (SELECT 1 FROM {table_name} WHERE {data_column} = ?)
                                    ''', (data_value, data_value))
            print('Records inserted successfully.')
            self.conn.commit()
        except sqlite3.Error as e:
            print('Error inserting records:', e)


    def insert_record(self, table_name, data):
        try:
            self.c.execute(f'''
                                INSERT INTO {table_name}
                                SELECT ?
                                WHERE NOT EXISTS (SELECT 1 FROM {table_name} WHERE {table_name} = ?)
                            ''', (data, data))

            print('Record inserted successfully.')
            self.conn.commit()
        except sqlite3.Error as e:
            print('Error inserting record:', e)

    def get_all_records(self, table_name):
        try:
            self.c.execute(f'''
                                SELECT {table_name} FROM {table_name}
                            ''')

            return self.c.fetchall()
        except sqlite3.Error as e:
            print('Error getting all record:')

    def close_connection(self):
        if self.conn:
            self.conn.close()


class DNCDatabase(ListStackerDBBase):

    def __init__(self, database_path = 'DNCDatabase.db'):

        super().__init__(database_path)


class ProcessedRecordsDB(ListStackerDBBase):

    def __init__(self, database_path = 'ProcessedDatabase.db'):

        super().__init__(database_path)
