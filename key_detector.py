#!/usr/local/bin/python
# -*- coding: UTF-8 -*-

"""This script estimates the key of the songs contained in a folder,
and performs an evaluation of its results according to the MIREX
standard.
There are two modes of operation: 'txt' and 'title'.
In 'txt mode, the program expects a first argument indicating the route
to a folder containing the audio to be analysed, and a second argument
containing the route to the ground truth annotation as individual text
files. The program expects that the file names of both the audio and the
annotations are equal (except for the extension), and if the name do not
match it will skip the evaluation for that file.
In 'title' mode, the program looks for the ground-truth annotation embedded
in the name of the audio file itself, according to the following format:

FORMAT:  'Artist Name - Title of the Song = Key annotation < genre > DATASET.wav'
EXAMPLE: 'Audio Junkies - Bird On A Wire = F minor < edm > KF1000.wav'

Besides common python libraries, this script depends on a module named
"keytools" which is provided along this file.

                                              Ángel Faraldo, March 2015."""

# WHAT TO ANALYSE
# ===============
analysis_mode = 'txt' # {'txt', 'title'}

if analysis_mode == 'title':
    collection     = ['KF100', 'KF1000', 'GSANG', 'ENDO100', 'DJTECHTOOLS60'] # ['KF100', 'KF1000', 'GSANG', 'ENDO100', 'DJTECHTOOLS60']
    genre          = ['edm'] # ['edm', 'non-edm']
    modality       = ['minor', 'major'] # ['major', 'minor']
    limit_analysis = 0 # Limit analysis to N random tracks. 0 = all samples matching above criteria.

# ANALYSIS PARAMETERS
# ===================
# faraldo:
avoid_edges          = 0 # % of duration at the beginning and end that is not analysed.
first_n_secs         = 15 # only analyse the first N seconds of each track
skip_first_minute    = True
spectral_whitening   = True
shift_spectrum       = True
# print and verbose:
verbose              = True
confusion_matrix     = True
results_to_file      = True
results_to_csv       = True
confidence_threshold = 1
# global:
sample_rate          = 44100
window_size          = 4096
jump_frames          = 4 # 1 = analyse every frame; 2 = analyse every other frame; etc.
hop_size             = window_size * jump_frames
window_type          = 'hann'
min_frequency        = 25
max_frequency        = 3500
# spectral peaks:
magnitude_threshold  = 0.0001
max_peaks            = 60
# hpcp:
band_preset          = False
split_frequency      = 250 # if band_preset == True
harmonics            = 4
non_linear           = True
normalize            = True
reference_frequency  = 440
hpcp_size            = 36
weight_type          = "squaredCosine" # {none, cosine or squaredCosine}
weight_window_size   = 1 # semitones
# key detector:
profile_type         = 'temperley'
use_three_chords     = False # BEWARE: False executes the extra code including all triads!
use_polyphony        = False
num_harmonics        = 15  # when use_polyphony == True
slope                = 0.2 # when use_polyphony == True

# ////////////////////////////////////////////////////////////////////////////

# LOAD MODULES
# ============
import sys, os
import essentia as e
import essentia.standard as estd
from key_tools import *
from random import sample
from time import time as tiempo
from time import clock as reloj


def key_detector():
    reloj()
    # create directory to write the results with an unique time id:
    if results_to_file:
        uniqueTime = str(int(tiempo()))
        wd = os.getcwd()
        temp_folder = wd + '/KeyDetection_'+uniqueTime
        os.mkdir(temp_folder)
        if results_to_csv:
            import csv
            csvFile = open(temp_folder + '/_estimation&hpcp.csv', 'w')
            lineWriter = csv.writer(csvFile, delimiter=',')
    # retrieve files and filenames according to the desired settings:
    if analysis_mode == 'title':
        allfiles = os.listdir(audio_folder)
        if '.DS_Store' in allfiles: allfiles.remove('.DS_Store')
        for item in collection: collection[collection.index(item)] = ' > ' + item + '.'
        for item in genre: genre[genre.index(item)] = ' < ' + item + ' > '
        for item in modality:modality[modality.index(item)] = ' ' + item + ' < '
        analysis_files = []
        for item in allfiles:
            if any(e1 for e1 in collection if e1 in item):
                if any(e2 for e2 in genre if e2 in item):
                    if any(e3 for e3 in modality if e3 in item):
                        analysis_files.append(item)
        song_instances = len(analysis_files)
        print song_instances, 'songs matching the selected criteria:'
        print collection, genre, modality
        if limit_analysis == 0:
            pass
        elif limit_analysis < song_instances:
            analysis_files = sample(analysis_files, limit_analysis)
            print "taking", limit_analysis, "random samples...\n"
    else:
        analysis_files = os.listdir(audio_folder)
        if '.DS_Store' in analysis_files:
            analysis_files.remove('.DS_Store')
        print len(analysis_files), '\nsongs in folder.\n'
        groundtruth_files = os.listdir(groundtruth_folder)
        if '.DS_Store' in groundtruth_files:
            groundtruth_files.remove('.DS_Store')
    # ANALYSIS
    # ========
    if verbose:
        print "ANALYSING INDIVIDUAL SONGS..."
        print "============================="
    if confusion_matrix:
        matrix = 24 * 24 * [0]
    mirex_scores = []
    for item in analysis_files:
        # INSTANTIATE ESSENTIA ALGORITHMS
        # ===============================
        loader = estd.MonoLoader(filename=audio_folder+'/'+item,
        						 sampleRate=sample_rate)
        cut    = estd.FrameCutter(frameSize=window_size,
                                  hopSize=hop_size)
        window = estd.Windowing(size=window_size,
                                type=window_type)
        rfft   = estd.Spectrum(size=window_size)
        sw     = estd.SpectralWhitening(maxFrequency=max_frequency,
                                        sampleRate=sample_rate)
        speaks = estd.SpectralPeaks(magnitudeThreshold=magnitude_threshold,
                                    maxFrequency=max_frequency,
                                    minFrequency=min_frequency,
                                    maxPeaks=max_peaks,
                                    sampleRate=sample_rate)
        hpcp   = estd.HPCP(bandPreset=band_preset,
                           harmonics=harmonics,
                           maxFrequency=max_frequency,
                           minFrequency=min_frequency,
                           nonLinear=non_linear,
                           normalized=normalize,
                           referenceFrequency=reference_frequency,
                           sampleRate=sample_rate,
                           size=hpcp_size,
                           splitFrequency=split_frequency,
                           weightType=weight_type,
                           windowSize=weight_window_size)
        key    = estd.Key(numHarmonics=num_harmonics,
                          pcpSize=hpcp_size,
                          profileType=profile_type,
                          slope=slope,
                          usePolyphony=use_polyphony,
                          useThreeChords=use_three_chords)
        # ACTUAL ANALYSIS
        # ===============
        audio = loader()
        duration = len(audio)
        if skip_first_minute and duration > (sample_rate*60):
            audio = audio[sample_rate*60:]
            duration = len(audio)
        if first_n_secs > 0:
            if duration > (first_n_secs * sample_rate):
                audio = audio[:first_n_secs * sample_rate]
                duration = len(audio)
        if avoid_edges > 0:
            initial_sample = (avoid_edges * duration) / 100
            final_sample = duration - initial_sample
            audio = audio[initial_sample:final_sample]
            duration = len(audio)
        number_of_frames = duration / hop_size
        chroma = []
        for bang in range(number_of_frames):
            spek = rfft(window(cut(audio)))
            p1, p2 = speaks(spek) # p1 are frequencies; p2 magnitudes
            if spectral_whitening:
                p2 = sw(spek, p1, p2)
            chroma.append(hpcp(p1,p2))
        chroma = np.mean(chroma, axis=0)
        if shift_spectrum:
            chroma = shift_vector(chroma, hpcp_size)
        estimation = key(chroma.tolist())
        result = estimation[0] + ' ' + estimation[1]
        confidence = estimation[2]
        if results_to_csv:
            chroma = list(chroma)
        # MIREX EVALUATION:
        # ================
        if analysis_mode == 'title':
            ground_truth = item[item.find(' = ')+3:item.rfind(' < ')]
            if verbose and confidence < confidence_threshold:
                print item[:item.rfind(' = ')]
                print 'G:', ground_truth, '|| P:',
            if results_to_csv:
                title = item[:item.rfind(' = ')]
                # THIS IS A TEMPORARY SOLUTION... it should be improved!
                lineWriter.writerow([title, ground_truth, chroma[0], chroma[1], chroma[2], chroma[3], chroma[4], chroma[5], chroma[6], chroma[7], chroma[8], chroma[9], chroma[10], chroma[11], chroma[12], chroma[13], chroma[14], chroma[15], chroma[16], chroma[17], chroma[18], chroma[19], chroma[20], chroma[21], chroma[22], chroma[23], chroma[24], chroma[25], chroma[26], chroma[27], chroma[28], chroma[29], chroma[30], chroma[31], chroma[32], chroma[33], chroma[34], chroma[35], result])
            ground_truth = key_to_list(ground_truth)
            estimation = key_to_list(result)
            score = mirex_score(ground_truth, estimation)
            mirex_scores.append(score)
        else:
            filename_to_match = item[:item.rfind('.')] + '.txt'
            print filename_to_match
            if filename_to_match in groundtruth_files:
                groundtruth_file = open(groundtruth_folder+'/'+filename_to_match, 'r')
                ground_truth = groundtruth_file.readline()
                if results_to_csv:
                    # lineWriter.writerow([filename_to_match, ground_truth, chroma, result])
                    # THIS IS A TEMPORARY SOLUTION... it should be improved!
                    lineWriter.writerow([filename_to_match, chroma[0], chroma[1], chroma[2], chroma[3], chroma[4], chroma[5], chroma[6], chroma[7], chroma[8], chroma[9], chroma[10], chroma[11], chroma[12], chroma[13], chroma[14], chroma[15], chroma[16], chroma[17], chroma[18], chroma[19], chroma[20], chroma[21], chroma[22], chroma[23], chroma[24], chroma[25], chroma[26], chroma[27], chroma[28], chroma[29], chroma[30], chroma[31], chroma[32], chroma[33], chroma[34], chroma[35], result])
                ground_truth = key_to_list(ground_truth)
                estimation = key_to_list(result)
                score = mirex_score(ground_truth, estimation)
                mirex_scores.append(score)
            else:
                print "FILE NOT FOUND... Skipping it from evaluation.\n"
                continue
        # CONFUSION MATRIX:
        # ================
        if confusion_matrix:
            xpos = (ground_truth[0] + (ground_truth[0] * 24)) + (-1*(ground_truth[1]-1) * 24 * 12)
            ypos = ((estimation[0] - ground_truth[0]) + (-1 * (estimation[1]-1) * 12))
            matrix[(xpos+ypos)] =+ matrix[(xpos+ypos)] + 1
        if verbose and confidence < confidence_threshold:
            print result, '(%.2f)' % confidence, '|| SCORE:', score, '\n'
        # WRITE RESULTS TO FILE:
        # =====================
        if results_to_file:
            with open(temp_folder + '/' + item[:-3]+'txt', 'w') as textfile:
                textfile.write(result)
                textfile.close()
    if results_to_csv:
        csvFile.close()
    print len(mirex_scores), "files analysed in", reloj(), "secs.\n"
    if confusion_matrix:
        matrix = np.matrix(matrix)
        matrix = matrix.reshape(24,24)
        print matrix
        if results_to_file:
            np.savetxt(temp_folder + '/_confusion_matrix.csv', matrix, fmt='%i', delimiter=',', header='C,C#,D,Eb,E,F,F#,G,G#,A,Bb,B,Cm,C#m,Dm,Ebm,Em,Fm,F#m,Gm,G#m,Am,Bbm,Bm')
    # MIREX RESULTS
    # =============
    evaluation_results = mirex_evaluation(mirex_scores)
    # WRITE INFO TO FILE
    # ==================
    if results_to_file:
        settings = "SETTINGS\n========\nAvoid edges ('%' of duration disregarded at both ends (0 = complete)) = "+str(avoid_edges)+"\nfirst N secs = "+str(first_n_secs)+"\nshift spectrum to fit tempered scale = "+str(shift_spectrum)+"\nspectral whitening = "+str(spectral_whitening)+"\nsample rate = "+str(sample_rate)+"\nwindow size = "+str(window_size)+"\nhop size = "+str(hop_size)+"\nmagnitude threshold = "+str(magnitude_threshold)+"\nminimum frequency = "+str(min_frequency)+"\nmaximum frequency = "+str(max_frequency)+"\nmaximum peaks = "+str(max_peaks)+"\nband preset = "+str(band_preset)+"\nsplit frequency = "+str(split_frequency)+"\nharmonics = "+str(harmonics)+"\nnon linear = "+str(non_linear)+"\nnormalize = "+str(normalize)+"\nreference frequency = "+str(reference_frequency)+"\nhpcp size = "+str(hpcp_size)+"\nweigth type = "+weight_type+"\nweight window size in semitones = "+str(weight_window_size)+"\nharmonics key = "+str(num_harmonics)+"\nslope = "+str(slope)+"\nprofile = "+profile_type+"\npolyphony = "+str(use_polyphony)+"\nuse three chords = "+str(use_three_chords)
        results_for_file = "\n\nEVALUATION RESULTS\n==================\nCorrect: "+str(evaluation_results[0])+"\nFifth:  "+str(evaluation_results[1])+"\nRelative: "+str(evaluation_results[2])+"\nParallel: "+str(evaluation_results[3])+"\nError: "+str(evaluation_results[4])+"\nWeighted: "+str(evaluation_results[5])
        write_to_file = open(temp_folder + '/_SUMMARY.txt', 'w')
        write_to_file.write(settings)
        write_to_file.write(results_for_file)
        if analysis_mode == 'title':
            corpus = "\n\nANALYSIS CORPUS\n===============\n" + str(collection) + '\n' + str(genre) + '\n' + str(modality) + '\n\n' + str(len(mirex_scores)) + " files analysed.\n"
            write_to_file.write(corpus)
        write_to_file.close()


if __name__ == "__main__":
    if analysis_mode == 'txt':
        try:
            audio_folder = sys.argv[1]
            groundtruth_folder = sys.argv[2]
        except:
            print "ERROR! In 'txt' mode you should provide two arguments:"
            print "filename.py <route to audio> <route to ground-truth annotations>\n"
            sys.exit()
    elif analysis_mode == 'title':
        try:
            audio_folder = sys.argv[1]
        except:
            audio_folder = "/Users/angel/GoogleDrive/EDM/EDM_Collections/KEDM_mono_wav"
            print "-------------------------------"
            print "Analysis folder NOT provided. Analysing contents in:"
            print audio_folder
            print "If you want to analyse a different folder you should type:"
            print "filename.py route-to-folder-with-audio-and-annotations-in-filename"
            print "-------------------------------"
    else:
        print "Unrecognised analysis mode. It should be either 'txt' or 'title'."
        sys.exit()
    key_detector()
