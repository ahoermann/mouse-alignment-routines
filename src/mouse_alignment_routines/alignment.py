import pandas as pd
import numpy as np
import epics
from . import transmission_models as tm
from logbook2mouse.scan import scan
from logbook2mouse.measure_config import (
    move_motor, move_to_sampleposition
    )
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO)

def center_pitch(experiment, limits, npoints, sampleposition, pitchmodel, store_location):
    "scan of pitch angle with fit, ensuring that the motor is always scanned in the negative direction"
    if limits[0] < limits[1]:
        scan("pitchgi", limits[0], limits[1], npoints, 1,
             experiment, sampleposition, store_location)
    else:
        scan("pitchgi", limits[1], limits[0], npoints, 1,
             experiment, sampleposition, store_location)
    data = pd.read_csv(Path("/home/ws8665-epics/scan-using-epics-ioc/current_scan.csv"), delimiter = ",",
                       )
    motorname = data.columns[0].split(":")[-1]

    res = pitchmodel.model.fit(data[data.columns[1]].values, pitchmodel.parameters, 
                         x = data[data.columns[0]].values,
                               method="basinhopping",
                         )
    center = res.best_values["x0"]
    beam_offset = res.best_values["beam_center"]
    pitchmodel.parameters["x0"].set(value = center, min = -1,  max = 1)
    pitchmodel.parameters["beam_center"].set(value = center)
    print('pitch fit', res.best_values)
    return center, beam_offset, pitchmodel

def zheavy_center(experiment, limits, npoints, sampleposition, zheavymodel, store_location):
    scan("zheavy", limits[0], limits[1], npoints, 1,
         experiment, sampleposition, store_location)
    data = pd.read_csv(Path("/home/ws8665-epics/scan-using-epics-ioc/current_scan.csv"), delimiter = ",",
                       )
    motorname = data.columns[0].split(":")[-1]
    xvals = data[data.columns[0]].values
    res = zheavymodel.model.fit(data[data.columns[1]].values, zheavymodel.parameters,
                                x = xvals,
                                )
    center = res.best_values["center"]
    zheavymodel.parameters["center"].set(value = center)
    sigma = res.best_values["sigma"]
    return center, sigma, zheavymodel 

def horizontal_center(experiment, limits, npoints, sampleposition, store_location):
    scan("ysam", limits[0], limits[1], npoints, 1,
                      experiment, sampleposition, store_location)
    data = pd.read_csv(Path("/home/ws8665-epics/scan-using-epics-ioc/current_scan.csv"), delimiter = ",",
                       )
    motorname = data.columns[0].split(":")[-1]

    res = tm.gap_model.fit(data[data.columns[1]].values, tm.gap_params, 
                          x = data[data.columns[0]].values,
                           method='basinhopping'
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

    pitchmodel = tm.PitchModel(samplelength=halfsample)
    zheavymodel = tm.ZheavyModel(sigma = sigma_beam, center = start_z)
    
    #center, sigma = zheavy_center(scanmanager,
    # not sure how the logic of this works
    pitch_center = start_pitch
    new_center, new_sigma, zheavymodel = zheavy_center(experiment, (-2*sigma_beam, +2*sigma_beam), 31,
                                          sampleposition, zheavymodel, store_location)
    zheavymodel.parameters["sigma"].set(value = new_sigma, vary = False)

    move_motor("zheavy", new_center)
    sampleposition["zheavy"] = new_center
    pitch_delta = pitch_limit(new_sigma, halfsample)
    pitchmodel.parameters["beam_sigma"].set(value = new_sigma, vary = False)
    new_pitch_center, new_beam_offset, pitchmodel = center_pitch(experiment, (-pitch_delta, +pitch_delta), 31,
                                                                 sampleposition, pitchmodel,
                                                                 store_location)
    sampleposition["pitchgi"] = new_pitch_center
    logging.info(f"Moving motor pitchgi to {new_pitch_center}")
    move_motor("pitchgi", new_pitch_center)

    sampleposition["zheavy"] = new_center+new_beam_offset
    logging.info(f"Moving motor zheavy to {new_center} + {new_beam_offset}")
    move_motor("zheavy", new_center+new_beam_offset)
    # with stopping condition but not adaptive number of points 
    while abs(new_center - center) > 0.01 or abs(new_pitch_center - pitch_center) > 0.005:
        center = new_center
        pitch_center = new_pitch_center
        beam_offset = new_beam_offset
        new_center, new_sigma, zheavymodel = zheavy_center(experiment, (-2*sigma_beam, +2*sigma_beam), 31,
                                              sampleposition,  zheavymodel, store_location)
        move_motor("zheavy", new_center)
        sampleposition["zheavy"] = new_center
        #pitchmodel.parameters["beam_sigma"].set(value = new_sigma)
        pitch_delta = pitch_limit(new_sigma, halfsample)
        new_pitch_center, new_beam_offset, pitchmodel = center_pitch(experiment, (-pitch_delta, +pitch_delta), 31,
                                                                     sampleposition, pitchmodel, store_location)
        new_center = new_center+new_beam_offset

        move_motor("pitchgi", new_pitch_center)
        sampleposition["pitchgi"] = new_pitch_center
        move_motor("zheavy", new_center)
        sampleposition["zheavy"] = new_center
        logging.info(f"preliminary horizontal position pitch: {new_pitch_center}°")
        logging.info(f"preliminary sample surface, vertical position: {new_center} mm")
    return new_pitch_center, new_center 
        
    
def roll_align(experiment, y_center, sigma_beam, rolloffset, centerofrotation = 30,
               sampleposition={"ysam.blank": -66}, zheavymodel=tm.ZheavyModel(), store_location=Path(".")):
    y_neg = y_center - rolloffset
    sampleposition["ysam"] = y_neg
    move_motor("ysam", y_neg)
    neg_center, sigma, zheavymodel = zheavy_center(experiment, (-4*sigma_beam, +4*sigma_beam), 31,
                                      sampleposition, zheavymodel, store_location)
    y_pos = y_center + rolloffset
    move_motor("ysam", y_pos)
    sampleposition["ysam"] = y_pos
    pos_center, sigma, zheavymodel = zheavy_center(experiment, (-4*sigma_beam, +4*sigma_beam), 31,
                                      sampleposition, zheavymodel, store_location)
    logging.info("positive edge:", pos_center)
    logging.info("negative edge:", neg_center)
    rollangle = np.rad2deg(np.arctan((pos_center - neg_center)/(2 * rolloffset)))
    print("roll angle:", rollangle)
    if abs(rollangle) > 1:  # something has probably gone wrong
        logging.info(f"Large roll angle identified ({rollangle} deg), reverting to zero.")
        rollangle = 0

    oldroll = epics.caget("mc0:rollgi")
    move_motor("rollgi", oldroll + rollangle) # to do: check sense of roll stage
    move_motor("ysam", y_center)
    sampleposition["ysam"] = y_center
    new_z = np.tan(np.deg2rad(oldroll + rollangle))*(y_center - centerofrotation)
    return oldroll + rollangle, new_z

def main():
    pass

if __name__ == "__main__":
    main()

