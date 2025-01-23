import numpy as np
from scipy.special import erf
import lmfit as lm
from attrs import define, field

def pitchgi_model(x, x0, length, ampl, beam_center, beam_sigma):
    return ampl * (1 -
                   0.5*(erf((length * np.abs(np.sin((x-x0)*np.pi/180.))
                             - beam_center)/beam_sigma)
                        + 1
                        )
                   )


@define
class PitchModel:
    model = field(default = lm.Model(pitchgi_model))
    samplelength = field(default = 15)
    parameters = field(init = False)

    def __attrs_post_init__(self):
        self.parameters = pitch_model.make_params(x0=dict(value = 0, min = -1, max = 1),
                                                  length=dict(value = self.samplelength, vary = False),
                                                  ampl=dict(value = 1.0, vary = False),
                                                  beam_center=dict(value = 0.0, min = -0.1, max = 0.1),
                                                  beam_sigma=dict(value = 0.1, min = 0.01, max = 0.5, vary = False)
                                                  )
    

pitch_model = lm.Model(pitchgi_model)
pitch_params = pitch_model.make_params()
pitch_params["x0"].set(value = -0.7, min = -1, max = 1)
pitch_params["length"].set(value = 15, min = 0, max = 30, vary = False)
pitch_params["ampl"].set(value = 1, min = 0, max = 1, vary = False)
pitch_params["beam_center"].set(value = 0, min = -2, max = 2)
pitch_params["beam_sigma"].set(value = 0.1, min = 0.01, max = 2)


@define
class ZheavyModel:
    model = field(default = lm.models.StepModel(form = "erf") + lm.models.LinearModel())
    parameters = field(init = False)
    sigma = field(default = 0.1)
    center = field(default = 4.5)

    def __attrs_post_init__(self):
        self.parameters = self.model.make_params(center=dict(value = self.center, min = 3, max = 5),
                                                 amplitude=dict(value = -1, min = -1, max = 0),
                                                 intercept=dict(value = 1, min = 0, max = 1, expr = "-amplitude"),
                                                 sigma=dict(value = self.sigma, min = 0.05, max = 1),
                                                 slope=dict(value = 0, vary = False)
                                                 )
    


z_model = lm.models.StepModel(form = "erf") + lm.models.LinearModel()
z_params = z_model.make_params()
z_params["center"].set(value = 4.5, min = 0, max = 10)
z_params["amplitude"].set(value = -1, min = -1, max = 0)
z_params["sigma"].set(value = 0.1, min = 0, max = 2)
z_params["slope"].set(value = 0, vary = False)
z_params["intercept"].set(value = 1, min = 0, max = 1, expr = "-amplitude")

gap_model = lm.models.RectangleModel(form = "erf") + lm.models.LinearModel()
gap_params = gap_model.make_params()
gap_params["amplitude"].set(value = 1, min = -1, max = 1)
gap_params["center1"].set(value = 1)
gap_params["center2"].set(value = 4)
gap_params["sigma1"].set(value = 0.1, min = 0)
gap_params["sigma2"].set(expr = "sigma1")
gap_params["slope"].set(value = 0, vary = False)
gap_params["intercept"].set(value = 1, min = 0, max = 1, expr = "-amplitude if amplitude < 0 else 0")
