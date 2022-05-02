import PySimpleGUI as sg
import pyautogui as pag
import time

sg.theme('BrownBlue')

# create a window
layout = [[sg.Text('Interval / second'),  sg.InputText(key='-interval-')],
          [sg.Text('Repeat / times  '),  sg.InputText(key='-repeat-')],
          [sg.Button('Run', key='-run-')]]

# show the window
window = sg.Window('Auto Save', layout, size=(200,80))

while True:
    event, values = window.read()

    if event == '-run-':
    
        """
        interval(s)   : time interval between taking photos
        repeat(times) : number of iteration
        """
        
        interval = int(values['-interval-'])
        repeat   = int(values['-repeat-'])
        
        # open the software
        pag.click(85,1175)

        for i in range(repeat+1):
        
            # take a photo
            pag.press('f8')

            time.sleep(1)
            
            # save the photo
            pag.keyDown('ctrl')
            pag.press('s')
            pag.keyUp('ctrl')
            
            # enter the file name (XXs)
            for j in range(len(str(i*interval))): # 
                pag.press(str(i*interval)[j])
            pag.press('s')
            
            pag.press('enter')
            pag.press('enter')
        
            # wait saving the photo
            time.sleep(5)

            # delete the temporary image file
            pag.keyDown('ctrl')
            pag.press('w')
            pag.keyUp('ctrl')

            # reset the camera
            pag.press('f7')

            # interval
            time.sleep(interval-6)

    if event == sg.WIN_CLOSED:
        break

    window.close()
