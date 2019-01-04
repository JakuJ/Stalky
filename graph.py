
import datetime
import os
import history
import fbapi
import status
import pandas as pd
import progressbar

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

    def to_csv(self, uid, start_time, end_time):

        # The user's history.
        status_history = history.StatusHistory(uid)

        # Their Facebook username.
        uname = fbapi.get_user_name(int(uid))

        # Generate a CSV from the multiple linear timeseries
        with open("generated_graphs/csv/{uname}.csv".format(uname=uname), "w") as f:

            f.write("time,")
            f.write(",".join(status.Status.statuses))
            f.write("\n")

            # TODO preprocess sort and splice this instead of linear search.
            seen_times = set()
            for data_point in status_history.activity:
                statuses = [str(data_point._status[status_type]) for status_type in status.Status.statuses]
                # ignore offline statuses inserted by fetcher if at the same time as last seen
                if data_point.time in seen_times and statuses == ['1', '1', '1', '1', '1']:
                    continue
                elif start_time < data_point.time < end_time:
                    seen_times.add(data_point.time)
                    # Write the time.
                    f.write(str(data_point.time) + ",")
                    # Write the various statuses.
                    # Sample line: <time>,3,1,3,1,1
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

    now = history.StatusHistory.START_TIME
    # Graph the last three days by default, but you can do ~whatever you believe you cannnnn~
    print("Graphing all data")
    g.generate_all_csvs(start_time=now - 3 * ONE_DAY_SECONDS, end_time=now)
    print("All done")

if __name__ == '__main__':
    main()
