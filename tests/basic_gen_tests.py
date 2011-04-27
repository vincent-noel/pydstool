from PyDSTool import *

print "Basic generator tests..."

# Test: InterpolateTable
xnames = ['x1', 'x2']
timeData = array([0.1, 1.1, 2.1])
x1data = array([10.2, -1.4, 4.1])
x2data = array([0.1, 0.01, 0.4])
xData = makeDataDict(xnames, [x1data, x2data])
itableArgs = {}
itableArgs['tdata'] = timeData
itableArgs['ics'] = xData
itableArgs['name'] = 'interp'
interptable = InterpolateTable(itableArgs)
itabletraj = interptable.compute('itable')
# print "itabletraj(0.4, 'x1') = ", itabletraj(0.4, 'x1')
# print "                         (x1 should be 6.72)"
# print "itabletraj(1.1) = ", itabletraj(1.1)

# Test: LookupTable
ltableArgs = copy(itableArgs)
ltableArgs['name'] = 'lookup'
lookuptable = LookupTable(ltableArgs)
ltabletraj = lookuptable.compute('ltable')
# print "ltabletraj(1.1) = ", ltabletraj(1.1)
# print "             (x2 should be 0.01)\n"
# print "ltabletraj(0.4) ="
try:
    ltabletraj(0.4)
except ValueError, e:
    pass
    # print "... ltabletraj(0.4) did not succeed because ", e
    # print "(0.4 is not in the tdata array)"
else:
    raise AssertionError

# Test: ODE system

fvarspecs = {"w": "k*w + a*itable + sin(t) + myauxfn1(t)*myauxfn2(w)",
           'aux_wdouble': 'w*2 + globalindepvar(t)',
           'aux_other': 'myauxfn1(2*t) + initcond(w)'}
fnspecs = {'myauxfn1': (['t'], '2.5*cos(3*t)'),
             'myauxfn2': (['w'], 'w/2')}
DSargs = {'tdomain': [0.1,2.1],
          'pars': {'k':2, 'a':-0.5},
          'inputs': {'itable' : interptable.variables['x1']},
          'auxvars': ['aux_wdouble', 'aux_other'],
          'algparams': {'init_step':0.01, 'strict':False},
          'checklevel': 2,
          'name': 'ODEtest',
          'fnspecs': fnspecs,
          'varspecs': fvarspecs
          }
testODE = Vode_ODEsystem(DSargs)
# print "params set => ", testODE.pars
# print "DS defined? => ", testODE.defined
# print "testODE.set(...)"
testODE.set(ics={'w':3.0},
                tdata=[0.11,2.1])
# print "testtraj = testODE.compute('test1')"
testtraj = testODE.compute('test1')
# print "DS defined now? => ", testODE.defined
# print "testtraj(0.5) => ", testtraj(0.5)
# print "testODE.diagnostics.showWarnings() => "
# print testODE.diagnostics.showWarnings()
# print "\ntestODE.indepvariable.depdomain => ", testODE.indepvariable.depdomain
# print "testtraj(0.2, 'aux_other') => ", \
#    testtraj(0.2, 'aux_other')

# Now adding a terminating co-ordinate threshold event...
ev_args = {'name': 'threshold',
           'eventtol': 1e-4,
           'eventdelay': 1e-5,
           'starttime': 0,
           'active': True,  # = default
           'term': True,
           'precise': True  # = default
           }
thresh_ev = Events.makePythonStateZeroCrossEvent('w', 20, 1, ev_args)
testODE.eventstruct.add(thresh_ev)
# print "Recomputing trajectory:"
# print "traj2 = testODE.compute('test2')"
traj2 = testODE.compute('test2')
# print "\ntestODE.diagnostics.showWarnings() => "
# print testODE.diagnostics.showWarnings()
# print "\ntestODE.indepvariable.depdomain => ", testODE.indepvariable.depdomain


# Test: Explicit functional trajectory
# Explicit functional trajectory 'sin_gen' computes sin(t*speed)

# Make 'xdomain' argument smaller than known limits for sine wave: [-1.001, 0.7]
ef_args = {'tdomain': [-50, 50],
        'pars': {'speed': 1},
        'xdomain': {'s': [-1., 0.7]},
        'name': 'sine',
        'globalt0': 0.4,
        'pdomain': {'speed': [0, 200]},
        'varspecs': {'s': "sin(globalindepvar(t)*speed)"}}
sin_gen = ExplicitFnGen(ef_args)
sintraj = sin_gen.compute('sinewave')
assert sintraj(0.0, checklevel=2)['s'] - 0.38941834 < 1e-7

try:
    sintraj(0.8, checklevel=2)
except PyDSTool_BoundsError, e:
    pass
    # print "... correctly raised error: ", e
else:
    raise AssertionError
# print "Set limits properly now, to [-1., 1.] ..."
# print "sin_gen.set({'xdomain': {'s': [-1., 1.]}})"
sin_gen.set(xdomain={'s': [-1., 1.]})
sintraj2 = sin_gen.compute('sinewave2')
# this doesn't raise an exception now
sintraj2(0.8, checklevel=2)

# Test if, min, max, & for macro
fnspecs = {'testif': (['x'], 'if(x<0.0,0.0,x)'),
          'testmin': (['x', 'y'], 'min(x,y)'),
          'testmax': (['x', 'y'], 'max(x,y)'),
          'testmin2': (['x', 'y'], '1/(2+min(1+(x*3),y))+y')
          }

DSargs = args(name='test',
              varspecs={'z[i]': 'for(i, 0, 1, 2*z[i+1])',
                   'z2': '-z0'},
              fnspecs=fnspecs
              )
tmm = Generator.Vode_ODEsystem(DSargs)

# test user interface to aux functions

assert tmm.auxfns.testif(1.0) == 1.0
assert tmm.auxfns.testmin(1.0, 2.0) == 1.0
assert tmm.auxfns.testmax(1.0, 2.0) == 2.0
assert tmm.auxfns.testmin2(1.0, 2.0) == 2.25

print "  ...passed"