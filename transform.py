import os
import re
import json
import progressbar

def transform(path):
    history = []
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            time, data = line.split('|')
            data = json.loads(data)

            vc = None
            
            if data['vc_0'] == 'active':
                vc = 0
            elif data['vc_8'] == 'active':
                vc = 8
            elif data['vc_10'] == 'active':
                vc = 10
            elif data['vc_74'] == 'active':
                vc = 74

            new = {
                'time': float(time),
                'active': data['status'] == 'active',
                'vc': vc,
                'type': None
            }
            history.append(new)

    with open(path, 'w') as f:
        for log in history:
            f.write(json.dumps(log))
            f.write('\n')


if __name__ == '__main__':
    filenames = os.listdir('log')
    num = len(filenames)
    for i in progressbar.progressbar(range(num)):
        transform('log/' + filenames[i])
