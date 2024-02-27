# Instax Parsing & Annotating for Digital Archiving

This repo contains two python scripts to help process Instax (& Polaroids, with tweaks) photos for digital archiving.

   `process_scan` &rarr; take a flatbed scanner output and parse it into N separate photos

   `process_photo` &rarr; annotate an individual instax photo with location, date, and description

## Getting Started

1. Make sure you have Python installed on your system.  
   1. I use `Python 3.9.18`, [pyenv](https://github.com/pyenv/pyenv) to manage different python installations, and 
   [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) to manage `instax` virtual env.

2. Clone or download this repository to your local machine.
3. Install the required dependencies using pip:

```shell
pip install -r requirements.txt
```

4. Try out the demos I included for both scripts
   1. See [scanning demo](scripts/scan/readme.md#example)
   2. See [annotating demo](scripts/photo/readme.md#example)

## Questions? Comments? Want to contribute?

I had a collection of about 500 instax photos to archive, and I needed a tool to do this. So, I built this.

Please feel free to contribute with feature requests or put up your own PR. There are many not-so-ideal things about 
this script, and parts of it are very ugly. 

I am familiar with Computer Vision concepts and the theory behind them, but certainly no expert. I tried to use some 
open source Deep Learning models from Hugging Face rather than use these basic concepts of contours and gradient 
filtering, but this got me close enough [shrug].

I take a lot of instax photos with friends, so I intend on actively using this and maintaining this tool.
