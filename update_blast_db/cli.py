import json, os, logging, argparse
from .download import get_metadata_file, download_archive_retry_if_fail2, extract_files_and_cleanup
from .diamond import prep4diamond
from datetime import datetime

def get_args():
    parser = argparse.ArgumentParser(description="Downloads given BLAST databases from ncbi hhtps")

    # Add arguments and options
    parser.add_argument('-d', '--databases', required=True, nargs='+', help='BLAST databases, e.g. nt nr ref_viroids_rep_genomes')
    parser.add_argument('-o', '--outdir', required=True, help='BLAST database output directory')
    parser.add_argument('-l', '--logdir', required=True, help='Directory to save log files')
    parser.add_argument('-e', '--diamond_exe', default='diamond', help='Path to diamond executable [diamond]')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    return args

def configure_logs(logfile, v):
    if v == True:
        logging.basicConfig(filename=logfile,format='%(asctime)s - %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(filename=logfile,format='%(asctime)s - %(message)s',level=logging.INFO)
    cmd_log = logging.StreamHandler()
    cmd_log.setLevel(logging.DEBUG if v else logging.INFO)
    logging.getLogger().addHandler(cmd_log)

def main():
    args = get_args()
    configure_logs(os.path.join(args.logdir, "blastdb.download_log.txt"), args.verbose)
    for database in args.databases:
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Download and extraction of {database} begun at {current_time}.")
        outdir = os.path.join(os.path.abspath(args.outdir), database)
        os.makedirs(outdir, exist_ok=True)
        metadata = get_metadata_file(database, outdir)
        if metadata:
            with open(os.path.join(outdir, metadata)) as mdjson:
                mdd = json.load(mdjson)
            for f in mdd['files']:
                download_archive_retry_if_fail2(f, outdir)
            logging.info(f"Extracting {database}...")
            extract_files_and_cleanup(outdir, mdd['files'])
            if metadata.endswith('-prot-metadata.json'):
                prep4diamond('diamond', outdir)
            os.rename(os.path.join(outdir, metadata), os.path.join(outdir, f'{database}-current-metadata.json'))
            logging.info("ncbi {} database downloaded and extracted successfully".format(database))

if __name__ == '__main__':
    main()