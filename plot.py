# -*- coding: utf-8 -*-
#from matplotlib import rc
#rc('text', usetex=True)
import matplotlib.pyplot as p
import scipy
from scipy.special import gamma
import scipy.io
import scipy.optimize as o

stuff = scipy.io.loadmat('spacings.mat')
stop_idxs = stuff['stop_idxs'].transpose()
all_gaps = stuff['spacings'].transpose()

hist_max = (int(max(all_gaps/10))+1)*10
for this_stop in range(int(stop_idxs[-1])):
    gaps = all_gaps[stop_idxs == this_stop]
    
    xdata = scipy.arange(0, hist_max, 2)
    ydata, _ = scipy.histogram(gaps, xdata, density=True)

    fig = p.figure()
    ax = fig.add_subplot(111)
    ax.hist(gaps, xdata, normed = 1)
    #ax.bar(xdata, ydata)
    ax.set_xlabel('Gap time (min.)')
    ax.set_ylabel('Probability density (1/min.)')
    avg_gap = scipy.mean(gaps)
    avg_gap_err = scipy.sqrt(scipy.var(gaps)/(len(gaps)-1))
    print 'The average arrival time is %.2f +/- %.2f min.' % (avg_gap, avg_gap_err)
    p.axvline(avg_gap, linewidth=4, color='k', linestyle=':')
    
    t=scipy.arange(0, hist_max, hist_max/1024.0)
    
    #Wigner surmise
    P=lambda beta, s, avg_gap: 2.0/avg_gap * (s/avg_gap)**beta \
            * gamma(1 + beta/2)**(1 + beta) * gamma((1 + beta)/2) ** -(2 + beta) \
            * scipy.exp(-(s/avg_gap * gamma(1+beta/2) / gamma((1+beta)/2))**2)
    
    #Poisson
    Q=lambda s, avg_gap: 1/avg_gap * scipy.exp(- s/avg_gap)
    
    #Mix
    Mix = lambda s, mix, beta, mu1, mu2: mix*Q(s, mu1) + (1-mix)*P(beta, s, mu2)
   
    popt, pcov = o.curve_fit(Mix, xdata[1:]-1, ydata, (0.15, 2, avg_gap/5, avg_gap))
    perr = scipy.sqrt(scipy.diag(pcov))
    p.xlim([0, hist_max])
    ax.set_autoscalex_on(False)
    p.ylim([0, 0.12])
    ax.set_autoscaley_on(False)
    p.plot(t, [popt[0]*Q(x, popt[2]) for x in t], linewidth=4, color='r')
    p.plot(t, [(1-popt[0])*P(popt[1], x, popt[3]) for x in t], linewidth=4, color='g')
    
    p.plot(t, [Mix(x, *popt) for x in t], linewidth=4, color='k')
    title = u'Bus gap times'
    title += u'\n (N=%d, ' % len(gaps)
    title += u'c=%.3f ± %.3f, ' % (popt[0], perr[0])
    title += u'b=%.3f ± %.3f, \n' % (popt[1], perr[1])
    title += u'm1=%.3f ± %.3f, ' % (popt[2], perr[2])
    title += u'm2=%.3f ± %.3f)' % (popt[3], perr[3])
    ax.set_title(title)
    
    p.show(block = False)
    fig.savefig('bus-stop-%d.png' % this_stop)

