import pandas as pd
import numpy as np
import epics
from . import transmission_models as tm
from logbook2mouse.scan import scan
from logbook2mouse.measure_config import (
    move_motor, move_to_sampleposition
    )
from pathlib import Path

def center_pitch(experiment, limits, npoints, sampleposition, store_location):
    "scan of pitch angle with fit, ensuring that the motor is always scanned in the negative direction"
    if limits[0] < limits[1]:
        scan("pitchgi", limits[0], limits[1], npoints, 1,
             experiment, sampleposition, store_location)
    else:
        scan("pitchgi", limits[1], limits[0], npoints, 1,
             experiment, sampleposition, store_location)
    data = pd.read_csv(store_location / "current_scan.csv", delimiter = ",",
                       )
    motorname = data.columns[0].split(":")[-1]

    res = tm.pitch_model.fit(data[data.columns[1]].values, tm.pitch_params, 
                          x = data[data.columns[0]].values, 
                          )
    center = res.best_values["x0"]
    beam_offset = res.best_values["beam_center"]
    tm.pitch_params["x0"].set(value = center, min = -1,  max = 1)
    return center, beam_offset

def zheavy_center(experiment, limits, npoints, sampleposition, store_location):
    scan("zheavy", limits[0], limits[1], npoints, 1,
         experiment, sampleposition, store_location)
    data = pd.read_csv(store_location / "current_scan.csv", delimiter = ",",
                       )
    motorname = data.columns[0].split(":")[-1]
    xvals = data[data.columns[0]].values
    res = tm.z_model.fit(data[data.columns[1]].values, tm.z_params, 
                          x = xvals, 
                          )
    center = res.best_values["center"]
    tm.z_params["center"].set(value = center, min = 2, max = 6)
    sigma = res.best_values["sigma"]
    tm.pitch_params["beam_sigma"].set(value = sigma, min = 0, max = 1, vary = False)
    tm.z_params["sigma"].set(value = sigma, min = 0, max = 1)
    return center, sigma 

def horizontal_center(experiment, limits, npoints, sampleposition, store_location):
    scan("ysam", limits[0], limits[1], npoints, 1,
                      experiment, sampleposition, store_location)
    data = pd.read_csv(store_location / "current_scan.csv", delimiter = ",",
                       )
    motorname = data.columns[0].split(":")[-1]

    res = tm.gap_model.fit(data[data.columns[1]].values, tm.gap_params, 
                          x = data[data.columns[0]].values, 
                          )
    center = 0.5*(res.best_values["center1"]+res.best_values["center2"])
    y = data[data.columns[1]].values
    x = data[data.columns[0]].values
    center = np.sum(x*(1-y))/np.sum(1-y)
    return center 

def pitch_limit(sigma_beam, halfsample):
    # \(\pm 2 \frac{\sigma_{\mathrm{beam}}}{\tfrac{1}{2} l_{\mathrm{sample}}}\)
    return np.rad2deg(2 * sigma_beam/halfsample)

def pitch_align(experiment, start_z, start_pitch, sigma_beam, halfsample=15, sampleposition={"ysam.blank": -66}, store_location=Path('.')):
    center, sigma = start_z, sigma_beam
    move_motor("zheavy", center)
    move_motor("pitchgi", start_pitch)
    #center, sigma = zheavy_center(scanmanager,
    # not sure how the logic of this works
    pitch_center = start_pitch
    new_center, new_sigma = zheavy_center(experiment, (-2*sigma_beam, +2*sigma_beam), 31,
                                          sampleposition, store_location)
    move_motor("zheavy", new_center) 
    pitch_delta = pitch_limit(new_sigma, halfsample)
    new_pitch_center, new_beam_offset = center_pitch(experiment, (-pitch_delta, +pitch_delta), 31,
                                                     sampleposition, store_location)
    move_motor("pitchgi", new_pitch_center)
    move_motor("zheavy", new_center+new_beam_offset)
    # with stopping condition but not adaptive number of points 
    while abs(new_center - center) > 0.01 or abs(new_pitch_center - pitch_center) > 0.002:
        center = new_center
        pitch_center = new_pitch_center
        beam_offset = new_beam_offset
        new_center, new_sigma = zheavy_center(experiment, (-2*sigma_beam, +2*sigma_beam), 31,
                                              sampleposition, store_location)
        move_motor("zheavy", new_center) 
        pitch_delta = pitch_limit(new_sigma, halfsample)
        new_pitch_center, new_beam_offset = center_pitch(experiment, (-pitch_delta, +pitch_delta), 31,
                                                         sampleposition, store_location)
        move_motor("pitchgi", new_pitch_center)
        move_motor("zheavy", new_center+new_beam_offset)
        logging.info(f"preliminary horizontal position pitch: {new_pitch_center}°")
        logging.info(f"preliminary sample surface, vertical position: {new_center} mm")
    return new_pitch_center, new_center 
        
    
def roll_align(experiment, y_center, sigma_beam, rolloffset, centerofrotation = 30,
               sampleposition={"ysam.blank": -66}, store_location=Path(".")):
    y_neg = y_center - rolloffset
    move_motor("ysam", y_neg)
    neg_center, sigma = zheavy_center(experiment, (-2*sigma_beam, +2*sigma_beam), 31,
                                      sampleposition, store_location)
    y_pos = y_center + rolloffset
    move_motor("ysam", y_pos)
    pos_center, sigma = zheavy_center(experiment, (-2*sigma_beam, +2*sigma_beam), 31,
                                      sampleposition, store_location)
    print("positive edge:", pos_center)
    print("negative edge:", neg_center)
    rollangle = np.rad2deg(np.arctan((pos_center - neg_center)/(2 * rolloffset)))
    print("roll angle:", rollangle)
    oldroll = epics.caget("mc0:rollgi")
    move_motor("rollgi", oldroll + rollangle) # to do: check sense of roll stage
    move_motor("ysam", y_center)
    if np.sign(y_pos - centerofrotation) == np.sign(y_neg - centerofrotation):
        new_z = np.tan(np.deg2rad(oldroll + rollangle))*abs(y_center - centerofrotation)
    else:
        new_z = None
    return oldroll + rollangle, new_z

def main():
    pass

if __name__ == "__main__":
    main()

