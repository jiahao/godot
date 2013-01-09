import matplotlib.pyplot as p
import scipy
from scipy.special import gamma
import scipy.io

stuff = scipy.io.loadmat('spacings.mat')
stop_idxs = stuff['stop_idxs'].transpose()
gaps = stuff['spacings'].transpose()

gaps = gaps[stop_idxs == 0]
fig = p.figure()
ax = fig.add_subplot(111)
ax.hist(gaps, (int(max(gaps/10))+1)*10, normed=True)
ax.set_title('Bus gap times (N=%d)' % len(gaps))
ax.set_xlabel('Gap time (min.)')
ax.set_ylabel('Probability density (1/min.)')
avg_gap = scipy.mean(gaps)
avg_gap_err = scipy.sqrt(scipy.var(gaps)/(len(gaps)-1))
print 'The average arrival time is %.2f +/- %.2f min.' % (avg_gap, avg_gap_err)
p.axvline(avg_gap, linewidth=4, color='k', linestyle=':')

t=scipy.arange(0, 50, 0.03)

#Wigner surmise
P=lambda beta, s, avg_gap: 2.0/avg_gap * (s/avg_gap)**beta \
        * gamma(1 + beta/2)**(1 + beta) * gamma((1 + beta)/2) ** -(2 + beta) \
        * scipy.exp(-(s/avg_gap * gamma(1+beta/2) / gamma((1+beta)/2))**2)

#Poisson
Q=lambda s, avg_gap: 1/avg_gap * scipy.exp(- s/avg_gap)


#Mix
mix=0.15
beta=2
poisson_mean = avg_gap/6
wigner_mean = avg_gap

p.plot(t, [mix*Q(x, poisson_mean) for x in t], linewidth=4, color='r')
p.plot(t, [(1-mix)*P(beta, x, wigner_mean) for x in t], linewidth=4, color='g')

p.plot(t, [mix*Q(x, poisson_mean) + (1-mix)*P(beta, x, wigner_mean) for x in t], linewidth=4, color='k')

p.show()

