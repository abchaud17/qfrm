from qfrm import *

class Chooser(OptionValuation):
    """ Chooser option class.

    Inherits all methods and properties of OptionValuation class.
    """

    def calc_px(self, tau=None, method='BS', nsteps=None, npaths=None, keep_hist=False):
        """ Wrapper function that calls appropriate valuation method.

        User passes parameters to calc_px, which saves them to local PriceSpec object
        and calls specific pricing function (_calc_BS,...).
        This makes significantly less docstrings to write, since user is not interfacing pricing functions,
        but a wrapper function calc_px().

        Parameters
        ----------
        tau : float
                Time to choose whether this option is a call or put.
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
        self : Chooser

        .. sectionauthor:: Oleg Melnikov

        Notes
        -----
        Hull, John C.,Options, Futures and Other Derivatives, 9ed, 2014. Prentice Hall. ISBN 978-0-13-345631-8. http://www-2.rotman.utoronto.ca/~hull/ofod/index.html

        Huang Espen G., Option Pricing Formulas, 2ed. http://down.cenet.org.cn/upfile/10/20083212958160.pdf

        Wee, Lim Tiong, MFE5010 Exotic Options,Notes for Lecture 4 Chooser option. http://www.stat.nus.edu.sg/~stalimtw/MFE5010/PDF/L4chooser.pdf

        Humphreys, Natalia A., ACTS 4302 Principles of Actuarial Models: Financial Economics. Lesson 14: All-or-nothing, Gap, Exchange and Chooser Options.


        Examples
        -------

        >>> s = Stock(S0=42, vol=.20)
        >>> o = European(ref=s, right='put', K=40, T=.5, rf_r=.1, desc='call @0.81, put @4.76, Hull p.339')

        >>> o.calc_px(method='BS').px_spec   # save interim results to self.px_spec. Equivalent to repr(o)
        qfrm.PriceSpec
        d1: 0.7692626281060315
        d2: 0.627841271868722
        keep_hist: false
        method: BS
        px: 0.8085993729000922
        px_call: 4.759422392871532
        px_put: 0.8085993729000922
        sub_method: standard; Hull p.335

        >>> (o.px_spec.px, o.px_spec.d1, o.px_spec.d2, o.px_spec.method)  # alternative attribute access
        (0.8085993729000922, 0.7692626281060315, 0.627841271868722, 'BS')

        >>> o.update(right='call').calc_px().px_spec.px  # change option object to a put
        4.759422392871532

        >>> European(clone=o, K=41, desc='Ex. copy params; new strike.').calc_px(method='LT').px_spec.px
        4.2270039114413125

        >>> s = Stock(S0=810, vol=.2, q=.02)
        >>> o = European(ref=s, right='call', K=800, T=.5, rf_r=.05, desc='53.39, Hull p.291')
        >>> o.calc_px(method='LT', nsteps=3, keep_hist=True).px_spec.px  # option price from a 3-step tree (that's 2 time intervals)
        59.867529937506426

        >>> o.px_spec.ref_tree  # prints reference tree
        ((810.0,),
         (746.4917680871579, 878.9112325795882),
         (687.9629133603595, 810.0, 953.6851293266307),
         (634.0230266330457, 746.491768087158, 878.9112325795882, 1034.8204598880159))

        >>> o.calc_px(method='LT', nsteps=2, keep_hist=True).px_spec.opt_tree
        ((53.39471637496134,),
         (5.062315192620067, 100.66143225703827),
         (0.0, 10.0, 189.3362341097378))

        >>> o.calc_px(method='LT', nsteps=2)
        European
        K: 800
        T: 0.5
        _right: call
        _signCP: 1
        desc: 53.39, Hull p.291
        frf_r: 0
        px_spec: qfrm.PriceSpec
          LT_specs:
            a: 1.0075281954445339
            d: 0.9048374180359595
            df_T: 0.9753099120283326
            df_dt: 0.9875778004938814
            dt: 0.25
            p: 0.5125991278953855
            u: 1.1051709180756477
          method: LT
          px: 53.39471637496135
          sub_method: binomial tree; Hull Ch.13
        ref: qfrm.Stock
          S0: 810
          curr: null
          desc: null
          q: 0.02
          tkr: null
          vol: 0.2
        rf_r: 0.05
        seed0: null

        """
        self.tau = tau
        self.px_spec = PriceSpec(method=method, nsteps=nsteps, npaths=npaths, keep_hist=keep_hist)
        return getattr(self, '_calc_' + method.upper())()

    def _calc_BS(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: European

        .. sectionauthor:: Oleg Melnikov

        """
        from scipy.stats import norm
        from math import sqrt, exp, log

        _ = self
        d2 = (log(_.ref.S0/_.K) + ((_.rf_r - _.ref.q - _.ref.vol**2/2)*_.T) ) / ( _.ref.vol * sqrt(_.T))
        d1 =  d2 + _.ref.vol * sqrt(_.T)

        d2n = (log(_.ref.S0/_.K) + (_.rf_r - _.ref.q ) * _.T - _.ref.vol**2 * _.tau /2) / ( _.ref.vol * sqrt(_.tau))
        d1n = d2n + _.ref.vol * sqrt(_.tau)

        px = _.ref.S0 * exp(-_.ref.q * _.T) * norm.cdf(d1) - _.K* exp(-_.rf_r * _.T ) * norm.cdf(d2) +\
             _.K* exp(-_.rf_r * _.T ) * norm.cdf(-d2n)  - _.ref.S0* exp(-_.ref.q * _.T) * norm.cdf(-d1n)

        self.px_spec.add(px=px, d1=d1, d2=d2)

        return self

    def _calc_LT(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: European

        .. sectionauthor:: thawda

        .. note::
        Implementing Binomial Trees:   http://papers.ssrn.com/sol3/papers.cfm?abstract_id=1341181

        """
        from numpy import cumsum, log, arange, insert, exp, sqrt, sum, maximum

        n = getattr(self.px_spec, 'nsteps', 3)
        _ = self.LT_specs(n)

        S = self.ref.S0 * _['d'] ** arange(n, -1, -1) * _['u'] ** arange(0, n + 1)
        O = maximum(self.signCP * (S - self.K), 0)          # terminal option payouts
        S_tree, O_tree = None, None

        if getattr(self.px_spec, 'keep_hist', False):
            S_tree = (tuple([float(s) for s in S]),)
            O_tree = (tuple([float(o) for o in O]),)

            for i in range(n, 0, -1):
                O = _['df_dt'] * ((1 - _['p']) * O[:i] + ( _['p']) * O[1:])  #prior option prices (@time step=i-1)
                S = _['d'] * S[1:i+1]                   # prior stock prices (@time step=i-1)

                S_tree = (tuple([float(s) for s in S]),) + S_tree
                O_tree = (tuple([float(o) for o in O]),) + O_tree

            out = O_tree[0][0]
        else:
            csl = insert(cumsum(log(arange(n) + 1)), 0, 0)         # logs avoid overflow & truncation
            tmp = csl[n] - csl - csl[::-1] + log(_['p']) * arange(n + 1) + log(1 - _['p']) * arange(n + 1)[::-1]
            out = (_['df_T'] * sum(exp(tmp) * tuple(O)))

        self.px_spec.add(px=float(out), sub_method='binomial tree; Hull Ch.135',
                         LT_specs=_, ref_tree=S_tree, opt_tree=O_tree)

        return self

    def _calc_MC(self, nsteps=3, npaths=4, keep_hist=False):
        """ Internal function for option valuation.

        Returns
        -------
        self: Chooser

        .. sectionauthor::

        Notes
        -----


        """
        return self

    def _calc_FD(self, nsteps=3, npaths=4, keep_hist=False):
        """ Internal function for option valuation.

        Returns
        -------
        self: Chooser

        .. sectionauthor::

        """
        return self












__author__ = 'thawda'
def chooser(S , K , T , vol , rfr = 0.01 , q = 0 , right = "call" , tau = 0):
    """

    :param S: Underlying stock price
    :type S : float
    :param K: Stike price
    :type K : float
    :param T: Time to maturity of call option, measured in years
    :type T : float
    :param vol: Volatility of the underlying stock
    :type vol : float
    :param rfr: Risk free rate
    :type rfr : float

    :param q: Dividend yield of the underlying (CC)
    :type q : float

    :param right: call or put
    :type right : String

    :param tau: Time to maturity of put option, measured in years
    :type tau : float
    :return:

    Reference : Hull, John C.,Options, Futures and Other Derivatives, 9ed, 2014. Prentice Hall. ISBN 978-0-13-345631-8. http://www-2.rotman.utoronto.ca/~hull/ofod/index.html

                Huang Espen G., Option Pricing Formulas, 2ed. http://down.cenet.org.cn/upfile/10/20083212958160.pdf

                Wee, Lim Tiong, MFE5010 Exotic Options,Notes for Lecture 4 Chooser option. http://www.stat.nus.edu.sg/~stalimtw/MFE5010/PDF/L4chooser.pdf

                Humphreys, Natalia A., ACTS 4302 Principles of Actuarial Models: Financial Economics. Lesson 14: All-or-nothing, Gap, Exchange and Chooser Options.
    """
    try:
        right   =   right.lower()
        S       =   float(S)
        K       =   float(K)
        T       =   float(T)
        vol     =   float(vol)
        rfr       =   float(rfr)
        q       =   float(q)
        tau    = float(tau)

    except:
        print('Right has to be string and everything else will be treated as float')
        return False

    assert right in ['call','put'], 'Make sure the right to be the "call" or "put" '
    assert vol > 0, 'Vol must be >=0'
    assert K > 0, 'K must be > 0'
    assert T > 0, 'T must be > 0'
    assert S >= 0, 'S must be >= 0'
    assert rfr >= 0, 'rfr must be >= 0'
    assert q >= 0, 'q must be >= 0'
    from numpy import sqrt , log, exp
    from scipy.stats import norm
    d2 = (log(S/K) + ((rfr - q - vol**2/2)*T) ) / ( vol * sqrt(T))
    d1 =  d2 + vol * sqrt( T)

    d2n = (log(S/K) + (rfr - q ) * T - vol**2 * tau /2) / ( vol * sqrt(tau))
    d1n = d2n + vol * sqrt(tau)

    price = S * exp(-q * T) * norm.cdf(d1) - K* exp(-rfr * T ) * norm.cdf(d2) + K* exp(-rfr * T ) * norm.cdf(-d2n)  - S* exp(-q * T) * norm.cdf(-d1n)
    return(price)
