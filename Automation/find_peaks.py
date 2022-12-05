import io
import sys
import numpy as np
import PySimpleGUI as sg
import scipy.signal as sp
import matplotlib.pyplot as plt


def get_peaks(wavelength, intensity) -> tuple:
    """
    return touples of (wavelength, intensity, prominence) for each peak

    Args:
        wavelength (array_like): wavelength / nm
        intensity  (array_like): intensity / a.u.
    """
    
    # get the peak indecies and prominence values
    peak_idx = sp.find_peaks(intensity)[0]
    prominence_value = sp.peak_prominences(intensity, peak_idx)[0]
    peaks = [[wavelength[i], intensity[i], pr] for i, pr in zip(peak_idx, prominence_value)]
    
    # sort the list from high prominence to low prominence
    peaks = [peaks[i] for i in np.argsort(-prominence_value)]

    return(peaks)


def smooth_wave(wavelength, intensity) -> tuple:
    """
    return n-smoothed wavelength and intensity

    Args:
        wavelength (array_like): wavelength / nm
        intensity  (array_like): intensity / a.u.
    """
    N = len(wavelength)
    new_wavelength = [(wavelength[i] + wavelength[i+1]) / 2 for i in range(N-1)]
    new_intensity  = [(intensity[i]  + intensity[i+1])  / 2 for i in range(N-1)]

    return (new_wavelength, new_intensity)


def plot_peaks(wavelength, intensity, peaks, n_peaks) -> None:
    """
    plot or re-plot the graph and update the list of "found peaks"

    Args:
        wavelength (array_like): wavelength / nm
        intensity  (array_like): intensity / a.u.
        peaks      (tuple): (wavelength, intensity, prominence) for each peak
        n_peaks    (int): number of peaks to plot
    """
    
    # extract peaks with high prominence in number of n_peaks
    peaks_x = [i[0] for i in peaks[:n_peaks]]
    peaks_y = [i[1] for i in peaks[:n_peaks]]
    
    plt.figure()
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Normalized Int.")
    plt.plot(wavelength, intensity)
    for x, y in zip(peaks_x, peaks_y): plt.vlines(x, 0, y, colors='red', linestyles='dotted')
    
    # update the text
    found_peaks = ''
    for i, j in enumerate(np.argsort(peaks_x[:n_peaks])):
        found_peaks += f'{i+1} : '.zfill(5)
        found_peaks += f'{round(peaks_x[j], 2)}'.ljust(7, '0')
        found_peaks += ' nm\n'
        plt.text(peaks_x[j], peaks_y[j]+0.01, f'{i+1}', color='black', size=7, horizontalalignment='center')
    window['Found Peaks'].update(found_peaks)
        
    # plot the graph inside the window
    item = io.BytesIO()
    plt.savefig(item, format='png')
    window['Graph'].update(item.getvalue())
    
    return


n_peaks, n_smooth = 10, 0
is_first_run = True
intensity_list = [False for _ in range(100)]


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
        data = open(values['Browse']).read()
        
        # csv data
        if values['Browse'].endswith('csv'):
            data = np.loadtxt(values['Browse'], delimiter=",")
            wavelength = data[:, 0]
            intensity  = data[:, 1]
        # µ-PL data
        elif values['Browse'].endswith('txt'):
            # ignore the header information
            # if not only_wave_data:
            data = data.replace('\n', '\t')
            data = data.split('\t')
            wavelength = np.array([float(w) for idx, w in enumerate(data[19:-1]) if idx%2==0])
            intensity  = np.array([float(i) for idx, i in enumerate(data[19:-1]) if idx%2==1])
        # other data style
        else:
            sg.popup_error('The input data style is not supported')
        
        is_first_run = False
        intensity_list[n_smooth] = [wavelength, intensity]
        
        peaks = get_peaks(wavelength, intensity)
        
        plot_peaks(wavelength, intensity, peaks, n_peaks)

        continue


    # Change the number of peaks
    if event == 'plus_peak' or (event == 'minus_peak' and n_peaks > 0):
        if event == 'plus_peak':  n_peaks += 1
        if event == 'minus_peak': n_peaks -= 1
        
        window['find_number'].update(f'Find {n_peaks} Peaks')
        plot_peaks(wavelength, intensity, peaks, n_peaks)

        continue


    # Change the number of smoothing
    if event == 'plus_smoothing' or (event == 'minus_smoothing' and n_smooth > 0):
        if event == 'plus_smoothing':  n_smooth += 1
        if event == 'minus_smoothing': n_smooth -= 1

        if intensity_list[n_smooth] != False:
            wavelength, intensity = intensity_list[n_smooth]
        else:
            wavelength, intensity = smooth_wave(wavelength, intensity)
            intensity_list[n_smooth] = wavelength, intensity
        
        peaks = get_peaks(wavelength, intensity)
        
        window['smoothing_number'].update(f'Smoothed {n_smooth} times')
        plot_peaks(wavelength, intensity, peaks, n_peaks)

        continue
