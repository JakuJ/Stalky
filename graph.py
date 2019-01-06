
import datetime
import os
import fbapi
import pandas as pd
import progressbar
import json
import time

LOG_DATA_DIR = "log"
CSV_OUTPUT_DIR = "generated_graphs/csv"
NAME_FILE = "names_storage.json"

UTC_OFFSET = 1
ONE_DAY_SECONDS = 60 * 60 * 24

class Grapher():
    def __init__(self):
        if not os.path.exists(CSV_OUTPUT_DIR):
            os.makedirs(CSV_OUTPUT_DIR)
        self.names = pd.read_json(NAME_FILE)

    def encode_type(self, act_type):
        mapping = {
            None: '0',
            'a2': '1',
            'p0': '2',
            'p2': '3'
        }
        return mapping[act_type]

    def to_csv(self, uid, start_time, end_time):

        # The users's facebook profile name
        uname = fbapi.get_user_name(int(uid))
        
        # The user's history.
        with open("{dir}/{uid}.txt".format(dir=LOG_DATA_DIR, uid=uid), 'r') as f:
            lines = map(str.strip, f.readlines())

        lines = sorted(list(lines), key=lambda line: json.loads(line)['time'])
            
        # Generate CSV file for plotting data
        with open("generated_graphs/csv/{uname}.csv".format(uname=uname), "w") as f:
            f.write("time,active,vc_0,vc_8,vc_10,vc_74,type\n")

            # TODO preprocess sort and splice this instead of linear search
            seen_times = set()
            for line in lines:
                data = json.loads(line)

                statuses = ['1' if data['vc'] == i else '0' for i in [0, 8, 10, 74]]
                statuses.insert(0, str(int(data['active'])))
                statuses.append(self.encode_type(data['type']))

                # ! Ignore already seen times
                if data['time'] in seen_times:
                    continue
                elif start_time < data['time'] < end_time:
                    seen_times.add(data['time'])
                    # Write the time.
                    f.write(str(data['time']) + ",")
                    # Write statuses
                    f.write(",".join(statuses))
                    f.write("\n")

    def generate_all_csvs(self, start_time, end_time):
        filenames = os.listdir(LOG_DATA_DIR)
        num = len(filenames)
        for i in progressbar.progressbar(range(num)):
            uid = filenames[i].split(".")[0]
            self.to_csv(uid, start_time, end_time)

def main():
    g = Grapher()
    now = time.time()

    print("Graphing all data")
    g.generate_all_csvs(start_time=now - 3 * ONE_DAY_SECONDS, end_time=now)
    print("All done")

if __name__ == '__main__':
    main()
