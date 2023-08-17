# Update BLAST DB

## Overview

`Update BLAST DB` automatically downloads designated BLAST databases from NCBI over https. 

## Installation

To install `Update BLAST DB`:

```
git clone https://github.com/bogemad/update_blast_db.git
cd update_blast_db
pip install .
```

## Usage
To download nt and nr databases from NCBI over https.

update_blast_db -d [DATABASES] -o [OUTPUT_DIRECTORY] -l [LOG_DIRECTORY]

Multiple databases can be downloaded at once (e.g. -d nt nr etc.)

## Contributing
Contributions welcome.

## License
Watch this space...
