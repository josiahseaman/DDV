This will guide you through installing FluentDNA as a python module called "FluentDNA".  This is the ideal
option for developers who want to integrate or tweak FluentDNA.  Non-technical users should use
a release from the [Releases Page](https://github.com/josiahseaman/FluentDNA/releases).  

## Quick Start
You will need:
1. Familiarity with the command line: [Windows Tutorial](https://github.com/pettarin/python-on-windows), [Mac Tutorial](http://docs.python-guide.org/en/latest/starting/install3/osx/#install3-osx)
1. Python (Windows must by Python 3.6 or newer): [Download Link](https://www.python.org/downloads/release/python-365/)
2. Git: [Download Link](https://git-scm.com/downloads)

**Installation**
From a command line in your python virtual environment:  
```
pip install --upgrade FluentDNA
```
If you get an error about html_template/ or example_data/ you need to **update pip and setuptools**.  Then rerun the FluentDNA install.
```
pip install --upgrade pip
pip install --upgrade setuptools
```

**Running**
fluentdna.py will be placed in the scripts folder and accessible through PYTHONPATH, it's a good idea to add this to PATH.
You should be able to use `fluentdna.py` as an executable from anywhere, depending on your setup. Running `fluentdna.py` with no arguments will point you to your *example_data/* and *results/* paths in your site packages, so you'll need to reference the full path.

`fluentdna.py --fasta="/path/to/site-packages/FluentDNA/example_data/hg38_chr19_sample.fa"`

**Note:** Windows ignores the #!/bin/usr/python line, you'll need to use python and the full path to the script:
`python C:\yourvenv\Scripts\fluentdna.py --fasta="C:\path\to\yourfasta.fa"`

To use the interactive browser, especially for large files, start a server.

`python /path/to/site-packages/FluentDNA/fluentdna.py --runserver`
If running on your local machine, this will open your browser at URL: `http://localhost:8000/`
If you are running FluentDNA through ssh to another computer you will need to talk to your administrator about opening a HTTP port.  The PORT is defined at the top of fluentdna.py under run_server().

To run FluentDNA from your own python script I recommend looking at fluentdna.py for examples such as `create_tile_layout_viz_from_fasta()`

### Example Commands
Check out the file https://github.com/josiahseaman/FluentDNA/blob/python-master/docs/example_DDV_commands.txt for more examples.

## Support Contact
If you run into any problems or would like to use FluentDNA in research, contact me at **josiah@newline.us**.  I'm happy to support my own software and always interested in new collaborations.

## FluentDNA Features

FluentDNA is a complete rewrite in Python of DDV.  FluentDNA has a much expanded feature set for handling
large, multipart files.  It can put an entire genome on a single image, marked with contig names.
FluentDNA has features for exploring genome alignments, annotations, and transposon alignments.
It was developed by Newline Technical Innovations and can be found at:
https://github.com/josiahseaman/FluentDNA/tree/python-master

## Python Versions
FluentDNA was primarily developed in Python 3.4.  After resolving [Issue #93](https://github.com/josiahseaman/FluentDNA/issues/93) we've been able to install in 3.7 and 3.8.  `blist` is not currently available for 3.7+ which means that genome alignment is not recommended.  I use wheel files to get around this problem available at [gohlke](https://www.lfd.uci.edu/~gohlke/pythonlibs/#blist).  Conda numpy does not support any Python older than 3.5.0.


# Compile Instructions for Developers:
PyInstaller is our platform for generating binary files for each release.  This is currently working in Windows and will be used to generate Mac DMG as well.  In theory, one can checkout the FluentDNA source code, install the dependencies into a new python environment, and then run
```
pip install pyinstaller==3.3.1
PyInstaller fluentdna.spec --clean --noconfirm
```
to generate a binary.  In practice, this will require some experimentation with version numbers to get everything installed.
* Make sure you use a fresh virtual environment as everything in your python will be included in the executable.
* Do not build from an Anaconda environment or you will get a 600MB build instead of a 30MB build.

### Windows with PyInstaller
* Requires Python 3.6.5, earlier versions are not compatible with pywin32
    * pypiwin32 is an alternative
* Earlier mentions of pip and setuptools versions were for cx_freeze.  For PyInstaller, just install the latest
* blist wouldn't compile because of a C++ dependency
* Download blist "wheel" from https://www.lfd.uci.edu/~gohlke/pythonlibs/#blist
* D:\python365\Scripts\easy_install.exe "D:\josiah\Documents\Downloads\blist-1.3.6-cp36-cp36m-win_amd64.whl"
* `pip install pyinstaller==3.3.1`
* `PyInstaller fluentdna.spec`

**Troubleshooting**: I repeated pip installs first with the existing Requirements.txt (designed for cx_freeze) then tried the most recent version if that didn't work.  In general the most recent version of a module worked.  
`D:\python365\Scripts\pip.exe list`  
altgraph (0.15)  
blist (1.3.6)  
DNASkittleUtils (1.0.13)  
future (0.16.0)  
macholib (1.9)  
natsort (5.1.1)  
pefile (2017.11.5)  
Pillow (5.1.0)  
pip (9.0.3)  
psutil (5.4.5)  
PyInstaller (3.3.1)  
pypiwin32 (223)  
pywin32 (223)  
setuptools (39.0.1)  


### Mac with PyInstaller
* Start by [downloading Python 3.6.5](https://www.python.org/downloads/release/python-365/) and use that as your fresh environment
```
/Python365/Scripts/pip install PyInstaller
cd <your FluentDNA directory>
/Python365/Scripts/pip install -r Requirements.txt
PyInstaller fluentdna.spec
```
You may need to troubleshoot the contents of fluentdna.spec using [this documentation](https://pyinstaller.readthedocs.io/en/v3.3.1/spec-files.html#spec-file-options-for-a-mac-os-x-bundle)  
The most common thing I have to troubleshoot is the path to *html_template*.  Make sure to test font and *border_box_corner.png* paths using:  
`./fluentdna --fasta=example_data/whole_genome_alignment/chr21_hg38_gapped.fa --extrafastas example_data/whole_genome_alignment/chr21_hg38_unique.fa example_data/whole_genome_alignment/panTro5_to_hg38_chr21_unique.fa example_data/whole_genome_alignment/panTro5_to_hg38_chr21_gapped.fa --outname="Test Parallel Layout"`


## Updating PyPI pip index using Twine
These instructions are mainly for future Josiah, since no one has a perfect memory.
* Tutorial here: https://packaging.python.org/tutorials/packaging-projects/#description
* Download Python 3.7, create virtual environment ./env/, activate it.  
```
python -m pip install --user --upgrade setuptools wheel  
python setup.py sdist bdist_wheel  
python -m pip install --user --upgrade twine
python -m pip install --upgrade --index-url https://test.pypi.org/simple/ fluentdna 
# important this will not install dependencies that are not on test.PyPI
```
* Verify program is working correctly, resource paths are all correct.
* Upload the official version to `twine upload dist/*` 
* You have to manually type your unique password; no pasting, you masochist.

### Linux using cx_freeze:
This method is out of date after the pip refactor and switch to PyInstaller platform.  Consider following the Mac example and use [PyInstaller for Linux](https://pyinstaller.readthedocs.io/en/v3.3.1/requirements.html#linux) instead.

  - Requires ldd and objdump installed (probably already on your system)
  - Install Mercurial `sudo apt-get install mercurial`
  - You need a custom compiled version of Python3.4 (will use instead of venv)

        sudo apt-get install zlib1g-dev libbz2-dev libncurses5-dev libreadline6-dev libsqlite3-dev libssl-dev libgdbm-dev liblzma-dev tk8.5-dev
        wget https://www.python.org/ftp/python/3.4.3/Python-3.4.3.tgz
        tar zxvf Python-3.4.3.tgz
        rm Python-3.4.3.tgz
        cd Python-3.4.3/
        ./configure --prefix=/path/to/projects/ddv_python --exec_prefix=/path/to/projects/ddv_python
        make
        make altinstall
        /path/to/projects/ddv_python/bin/pip uninstall setuptools
        /path/to/projects/ddv_python/bin/pip uninstall pip
        wget https://pypi.python.org/packages/source/s/setuptools/setuptools-3.4.4.tar.gz
	    tar -vzxf setuptools-3.4.4.tar.gz
	    rm setuptools-3.4.4.tar.gz
	    cd setuptools-3.4.4
        /path/to/projects/ddv_python/bin/python setup.py install
        cd ..
        rm -r setuptools-3.4.4/
        wget https://pypi.python.org/packages/source/p/pip/pip-1.5.6.tar.gz
	    tar -vzxf pip-1.5.6.tar.gz
	    rm pip-1.5.6.tar.gz
	    cd pip-1.5.6
	    /path/to/projects/ddv_python/bin/python setup.py install
	    cd ..
	    rm -r pip-1.5.6

  - Using the new python, install all the requirements `/path/to/projects/ddv_python/bin/pip install -r /path/to/FluentDNA/Requirements.txt`
  - `/path/to/projects/ddv_python/bin/pip install hg+https://bitbucket.org/BryanHurst/cx_freeze`
    - If the above install fails, then there is a problem with your python shared libraries, I have a clone of the cx_freeze repo with a temp fix
      - CD to a directory where you want to download it, then `hg clone hg+https://bitbucket.org/BryanHurst/cx_freeze; cd cx_freeze; /path/to/projects/adsm_python/bin/python setup.py install`
