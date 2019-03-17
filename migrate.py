import os
import sqlite3
import pandas as pd
import re
import fbapi

DATA_PATH = "data"
DB_PATH = 'data.db'
OLD_DB_PATH = 'names.db'

if __name__ == '__main__':
    fbapi.create_database()
    
    files = os.listdir(DATA_PATH)
    dataframes = []
    n = len(files)
    i = 0
    for file in files:
        path = f'{DATA_PATH}/{file}'
        i += 1
        print('Processing', path, f'{i} / {n}')

        dataframe = pd.read_csv(path, sep=',')
        dataframe['User_ID'] = re.match(r'([0-9]+)\.csv', file)[1]
        dataframe = dataframe.rename(columns={
            'time': 'Time',
            'active': 'Activity',
            'type': 'AP_ID'
        })
        dataframe['VC_ID'] = dataframe['vc_0'] * 1 + dataframe['vc_8'] * 8 + dataframe['vc_10'] * 10 + dataframe['vc_74'] * 74
        dataframe.loc[dataframe['VC_ID'] == 0, 'VC_ID'] = None
        dataframe.loc[dataframe['VC_ID'] == 1, 'AP_ID'] = 0

        dataframe.loc[dataframe['AP_ID'] == 0, 'AP_ID'] = None

        dataframe.Time = dataframe.Time.astype(int)

        dataframes.append(dataframe.drop(columns=['vc_0', 'vc_8', 'vc_10', 'vc_74']))

    data = pd.concat(dataframes, axis=0, ignore_index=True)

    print(f'Dumping data to {DB_PATH}\nThis may take a few minutes ...')
    conn = sqlite3.connect(DB_PATH)
    data.to_sql('Logs', conn, index_label='Log_ID', if_exists='append')
    
    print('Removing erroneous data')
    c = conn.cursor()
    c.execute('DELETE FROM Logs WHERE Time < 1500000000')
    c.close()

    print('Migration complete')
    conn.commit()
    conn.close()