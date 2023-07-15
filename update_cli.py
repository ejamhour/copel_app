from glob import glob
import os
import hashlib
import json
from datetime import datetime
import time
from zipfile import ZipFile
import requests
from os import getcwd


class UpdateAPP:

    def __init__(self, **args):

        os.chdir( os.path.dirname(__file__))        

        self.dlist = [
            '../cisei_lib/**/*.py', 
            '../Wolfram/**/*.wl*', 
            '../public/**/*.*', 
            '../*.py' 
        ]    

        self.base = [
            '../Configuration/*.*',
            '../Data/**/*.*'
        ]  

        self.history = 'package_history.json'

    def __str__(self):
        return 'Update Smart Grid Planner'

    def __enter__(self):
        return self
    
    def __exit__(self, t, v, tr):
        print('Update APP has exit!')

    # Download a file from github repository
    def repo_file(self, file):
        # url = f"https://github.com/ejamhour/copel_app/blob/main/{file}?raw=True"
        url = f"https://raw.githubusercontent.com/ejamhour/copel_app/main/{file}"
        r = requests.get(url)
        if r.content == b'404: Not Found':
            print(r)
            raise Exception(f'ERROR: Could not download {file} from github')          
        return r.content

    # Returns a string-base MD5 hash of the file
    def compute_hash(self, file):
        m = hashlib.md5()
        with open(file,'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    # Creates a list of file entries as dictionaries
    def scan_dir(self, dir):

        files = [ f for f in glob( dir, recursive=True) ]

        d = []        
        for f in files:
            e = {}
            e['path'] = f
            e['date'] = time.ctime(os.path.getmtime(f))
            e['hash'] = self.compute_hash(f)
            d.append(e)
  
        return d
    
    # Creates a json with the current files info 
    def create_json(self, save=False, date=None):

        res  = {'date' : time.ctime() if date is None else date  } 
        # this script is suppose to be in a child folder
        for d in self.dlist: res[d] = self.scan_dir(d) 
        res = json.dumps(res, indent = 4)
        if save:
            with open('my_files.json' ,'w') as f:
                f.write(res)
        return res
    
    # Creates a package with files modified since (last) update
    # -- update=None: include all files, base=True include Data e Configuration.
    def create_package(self, file='package.zip', update='my_files.json', base=False):
        if update is not None and os.path.isfile(update):
            with open(update) as f:
                lu = json.load(f)
        else:
            lu = {}

        res = {}
        for d in self.dlist:
            old = [ u['hash'] for u in lu.get(d, [] ) ]
            new = [f for f in self.scan_dir(d) if f['hash'] not in old ] 
            if len(new) > 0: res[d] = new 
        
        with ZipFile(file, 'w') as zip:
            for dir,files in res.items():
               for f in files:
                   zip.write(f['path'])
            if base:
                for d in self.base:
                    for f in self.scan_dir(d):
                        zip.write(f['path'])

            res['date'] =  time.ctime()
            zip.writestr('updates/package.json', json.dumps(res, indent=4))

        # TODO: criar um json com o nome do package
        with open(os.path.splitext(file)[0] + '.json', 'w') as f:
            f.write( json.dumps(res, indent=4) )

    # Apply package to the current directory if not outdated
    def apply_package(self, package):

        with open('my_files.json', 'r') as f:
            linfo = json.load(f)

        with ZipFile(package, 'r') as zip:
            pinfo = json.loads( zip.read('updates/package.json').decode() ) 

            t = lambda d : datetime.strptime(d, "%a %b %d %H:%M:%S %Y")

            if t(pinfo['date']) > t(linfo['date']):
                print('Your app you be updated!')
                zip.extractall("../")
            else:
                print('This package is outdated!')

            self.create_json(save=True, date=pinfo['date'])
    
    # Check updates, download and apply packages if necessary
    def check_update(self):

        with open('my_files.json', 'r') as f:
            linfo = json.load(f)
        
        t = lambda d : datetime.strptime(d, "%a %b %d %H:%M:%S %Y")

        pkg = self.repo_file("package.json")
        pkg = json.loads(pkg.decode())

        updates = [ k for k,v in pkg.items() if t(v["date"]) > t(linfo['date']) ]

        if len(updates) > 0:
            print('There are updates available.')
            print('downloading packages ... ')
            try:
                for u in updates:
                    res = self.repo_file(f"package_{u}.zip")
            except Exception as e:
                print(e)
                return
      

if __name__ == '__main__':

      
    with UpdateAPP() as uapp:
        # uapp.create_json(save=True)
        uapp.create_package(file='package_v1.zip', update='my_files.json', base=False)
        # uapp.apply_package('package.zip')
        # uapp.check_update()

        pass

        





