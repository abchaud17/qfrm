from scipy import stats
import warnings
import numpy as np
import math
from OptionValuation import *

class Shout(OptionValuation):
    """ Shout option class.

    Inherits all methods and properties of OptionValuation class.
    """

    def __init__(self,q=0.0,*args,**kwargs):


        super().__init__(*args,**kwargs)
        self.q = q


    def calc_px(self, method='LT', nsteps=None, npaths=None, keep_hist=False):
        """ Wrapper function that calls appropriate valuation method.

        User passes parameters to calc_px, which saves them to local PriceSpec object
        and calls specific pricing function (_calc_BS,...).
        This makes significantly less docstrings to write, since user is not interfacing pricing functions,
        but a wrapper function calc_px().

        Parameters
        ----------
        method : str
                Required. Indicates a valuation method to be used: 'BS', 'LT', 'MC', 'FD'
        nsteps : int
                LT, MC, FD methods require number of times steps
        npaths : int
                MC, FD methods require number of simulation paths
        keep_hist : bool
                If True, historical information (trees, simulations, grid) are saved in self.px_spec object.


        Returns
        -------
        self : Shout

        .. sectionauthor:: Mengyan Xie

        Notes
        -----
        Verification of Shout option: http://www.stat.nus.edu.sg/~stalimtw/MFE5010/PDF/L4shout.pdf
        Hull Ch26.12 P609

        -------
        Examples

        This two excel spreadsheet price shout option.
        http://investexcel.net/shout-options-excel/
        https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=9&cad=rja&uact=8&ved=0ahUKEwjMsfu4n6TJAhVJz2MKHQA_B-MQFghSMAg&url=http%3A%2F%2Fwww.actuarialworkshop.com%2FBinomial%2520Tree.xls&usg=AFQjCNEic5d4DfV5BTKbzkPW2LhzBU0Fdw&sig2=lB14d9wQBxsiqdaXlqTBTw&bvm=bv.108194040,d.eWE


        >>> s = Stock(S0=50, vol=.3)
        >>> o = Shout(ref=s, right='call', K=52, T=2, rf_r=.05, desc='Example from internet')

        >>> o.calc_px(method='LT', nsteps=2, keep_hist=True).px_spec.px
        11.803171356649463

        >>> o.px_spec.ref_tree
        ((50.000000000000014,), (37.0409110340859, 67.49294037880017), (27.440581804701324, 50.00000000000001, 91.10594001952546))

        >>> o.calc_px(method='LT', nsteps=2, keep_hist=False)
        Shout.Shout
        K: 52
        T: 2
        _right: call
        _signCP: 1
        desc: Example from internet
        frf_r: 0
        px_spec: PriceSpec
          LT_specs:
            a: 1.0512710963760241
            d: 0.7408182206817179
            df_T: 0.9048374180359595
            df_dt: 0.951229424500714
            dt: 1.0
            p: 0.5097408651817704
            u: 1.3498588075760032
          keep_hist: false
          method: LT
          nsteps: 2
          px: 11.803171356649463
          sub_method: binomial tree; Hull Ch.13
        q: 0.0
        ref: Stock
          S0: 50
          curr: -
          desc: -
          q: 0
          tkr: -
          vol: 0.3
        rf_r: 0.05
        seed0: -
        <BLANKLINE>



        >>> from pandas import Series;  steps = range(1,11)
        >>> O = Series([o.calc_px(method='LT', nsteps=s).px_spec.px for s in steps], steps)
        >>> O.plot(grid=1, title='LT Price vs nsteps')
        <matplotlib.axes._subplots.AxesSubplot object at ...>
        >>> import matplotlib.pyplot as plt
        >>> plt.show()

       """

        return super().calc_px(method=method, nsteps=nsteps, npaths=npaths, keep_hist=keep_hist)


    def _calc_LT(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Shout

        .. sectionauthor:: Mengyan Xie

        Notes
        -----

        The shout option is usually a call option, but with a difference: at any time t before maturity, the holder may
        "shout". The effect of this is that he is guaranteed a minimum payoff of St - K, although he will get the payoff
        of the call option if this is greater than the minimum. In spirit this is the same as the binomial method for
        pricing American options.



        """
        from numpy import arange, maximum, log, exp, sqrt

        keep_hist = getattr(self.px_spec, 'keep_hist', False)
        n = getattr(self.px_spec, 'nsteps', 3)
        _ = self.LT_specs(n)

        S = self.ref.S0 * _['d'] ** arange(n, -1, -1) * _['u'] ** arange(0, n + 1)  # terminal stock prices
        O = maximum(self.signCP * (S - self.K), 0)          # terminal option payouts

        S_tree = (tuple([float(s) for s in S]),)  # use tuples of floats (instead of numpy.float)
        O_tree = (tuple([float(o) for o in O]),)

        for i in range(n, 0, -1):
            left = n - i + 1
            tleft = left * _['dt']
            d1 = (0 + (self.rf_r + self.ref.vol ** 2 / 2) * tleft) / (self.ref.vol * math.sqrt(tleft))
            d2 = d1 - self.ref.vol * math.sqrt(tleft)

            O = _['df_dt'] * ((1 - _['p']) * O[:i] + ( _['p']) * O[1:])  #prior option prices (@time step=i-1)
            S = _['d'] * S[1:i+1]                   # prior stock prices (@time step=i-1)
            Shout = self.signCP * S / math.exp(self.ref.q * tleft) * stats.norm.cdf(self.signCP * d1) - \
                    self.signCP * S / math.exp(self.rf_r * tleft) * stats.norm.cdf(self.signCP * d2) + \
                    self.signCP * (S - self.K) / math.exp(self.rf_r * tleft)

            Payout = maximum(Shout, 0)
            O = maximum(O, Payout)

            S_tree = (tuple([float(s) for s in S]),) + S_tree
            O_tree = (tuple([float(o) for o in O]),) + O_tree

            out = O_tree[0][0]

        self.px_spec.add(px=float(Util.demote(O)), method='LT', sub_method='binomial tree; Hull Ch.13',
                        LT_specs=_, ref_tree = S_tree if keep_hist else None, opt_tree = O_tree if keep_hist else None)

        #self.px_spec.add(px=float(out), sub_method='binomial tree; Hull Ch.26.12',
        #                 LT_specs=_, ref_tree=S_tree, opt_tree=O_tree)

        return self

    def _calc_BS(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Shout

        .. sectionauthor::

        Note
        ----

        """

        return self

    def _calc_MC(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Shout

        .. sectionauthor::

        Note
        ----

        """
        return self

    def _calc_FD(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Shout

        .. sectionauthor::

        Note
        ----

        """

        return self
