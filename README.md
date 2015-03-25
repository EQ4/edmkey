# edmkey
Python scripts for automatic key detection in EDM

This repository provides scripts for key detection and its evaluation. 
It also contains a program to automatically extract key-profiles from a corpus.
They are based on a fork of MTG's Music Information Retrieval Library "Essentia"
which can be downloaded from the following link:

https://github.com/angelfaraldo/essentia/tree/angel_key_detection

You can follow instructions of that page, or visit the home page of 
Essentia (http://essentia.upf.edu/) for further information about the
library and how to build it and install it. Detailed instructions and 
dependencies here:

http://essentia.upf.edu/documentation/installing.html
_____________________________________________________________________________

"key_detector.py" estimates the key of the songs contained in a folder,
and performs an evaluation of its results according to the MIREX standard.
It generate text files with the key estimations for further evaluation
as well as a summary with the parameters used and confusion matrixes as 
cvs files.

There are two modes of operation: 'txt' and 'title'. In 'txt mode, the program 
expects a first argument indicating the route to a folder containing the audio 
to be analysed, and a second argument containing the route to the ground-truth
annotation as individual text files. The program expects that the file names
of both the audio and the annotations are equal (except for the extension),
and if the name do notmatch it will skip the evaluation for that file. In
'title' mode, the program looks for the ground-truth annotation embedded
in the name of the audio file itself, according to the following format:

FORMAT: Artist Name - Title of the Song = Key annotation < genre > DATASET.wav
EXAMPLE: Audio Junkies - Bird On A Wire = F minor < edm > KF1000.wav

Besides common python libraries, this script depends on a module named
"key_tools.py" which is provided along this file.

Ángel Faraldo, March 2015.
