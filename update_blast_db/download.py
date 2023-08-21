import sys, os, hashlib, requests, logging, subprocess, glob, json



def calcmd5(file):
    logging.info("Calculating md5 checksum for downloaded file...")
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def remote_file_exists(filename):
    c = requests.head('https://ftp.ncbi.nih.gov/blast/db/{}'.format(filename), stream=True, timeout = 60)
    if c.status_code < 400:
        return True
    else:
        return False

def download_file(f, o):
    logging.info("Downloading {}...".format(f))
    with requests.get('https://ftp.ncbi.nih.gov/blast/db/{}'.format(f), stream=True, allow_redirects=True, timeout = 1800) as r:
        r.raise_for_status()
        with open(os.path.join(o, f), 'wb') as h:
            # h.write(r.content)
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: # filter out keep-alive new chunks
                    h.write(chunk)

def md5_compare(local_hash, remote_file):
    logging.info("Comparing md5 checksum to remote copy...")
    with open(remote_file) as remote:
        remote_hash = [ x.split()[0] for x in remote ][0]
    if local_hash == remote_hash:
        return True
    else:
        return False


def check_retries_num(r):
    if r < 10:
        r += 1
        logging.info("Download attempt {} failed. Retrying...".format(r))
    else:
        logging.info("Download failed after 3 retries. Exiting...")
        sys.exit(1)
    return r

def extract_files_and_cleanup(outdir, files):
    for url in files:
        file = os.path.basename(url)
        logging.info(f"Extracting {file}...")
        subprocess.call(['tar', 'xvzf', os.path.join(outdir, file), '-C', outdir])
        os.remove(os.path.join(outdir, file))

def get_json_d(file):
    with open(file) as h:
        return json.load(h)

def get_metadata_file(database, outdir):
    metadata_n = f"{database}-nucl-metadata.json"
    metadata_p = f"{database}-prot-metadata.json"
    old_metadata_file = os.path.join(outdir, f'{database}-current-metadata.json')
    if os.path.isfile(old_metadata_file):
        old_mdd = get_json_d(old_metadata_file)
        old_lu = old_mdd["last-updated"]
        logging.info(f"Current {database} updated {old_lu}")
    else:
        old_lu = False
        logging.info(f"No local metadata file found, proceeding with download...")
    if remote_file_exists(metadata_n):
        download_file(metadata_n, outdir)
        mn = metadata_n
    elif remote_file_exists(metadata_p):
        download_file(metadata_p, outdir)
        mn = metadata_p
    else:
        logging.info("Can't locate database: {}. Please check that the name exists in https://ftp.ncbi.nih.gov/blast/db/".format(database))
        return False
    new_md = get_json_d(os.path.join(outdir, mn))
    new_lu = new_md["last-updated"]
    logging.info(f"Most recent {database} updated {new_lu}")
    if old_lu == new_lu:
        logging.info(f"No new verison of {database} available. Skipping download...")
        return False
    logging.info(f"Downloading most recent {database} version...")
    return mn


def test_if_numbered_dl(database):
    not_num = "{}.tar.gz".format(database)
    if remote_file_exists(not_num):
        return False
    i = '0'
    while len(i) < 6:
        num = "{}.{}.tar.gz".format(database, i)
        if remote_file_exists(num):
            return i
        i += '0'
    logging.info("Can't locate database: {}. Please check that the name exists in https://ftp.ncbi.nih.gov/blast/db/".format(database))
    sys.exit(1)

def download_archive_retry_if_fail(filename, outdir, archive_num, database, i):
    retries = 0
    while True:
        if not os.path.isfile(os.path.join(outdir, filename)):
            try:
                download_file(filename, outdir)
            except Exception as e:
                logging.error(f"Download of {filename} failed: {e}")
                os.remove(filename)
                retries = check_retries_num(retries)
                continue
        else:
            logging.info(f"{filename} already downloaded, checking integrity...")
        md5_local = calcmd5(os.path.join(outdir, filename))
        if i != False:
            md5_remote_file = "{}.{}.tar.gz.md5".format(database, str(archive_num).zfill(len(i)))
        else:
            md5_remote_file = "{}.tar.gz.md5".format(database)
        try:
            download_file(md5_remote_file, outdir)
            if md5_compare(md5_local, md5_remote_file) == True:
                logging.info(f"Download and md5 check of {filename} successful. Deleting md5 file...")
                os.remove(md5_remote_file)
                return True
            else:
                logging.info(f"md5 check of {filename} failed. Deleting files and retrying download...")
                os.remove(filename)
                os.remove(md5_remote_file)
                retries = check_retries_num(retries)
        except Exception as e:
            logging.error(f"Download of {md5_remote_file} failed. Restarting process: {e}")


def download_archive_retry_if_fail2(url, outdir):
    retries = 0
    filename = os.path.basename(url)
    filepath = os.path.join(outdir, filename)
    while True:
        if not os.path.isfile(filepath):
            try:
                download_file(filename, outdir)
            except Exception as e:
                logging.error(f"Download of {filename} failed: {e}")
                if os.path.isfile(filepath):
                    os.remove(filepath)
                retries = check_retries_num(retries)
                continue
        else:
            logging.info(f"{filename} already downloaded, checking integrity...")
        md5_local = calcmd5(filepath)
        md5_remote_file = "{}.md5".format(filename)
        md5_remote_local_copy = os.path.join(outdir, md5_remote_file)
        try:
            download_file(md5_remote_file, outdir)
            if md5_compare(md5_local, md5_remote_local_copy) == True:
                logging.info(f"Download and md5 check of {filename} successful. Deleting md5 file...")
                os.remove(md5_remote_local_copy)
                return True
            else:
                logging.info(f"md5 check of {filename} failed. Deleting files and retrying download...")
                if os.path.isfile(filepath):
                    os.remove(filepath)
                if os.path.isfile(md5_remote_local_copy):
                    os.remove(md5_remote_local_copy)
                retries = check_retries_num(retries)
        except Exception as e:
            logging.error(f"Download of {md5_remote_file} failed. Restarting process: {e}")

