import io
import sys
import math
import seaborn
import numpy as np
import pandas as pd
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

    global n_figure
    n_figure += 1
    
    # extract peaks with high prominence in number of n_peaks
    peaks_x = [i[0] for i in peaks[:n_peaks]]
    peaks_y = [i[1] for i in peaks[:n_peaks]]
    
    plt.figure()
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Normalized Int.")
    plt.plot(wavelength, intensity)
    for i, xy in enumerate(zip(peaks_x, peaks_y)):
        plt.vlines(xy[0], 0, xy[1], colors='red', linestyles='dotted')
        plt.text(xy[0], xy[1]+0.01, f'{i+1}', color='black', size=7, horizontalalignment='center')
    
    # update the text
    found_peaks = ''
    for i, j in enumerate(np.argsort(peaks_x[:n_peaks])):
        found_peaks += f'{i+1} : '.zfill(5)
        found_peaks += f'{round(peaks_x[j], 2)}'.ljust(7, '0')
        found_peaks += ' nm\n'

    window['Found Peaks'].update(found_peaks)
        
    # plot the graph inside the window
    item = io.BytesIO()
    plt.savefig(item, format='png')
    window['Graph'].update(item.getvalue())
    
    return


def calc_te(n, d, m) -> float:
    """
    Calculate wavelength of TE modes

    Args:
        n (float): Refractive Index
        d (float): Diameter / nm
        m (int)  : Mode Number
    """
    
    return n * math.pi * d / ((m+0.5) + 1.85576 * ((m+0.5) ** (1/3)) - (1/n**2) * (n**2/(n**2-1)) ** 0.5)


def calc_tm(n, d, m) -> float:
    """
    Calculate wavelength of TM modes

    Args:
        n (float): Refractive Index
        d (float): Diameter / nm
        m (int)  : Mode Number
    """
    
    return n * math.pi * d / ((m+0.5) + 1.85576 * ((m+0.5) ** (1/3)) - (n**2/(n**2-1)) ** 0.5)


n_peaks, n_smooth, n_figure = 10, 0, 0
is_first_run = True
intensity_list = [False for _ in range(100)]


# make a window
layout = [[sg.Text('Input File'), sg.InputText(), sg.FileBrowse(), sg.Button('View')],
          
          [sg.Text(f'Find {n_peaks} peaks', key='find_number'),
           sg.Button('-', key='minus_peak'),
           sg.Button('+', key='plus_peak'),
           sg.Text(f'Smoothed {n_smooth} times', key='smoothing_number'),
           sg.Button('-', key='minus_smoothing'), sg.Button('+', key='plus_smoothing')],
          
          [sg.Text('Refractive Index :'),
           sg.InputText('1.3', size=(5, 1), key='n_start'),
           sg.Text('        ~'),
           sg.InputText('1.8', size=(5, 1), key='n_stop'),
           sg.Text('       Step :'),
           sg.InputText('0.01', size=(5, 1), key='n_step')],
          
          [sg.Text('Diameter :           '),
           sg.InputText('3.0', size=(5, 2), key='d_start'),
           sg.Text('µm   ~'),
           sg.InputText('15.0', size=(5, 2), key='d_stop'),
           sg.Text('µm   Step :'),
           sg.InputText('0.01', size=(5, 2), key='d_step'),
           sg.Text('µm'),
           sg.Button('WGM Assign', key='assign', button_color='orange'),
           sg.Text('', key='message'),],
          
          [sg.Image('', key='Graph')],
          
          [sg.Text('', key='Found Peaks')]]

window = sg.Window("WGM Assign", layout, size=(650,600))


while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        sys.exit()

    if event == 'View' and is_first_run:
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
            sg.popup_error('The data style is NOT supported')
        
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
    
        
    if event == 'assign':
        window['message'].update('Now Processing. Please Wait ...')
        
        peak_wave = [i[0] for i in peaks[:n_peaks]]
        wave_min, wave_max = min(wavelength), max(wavelength)
        
        n_start, n_stop, n_step = float(values['n_start']), float(values['n_stop']), float(values['n_step'])
        d_start, d_stop, d_step = float(values['d_start'])*1000, float(values['d_stop'])*1000, float(values['d_step'])*1000
        n_loop = ((n_stop - n_start) / n_step) * ((d_stop - d_start ) / d_step)
        
        n_range = np.arange(start=n_start, stop=n_stop+n_step, step=n_step)  # refractive index
        d_range = np.arange(start=d_start, stop=d_stop+d_step, step=d_step)  # diameter / nm

        df = pd.DataFrame(np.zeros((len(n_range), len(d_range))))
        df.columns =[f'{round(d/1000, 4)}' for d in d_range]
        df.index = [f'{round(n, 4)}' for n in n_range]
        
        counter = 0
        score_list = np.empty([len(n_range) * len(d_range), 3])     
        
        for n in n_range:
            for d in d_range:
            
                score = 0
                pred_te = [calc_te(n, d, i) for i in range(1, 200) if wave_min < calc_te(n, d, i) < wave_max]
                pred_tm = [calc_tm(n, d, i) for i in range(1, 200) if wave_min < calc_tm(n, d, i) < wave_max]
                
                for x in pred_te + pred_tm:
                    for peak in peak_wave:
                        if peak - 1 < x < peak + 1: score += 1 - abs(peak - x)
                
                if score > len(peak_wave): score = len(peak_wave)
                    
                score_list[counter] = n, d, score
                
                df.at[f'{round(n, 4)}', f'{round(d/1000, 4)}'] = score

                counter += 1
                print(f'{round(100 * counter / n_loop, 2)} % done', end='\r')               
                
                
        plt.figure()
        heatmap = seaborn.heatmap(df, cmap='OrRd')
        heatmap.set(xlabel='Diameter / µm', ylabel='Refractive Index')
        plt.savefig('score.png', format="png", dpi=300)
        

        best_idx = score_list[:, 2].argmax()
        n, d = score_list[best_idx][0], score_list[best_idx][1]

        pred_te = [(i, calc_te(n, d, i)) for i in range(1, 200) if wave_min < calc_te(n, d, i) < wave_max]
        pred_tm = [(i, calc_tm(n, d, i)) for i in range(1, 200) if wave_min < calc_tm(n, d, i) < wave_max]
        
        plt.figure()
        plt.suptitle(f'Diameter = {d/1000} µm  Refractive Index = {n}')
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Normalized Int.") 
        plt.plot(data[:, 0], data[:, 1]/max(data[:, 1]))
        plt.vlines(np.array(pred_te)[:, 1], 0, 1, colors='orange')
        plt.vlines(np.array(pred_tm)[:, 1], 0, 1, colors='green')
        for te, tm in zip(pred_te, pred_tm):
            plt.text(te[1], 1, f'TE{te[0]}', color='orange', horizontalalignment='center', rotation='vertical')
            plt.text(tm[1], 1, f'TM{tm[0]}', color='green', horizontalalignment='center', rotation='vertical')
        for i in range(1, n_figure+1): plt.close(i)
        plt.savefig('WGM_assign.png', format="png", dpi=300)
        plt.show()
        
        sys.exit()
        
    continue
