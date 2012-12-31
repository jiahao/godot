import matplotlib.pyplot as p
import scipy
from scipy.special import gamma
import scipy.io

stuff = scipy.io.loadmat('data.mat')
gaps = stuff['gaps'].transpose()

fig = p.figure()
ax = fig.add_subplot(111)
ax.hist(gaps, 60, normed=True)
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
p.plot(t, [P(0.1, x, avg_gap) for x in t], linewidth=4, color='g')
p.plot(t, [P(0.3, x, avg_gap) for x in t], linewidth=4, color='g')
p.plot(t, [P(0.5, x, avg_gap) for x in t], linewidth=4, color='g')
p.plot(t, [P(1, x, avg_gap) for x in t], linewidth=4, color='g')
#p.plot(t, [P(2, x, avg_gap) for x in t], linewidth=4, color='g')
p.plot(t, [Q(x, avg_gap) for x in t], linewidth=4, color='r')
p.show()

