import subprocess, os

def prep4diamond(diamond_exe, outdir):
    db_loc = os.path.join(outdir, os.path.basename(outdir))
    subprocess.run([diamond_exe, 'prepdb', '-d', db_loc])