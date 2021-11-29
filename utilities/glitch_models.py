import numpy as np
from gwpy.timeseries import TimeSeries

def white_noise(times_array):
    l_=len(times_array)
    h0 = np.random.uniform(1e-21, 5e-21)
    s = np.random.normal(0, 1, l_)
    return s*h0

def scatlight_model(times_array, t0, tau, f0, snr):
    h0 = 1e-22*snr
    phi =2.* np.pi * f0*np.abs(times_array-t0)*(1.-0.5*(times_array-t0)**2.)
    return h0*np.sin(phi)*np.exp(-(times_array-t0)**2/(2*tau))
    
def singauss_model(times_array, t0, tau, f0, snr):
    h0 = 1e-22*snr
    block0 =  np.exp(-((times_array - t0) ** 2) / (2 * tau ** 2))
    block1 = h0*np.sin(2 * np.pi * f0 * (times_array - t0)) * block0
    return block1   

if __name__=='__main__':
    times_ = np.linspace(0, 120, 4096*120)
    data = scatlight_model(times_, 60., 0.23, 62., 20.)
    data += white_noise(times_)
    timeseries_data = TimeSeries(data, 
                                 sample_rate = 4096, 
                                 t0 = times_[0])
    q_data = timeseries_data.q_transform(qrange=(8, 22), 
                                frange=(10, 500), logf=True,             
                                gps=60., whiten=True,   
                                outseg=(60 - 1, 60 + 1))
    plot = q_data.plot(figsize=[8, 4])
    ax = plot.gca()
    ax.set_xscale('seconds')
    ax.set_yscale('log')
    ax.set_ylim(20, 500)
    ax.set_ylabel('Frequency [Hz]')
    ax.grid(True, axis='y', which='both')
    ax.colorbar(cmap='viridis', label='Normalized energy')
    plot.show() 
    
