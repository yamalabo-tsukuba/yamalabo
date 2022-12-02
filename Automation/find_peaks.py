import io
import sys
import numpy as np
import PySimpleGUI as sg
import scipy.signal as sp
import matplotlib.pyplot as plt


n_peaks = 10
n_smooth = 0

is_first_run = True
intensity_list = [False for _ in range(100)]


# get touples (wavelength, intensity, prominence) for each peak
def get_peaks(wavelength, intensity):
    
    # get the peak indecies and prominence values
    peak_idx = sp.find_peaks(intensity)[0]
    prominence_value = sp.peak_prominences(intensity, peak_idx)[0]
    
    # make a list of 
    peaks = [[wavelength[i], intensity[i], pr] for i, pr in zip(peak_idx, prominence_value)]
    
    # sort the list from high prominence to low prominence
    peaks = [peaks[i] for i in np.argsort(-prominence_value)]

    return(peaks)


# re-plot the graph and update the list of found peaks
def plot_peaks(wavelength, intensity, peaks, num_p):
    plt.figure()
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Intensity")
    plt.plot(wavelength, intensity)
    
    # extract peaks with high prominence in number of num_p
    peaks_x = [i[0] for i in peaks[:num_p]]
    peaks_y = [i[1] for i in peaks[:num_p]]
    
    # put the marker at the peak points
    plt.plot(peaks_x, peaks_y, linestyle='None', marker='*')
    
    # plot the graph inside the window
    item = io.BytesIO()
    plt.savefig(item, format='png')
    window['Graph'].update(item.getvalue())
    
    # update the text
    found_peaks = ''
    for i, j in enumerate(np.argsort(peaks_x[:num_p])):
        found_peaks += f'{i+1} : '.zfill(5)
        found_peaks += f'{round(peaks_x[j], 2)}'.ljust(7, '0')
        found_peaks += ' nm\n'
    window['Found Peaks'].update(found_peaks)
    
    
def smooth_wave(wavelength, intensity):
    new_wavelength, new_intensity = [], []
    for i in range(len(intensity)-1):
        new_wavelength.append((wavelength[i] + wavelength[i+1]) / 2)
        new_intensity.append((intensity[i]  + intensity[i+1]) / 2)

    return(new_wavelength, new_intensity)


# make a window
layout = [[sg.Text('Input File'), sg.InputText(), sg.FileBrowse(), sg.Button('Run')],
          [sg.Text(f'Find {n_peaks} peaks', key='find_number'),
           sg.Button('-', key='minus_peak'),
           sg.Button('+', key='plus_peak'),
           sg.Text(f'Smoothed {n_smooth} times', key='smoothing_number'),
           sg.Button('-', key='minus_smoothing'), sg.Button('+', key='plus_smoothing')],
          [sg.Image('', key='Graph')],
          [sg.Text('', key='Found Peaks')]]

window = sg.Window("File Select", layout, size=(650,800))


while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        sys.exit()

    if event == 'Run' and is_first_run:
        
        # get the absolute path of a text file of µ-PL measurement
        f = open(values['Browse']).read()
        
        # ignore the header information
        # if not only_wave_data:
        f = f.replace('\n', '\t')
        f = f.split('\t')
        wavelength = [float(w) for idx, w in enumerate(f[19:-1]) if idx%2==0]
        intensity  = [float(i) for idx, i in enumerate(f[19:-1]) if idx%2==1]
        
        peaks = get_peaks(wavelength, intensity)
        plot_peaks(wavelength, intensity, peaks, n_peaks)

        is_first_run = False
        intensity_list[n_smooth] = [wavelength, intensity]

        continue


    if event == 'plus_peak':
        n_peaks += 1
        window['find_number'].update(f'Find {n_peaks} Peaks')
        plot_peaks(wavelength, intensity, peaks, n_peaks)

        continue


    if event == 'minus_peak' and n_peaks > 0:
        n_peaks -= 1
        window['find_number'].update(f'Find {n_peaks} Peaks')
        plot_peaks(wavelength, intensity, peaks, n_peaks)

        continue


    if event == 'plus_smoothing':
        n_smooth += 1

        if intensity_list[n_smooth] != False:
            wavelength, intensity = intensity_list[n_smooth][0], intensity_list[n_smooth][1]
        else:
            wavelength, intensity = smooth_wave(wavelength, intensity)
            intensity_list[n_smooth] = [wavelength, intensity]
        
        peaks = get_peaks(wavelength, intensity)
        
        plot_peaks(wavelength, intensity, peaks, n_peaks)
        window['smoothing_number'].update(f'Smoothed {n_smooth} times')

        continue


    if event == 'minus_smoothing' and n_smooth > 0:
        n_smooth -= 1
        wavelength, intensity = intensity_list[n_smooth][0], intensity_list[n_smooth][1]
        
        peaks = get_peaks(wavelength, intensity)
        
        plot_peaks(wavelength, intensity, peaks, n_peaks)
        window['smoothing_number'].update(f'Smoothed {n_smooth} times')
        
        continue
