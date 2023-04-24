import pandas as pd
import os
import multiprocessing

COMBINED_DATA_PATH = "C:\\Users\\raval\\Desktop\\stressdetection\\6Bdata"
SAVE_PATH = "C:\\Users\\raval\\Desktop\\stressdetection\\merge1"

# if COMBINED_DATA_PATH != SAVE_PATH:
#     os.mkdir(SAVE_PATH)

print("Reading data ...")

# acc, eda, hr, temp = None, None, None, None

signals = ['acc', 'eda', 'hr', 'temp']

def read_parallel(signal):
    df = pd.read_csv(os.path.join(COMBINED_DATA_PATH, f"combined_{signal}.csv"), dtype={'id': str})
    return [signal, df]

"""
if __name__ == '__main__':
    multiprocessing.freeze_support()
    with multiprocessing.Pool(len(signals)) as pool:
        results = pool.map(read_parallel, signals)
    pool.close()
    pool.join()
    
    for i in results:
        globals()[i[0]] = i[1]
"""

acc = pd.read_csv(os.path.join(COMBINED_DATA_PATH, f"combined_acc.csv"), dtype={'id': str})
eda = pd.read_csv(os.path.join(COMBINED_DATA_PATH, f"combined_eda.csv"), dtype={'id': str})
hr = pd.read_csv(os.path.join(COMBINED_DATA_PATH, f"combined_hr.csv"), dtype={'id': str})
temp = pd.read_csv(os.path.join(COMBINED_DATA_PATH, f"combined_temp.csv"), dtype={'id': str})

# Merge data
print('Merging Data ...')
ids = eda['id'].unique()
columns=['X', 'Y', 'Z', 'EDA', 'HR', 'TEMP', 'id', 'datetime']

def merge_parallel(id):
    print(f"Processing {id}")
    df = pd.DataFrame(columns=columns)
    
    acc_id = acc[acc['id'] == id].drop(['id'], axis=1)
    eda_id = eda[eda['id'] == id].drop(['id'], axis=1)
    hr_id = hr[hr['id'] == id].drop(['id'], axis=1)
    temp_id = temp[temp['id'] == id].drop(['id'], axis=1)

    df = acc_id.merge(eda_id, on='datetime', how='outer')
    df = df.merge(temp_id, on='datetime', how='outer')
    df = df.merge(hr_id, on='datetime', how='outer')

    df.fillna(method='ffill', inplace=True)
    df.fillna(method='bfill', inplace=True)

    return df

if __name__ == '__main__':
    multiprocessing.freeze_support()
    with multiprocessing.Pool(len(ids)) as pool:
        results = pool.map(merge_parallel, ids)
    pool.close()
    pool.join()
    
    new_df = pd.concat(results, ignore_index=True)
    
    print("Saving data ...")
    new_df.to_csv(os.path.join(SAVE_PATH, "merged_6B.csv"), index=False)