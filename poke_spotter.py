import hashlib
import os
import shutil
import time
from multiprocessing import Process, Queue, cpu_count
from math import floor

from PIL import Image

CACHE_DIR = '/Users/xrjhx/AppData/Roaming/Discord/Cache'
RESIZE = (25, 25)

def current_time_millis():
    return int(round(time.time() * 1000))

def benchmark(decorated):
    def wrapper(*args, **kwargs):
        start = current_time_millis()
        res = decorated(*args, *kwargs)
        total = current_time_millis() - start
        print(f'{decorated.__name__}: {total}ms')
        return res
    return wrapper

class PokeSpotter:
    def __init__(self, cache_dir: str=CACHE_DIR, resize: tuple=RESIZE):
        self._resize = resize
        self._cache_dir = cache_dir
        self._pokedex = 'assets/pokedex'
        self._cache_thumb = 'working/smol_cache'
        self._pokedex_thumb = 'assets/smol_pokedex'
        self._cache = 'working/cache'

    @staticmethod
    def get_file_type(in_bytes: bytes):
        if in_bytes[1:4].decode('ASCII', errors='ignore') == 'PNG':
            return 'png'
        if in_bytes[6:10].decode('ASCII', errors='ignore') == 'JFIF':
            return 'jpg'
        return None

    @benchmark        
    def parse_cache(self, clear: bool=False):
        if clear:
            shutil.rmtree(self._cache, ignore_errors=True)
        os.makedirs(self._cache, exist_ok=True)
        for filename in os.listdir(self._cache_dir):
            if not filename.startswith('f_'):
                continue
            file_type = None
            source = os.path.join(self._cache_dir, filename)
            with open(source, 'rb') as file:
                file_bytes = file.read(16)
            file_type = self.get_file_type(file_bytes)
            if file_type is None:
                continue
            dest = os.path.join(self._cache, filename) + '.' + file_type
            shutil.copyfile(source, dest)

    @staticmethod
    def parse_cache_process(in_q: Queue, src_dir:str, dest_dir: str):
        filenames = in_q.get()
        for filename in filenames:
            if not filename.startswith('f_'):
                continue
            file_type = None
            source = os.path.join(src_dir, filename)
            with open(source, 'rb') as file:
                file_bytes = file.read(16)
            file_type = PokeSpotter.get_file_type(file_bytes)
            if file_type is None:
                continue
            dest = os.path.join(dest_dir, filename) + '.' + file_type
            shutil.copyfile(source, dest)

    @benchmark
    def parse_cache_multi(self, clear: bool=False):
        if clear:
            shutil.rmtree(self._cache, ignore_errors=True)
        os.makedirs(self._cache, exist_ok=True)
        filenames = os.listdir(self._cache_dir)
        items = len(filenames)
        cores = cpu_count()
        out_q = Queue()
        processes = []

        load = floor(items / cores)
        extra = (items - (load) * cores)
        current_element = 0
        for _ in range(cores):
            start = current_element
            iter_extra = 1 if extra > 0 else 0
            end = start + load + iter_extra
            extra -= 1
            current_element = end
            current_filenames = filenames[start:end]
            out_q.put(current_filenames)
            process = Process(target=self.parse_cache_process, args=(out_q, self._cache_dir, self._cache))
            process.start()
            processes.append(process)
        
        # wait for tasks to be done
        for process in processes:
            process.join()

    @benchmark     
    def make_smol(self, src_dir:str, dest_dir:str):
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dest_dir, exist_ok=True)

        for filename in os.listdir(src_dir):
            path = os.path.join(src_dir, filename)
            img = Image.open(path)
            if img.size != (475, 475):
                continue
            img.thumbnail(RESIZE)
            img.save(os.path.join(dest_dir, filename))

    def hash_file(self, file_dir: str):
        file_bytes = None
        with open(file_dir, 'rb') as file:
            file_bytes = file.read()
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @benchmark     
    def hash_cache(self):
        hashes = []
        for filename in os.listdir(self._cache_thumb):
            path = os.path.join(self._cache_thumb, filename)
            hashes.append((self.hash_file(path), filename))
        return hashes

    @benchmark     
    def hash_pokedex(self):
        hashes = dict()
        for filename in os.listdir(self._pokedex_thumb):
            path = os.path.join(self._pokedex_thumb, filename)
            hashes[self.hash_file(path)] = filename.split('.')[0]
        return hashes

    def find_matches(self, cache: list, pokedex: dict):
        matches = []
        for item in cache:
            fhash = item[0]
            name = pokedex.get(fhash)
            if name is not None:
                matches.append(name)

        filtered_matches = []
        for match in matches:
            if match not in filtered_matches:
                filtered_matches.append(match)

        return filtered_matches

    def spot(self):
        start = current_time_millis()
        # self.make_smol(self._pokedex, self._pokedex_thumb)
        # self.parse_cache(clear=True)
        self.parse_cache_multi(clear=True)
        self.make_smol(self._cache, self._cache_thumb)
        cache_hashes = self.hash_cache()
        pokedex_hashes = self.hash_pokedex()
        matches = self.find_matches(cache_hashes, pokedex_hashes)
        total = current_time_millis() - start
        print(f'spotting time: {total}ms')
        return matches


def main():
    spotter = PokeSpotter()
    matches = spotter.spot()
    print(', '.join(matches))

if __name__ == "__main__":
    main()
