import matplotlib.pyplot as plt
import numpy as np

from qfrm.pricespec import PriceSpec

try:
    from qfrm.OptionValuation import *  # production:  if qfrm package is installed
except:
    from qfrm.option import *  # development: if not installed and running from source


class Bermudan(OptionValuation):
    """ Bermudan option class.

    Inherits all methods and properties of OptionValuation class.
    The Bermudan option is a modified American with restricted early-exercise dates. Due to this restriction,
    Bermudans are named as such as they are "between" American and European options in exercisability, and as
    this module demonstrates, in price.
    """

    def calc_px(self, method='LT', tex=(.12, .24, .46, .9, .91, .92, .93, .94, .95, .96, .97, .98, .99, 1.),
                nsteps=None, npaths=None, keep_hist=False, R=3, seed=4294967295):
        """ Wrapper function that calls appropriate valuation method.

        All parameters of ``calc_px`` are saved to local ``px_spec`` variable of class ``PriceSpec`` before
        specific pricing method (``_calc_BS()``,...) is called.
        An alternative to price calculation method ``.calc_px(method='BS',...).px_spec.px``
        is calculating price via a shorter method wrapper ``.pxBS(...)``.
        The same works for all methods (BS, LT, MC, FD).

        Parameters
        ----------
        method : str
                Required. Indicates a valuation method to be used:
                ``BS``: Black-Scholes Merton calculation
                ``LT``: Lattice tree (such as binary tree)
                ``MC``: Monte Carlo simulation methods
                ``FD``: finite differencing methods
        tex : list
                Required. Must be a vector (tuple; list; array, ...) of times to exercisability. 
                For Bermudan, assume that exercisability is for discrete tex times only.
                This also needs to be sorted ascending and the final value is the corresponding vanilla maturity.
                If T is not equal the the final value of tex, then
                    the T will take precedence: if T < max(tex) then tex will be truncated to tex[tex < T] and will be 
                    appended to tex.
                    If T > max(tex) then the largest value of tex will be replaced with T.
        nsteps : int
                FD methods require number of times steps.
                Optional if using LT: n_steps = <integer> * <length of tex>. Will fill in the spaces between steps 
                implied by tex.
                Useful if tex is regular or sparse to improve accuracy. Otherwise leave as None.
                Currently unused in MC. MC simply uses tex intervals as steps.
        npaths : int
                MC, FD methods require number of simulation paths
        keep_hist : bool
                If True, historical information (trees, simulations, grid) are saved in self.px_spec object.
        R : int
                Number of basis functions. Used to generate weighted Laguerre polynomial values.
                Used in MC method. Must be between 0 and 6.
        seed : int
                The seed for the RNG.

        Returns
        -------
        self : Bermudan


        Notes
        -----

        **LT Notes**

        Referenced example is from p.9 of
        `Bermudan Option Pricing using Binomial Models Seminar in Analytical Finance I
        <http://janroman.dhis.org/stud/I2012/Bermuda/reportFinal.pdf>`_

        References
        ----------
        [1] http://eprints.maths.ox.ac.uk/789/1/Thom.pdf
        [2] http://eprints.maths.ox.ac.uk/934/1/longyun_chen.pdf

        Examples
        --------

       **LT Examples**

        LT pricing of Bermudan options

        >>> s = Stock(S0=50, vol=.3)
        >>> o = Bermudan(ref=s, right='put', K=52, T=2, rf_r=.05)
        >>> o.pxLT(keep_hist=True)
        7.251410364

        Changing the maturity

        >>> o = Bermudan(ref=s, right='put', K=52, T=1, rf_r=.05)
        >>> o.pxLT(keep_hist=True)
        5.916826966

        >>> o = Bermudan(ref=s, right='put', K=52, T=.5, rf_r=.05)
        >>> o.pxLT(keep_hist=True)
        4.705110749

        Explicit input of exercise schedule

        >>> np.random.seed(12345678)
        >>> rlist = np.random.normal(1,1,20)
        >>> times = tuple(map(lambda i: float(str(round(abs(rlist[i]),2))), range(20)))
        >>> o = Bermudan(ref=s, right='put', K=52, T=1., rf_r=.05)
        >>> o.pxLT(tex=times, keep_hist=True)
        5.824649677

        Example from outside reference

        >>> times = (3/12,6/12,9/12,12/12,15/12,18/12,21/12,24/12)
        >>> o = Bermudan(ref=Stock(50, vol=.6), right='put', K=52, T=2, rf_r=0.1)
        >>> o.pxLT(tex=times, nsteps=40, keep_hist=False)
        13.206509996

        Price vs. strike curve - example of vectorization of price calculation

        >>> Karr = np.linspace(30,70,101)
        >>> px = tuple(map(lambda i:  Bermudan(ref=Stock(50, vol=.6), right='put', K=Karr[i], T=2, rf_r=0.1).
        ... pxLT(tex=times, nsteps=20), range(Karr.shape[0])))
        >>> fig = plt.figure()
        >>> ax = fig.add_subplot(111)
        >>> ax.plot(Karr,px,label='Bermudan put') # doctest: +ELLIPSIS
        [<...>]
        >>> ax.set_title('Price of Bermudan put vs K') # doctest: +ELLIPSIS
        <...>
        >>> ax.set_ylabel('Px') # doctest: +ELLIPSIS
        <...>
        >>> ax.set_xlabel('K') # doctest: +ELLIPSIS
        <...>
        >>> ax.grid()
        >>> ax.legend() # doctest: +ELLIPSIS
        <...>
        >>> plt.show()


        **MC Examples**

        Example #1

        >>> s = Stock(S0=1200, vol=.25, q=0.015)
        >>> T = 1; tex = np.arange(0.1, T + 0.1, 0.1)
        >>> o = Bermudan(ref=s, right='call', K=1200, T=T, rf_r=.03, frf_r=0.05)
        >>> o.pxMC(R=2, npaths=5, tex=tex)
        31.682017621

        Example #2 (verifiable): See reference [1], section 5.1 and table 5.1 with arguments N=10^2, R=3
        Uncomment to run (number of paths required is too high for doctests)

        # >>> s = Stock(S0=11, vol=.4)
        # >>> T = 1; tex = np.arange(0.1, T + 0.1, 0.1)
        # >>> o = Bermudan(ref=s, right='put', K=15, T=T, rf_r=.05, desc="in-the-money Bermudan put")
        # >>> actual = o.pxMC(R=3, npaths=10**2, tex=tex); expected = 4.200888
        # >>> actual
        # 4.0403015590000004
        # >>> (abs(actual - expected) / expected) < 0.10  # Verify within 10% of expected
        # True

        Example #3 (verifiable): See reference [1], section 5.1 and table 5.1 with arguments N=10^5, R=6
        Uncomment to run (number of paths required is too high for doctests)

        # >>> s = Stock(S0=11, vol=.4)
        # >>> T = 1; tex = np.arange(0.1, T + 0.1, 0.1)
        # >>> o = Bermudan(ref=s, right='put', K=15, T=T, rf_r=.05, desc="in-the-money Bermudan put")
        # >>> actual = o.pxMC(R=6, npaths=10**5, tex=tex); expected = 4.204823
        # >>> actual
        # 3.9492928389999999
        # >>> (abs(actual - expected) / expected) < 0.10  # Verify within 10% of expected
        # True

        Example #4 (plot)

        >>> s = Stock(S0=11, vol=.4)
        >>> T = 1; tex = np.arange(0.1, T + 0.1, 0.1)
        >>> o = Bermudan(ref=s, right='put', K=15, T=T, rf_r=.01)
        >>> o.pxMC(R=3, npaths=10, tex=tex, keep_hist=True)
        4.016206951
        >>> o.plot_MC()

        :Authors:
            Oleg Melkinov
            Andy Liao <Andy.Liao@rice.edu>
            Patrick Granahan
        """

        # Seed the RNG
        np.random.seed(seed)

        T = max(tex)
        deltaT = self.T - T
        epsilon = 10 ** (-11)

        if deltaT < epsilon:
            tex = tuple(np.asarray(tex)[np.asarray(tex) < self.T]) + (self.T,)
        elif deltaT > epsilon:
            tex = tex[:-1] + (self.T,)

        self.tex = tex
        knsteps = max(tuple(map(lambda i: int(T / (tex[i + 1] - tex[i])), range(len(tex) - 1))))
        if nsteps != None:
            knsteps = knsteps * nsteps
        nsteps = knsteps
        self.px_spec = PriceSpec(method=method, nsteps=nsteps, npaths=npaths, keep_hist=keep_hist, R=R, seed=seed)
        return getattr(self, '_calc_' + method.upper())()

    def _calc_LT(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Bermudan

        :Authors:
            Oleg Melnikov
            Andy Liao <Andy.Liao@rice.edu>

        """

        keep_hist = getattr(self.px_spec, 'keep_hist', False)
        n = getattr(self.px_spec, 'nsteps', 3)
        _ = self.LT_specs(n)

        #Redo tree steps

        S = self.ref.S0 * _['d'] ** np.arange(n, -1, -1) * _['u'] ** np.arange(0, n + 1)  # terminal stock prices
        O = np.maximum(self.signCP * (S - self.K), 0)          # terminal option payouts
        # tree = ((S, O),)
        S_tree = (tuple([float(s) for s in S]),)  # use tuples of floats (instead of numpy.float)
        O_tree = (tuple([float(o) for o in O]),)
        # tree = ([float(s) for s in S], [float(o) for o in O],)

        for i in range(n, 0, -1):
            O = _['df_dt'] * ((1 - _['p']) * O[:i] + ( _['p']) * O[1:])  #prior option prices
            #(@time step=i-1)
            S = _['d'] * S[1:i+1]                   # prior stock prices (@time step=i-1)
            Payout = np.maximum(self.signCP * (S - self.K), 0)   # payout at time step i-1 (moving backward in time)
            if i*_['dt'] in self.tex:   #The Bermudan condition: exercise only at scheduled times
                O = np.maximum(O, Payout)
            # tree = tree + ((S, O),)
            S_tree = (tuple([float(s) for s in S]),) + S_tree
            O_tree = (tuple([float(o) for o in O]),) + O_tree
            # tree = tree + ([float(s) for s in S], [float(o) for o in O],)

        self.px_spec.add(px=float(Util.demote(O)), method='LT', sub_method='binomial tree; Hull Ch.13',
                        LT_specs=_, ref_tree = S_tree if keep_hist else None, opt_tree = O_tree if keep_hist else None)

        # self.px_spec = PriceSpec(px=float(Util.demote(O)), method='LT', sub_method='binomial tree; Hull Ch.13',
        #                 LT_specs=_, ref_tree = S_tree if save_tree else None, opt_tree = O_tree if save_tree 
        #else None)
        return self

    def _calc_BS(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Bermudan

        .. sectionauthor:: 

        Note
        ----

        """
        return self

    def _calc_MC(self):
        """ Internal function for option valuation.

        See calc_px() for full documentation.

        Returns
        -------
        self: Bermudan

        :Authors:
            Patrick Granahan
        """

        # Get arguments from calc_px
        npaths = getattr(self.px_spec, 'npaths')
        R = getattr(self.px_spec, 'R')

        def payout(stock_price):
            """
            Calculates the payout of a Bermudan option at a given stock_price.

            Parameters
            ----------
            stock_price : numpy.matrix
                A vector of stock prices

            Returns
            -------
            payout : numpy.matrix
                    The vector of payouts.
            """
            payout = np.maximum(self.signCP * (stock_price - self.K), 0)
            return payout

        def delta_T_array():
            """
            Creates an array of time differences.

            Returns
            -------
            delta_Ts : numpy.array
                The array of time differences.
            """
            # Create an array of time differences
            delta_Ts = np.zeros((len(self.tex)))

            # Calculate the time difference between the next exercise date and the current exercise date
            for tex_index in range(len(self.tex)):
                previous_tex = 0 if tex_index == 0 else self.tex[tex_index - 1]
                delta_Ts[tex_index] = self.tex[tex_index] - previous_tex

            return delta_Ts

        def generate_stock_price_paths(delta_Ts):
            """
            Generates a matrix (dimensions npaths * (tex + 1)) of stock price stock_price_paths.
            Each row represents a path, with each column representing a snapshot of each path at a given tex.
            An extra column is included to accomodate the start date.

            An item at matrix[x][y] gets the stock price on the xth path at exercise date y.

            Notes
            -----
            See http://nakamuraseminars.org/nsblog/2014/06/21/monte-carlo-in-python-an-example/ for more discussion
            on how this method can be further optimized.

            Parameters
            ----------
            delta_Ts : numpy.array
                    An array of time differences.

            Returns
            -------
            stock_price_paths : numpy.matrix
                    Matrix of stock_price_paths generated.
            """
            # Create the zero matrix of stock_price_paths
            paths = np.zeros((npaths, len(self.tex) + 1))

            # Seed the first column with the start prices
            paths[:, 0] = self.ref.S0

            # Fill the matrix, looping over time only
            for tex_index in range(len(self.tex)):
                # Generate an array of uniform random samples, npaths in length
                random_samples = np.random.normal(loc=0.0, scale=1.0, size=npaths)

                # Calculate the stock prices, using the standard propagation equation
                drift = self.rf_r - self.ref.q
                discount = np.exp(((drift - 0.5 * (self.ref.vol ** 2)) * delta_Ts[tex_index]) + (
                    self.ref.vol * random_samples * np.sqrt(delta_Ts[tex_index])))
                paths[:, tex_index + 1] = paths[:, tex_index] * discount

            return np.matrix(paths)

        # Generate stock_price_paths
        stock_price_paths = generate_stock_price_paths(delta_T_array())

        # Generate the matrix of payouts using the matrix of stock prices
        payouts = payout(stock_price_paths)

        # Copy payouts
        terminal_payouts = np.copy(payouts)

        # Step backwards through the exercise dates, halting before we get to the current date
        for tex_index in range(len(self.tex) - 1, 1, -1):
            # Fit a polynomial of degree R to the stock prices at the tex against the terminal payouts at the tex + 1.
            # Used to generate a vector of coefficients that minimises the squared error.
            MSE_coefficients = np.polyfit(stock_price_paths[:, tex_index].A1,  # A1 reshapes (npaths, 1) to (npaths,)
                                          terminal_payouts[:, tex_index + 1],
                                          R)

            # Calculate the continuation price by evaluating the stock prices at tex_index using the MSE_coefficients
            continuation_price = np.polyval(MSE_coefficients, stock_price_paths[:, tex_index])

            # Calculate the terminal payouts on each path by looking at whether the option is exercised
            condition = payouts[:, tex_index] > continuation_price
            x = payouts[:, tex_index]
            y = terminal_payouts[:, tex_index + 1]
            terminal_payouts[:, tex_index] = np.where(condition.A1, x.A1, y)

        # Calculate the payoffs on each path for the current date
        terminal_payouts[:, 0] = terminal_payouts[:, 1]

        # Find the average price across all the stock_price_paths, then record it
        price = np.mean(terminal_payouts[:, 0])
        self.px_spec.add(px=price)

        # Record history if requested
        if getattr(self.px_spec, 'keep_hist'):
            self.px_spec.add(terminal_payouts=terminal_payouts, payouts=payouts, stock_price_paths=stock_price_paths)

        return self

    def _calc_FD(self):
        """ Internal function for option valuation.

        Returns
        -------
        self: Bermudan

        .. sectionauthor:: 

        Note
        ----

        """

        return self

    def plot_MC(self):
        """
        Plots the price paths, payout paths, and terminal payout paths of a given Monte Carlo simulation.

        Returns
        -------
        None
            Only shows the plot.
        """
        # Fetch history from px_spec
        terminal_payouts = self.px_spec.terminal_payouts
        payouts = self.px_spec.payouts
        stock_price_paths = self.px_spec.stock_price_paths

        # Three subplots sharing both x/y axes
        f, (ax1, ax2, ax3) = plt.subplots(3, sharex=True, sharey=False)

        # The x axis will always be self.tex, with the current date prepended
        x = (0,) + self.tex

        # Plot the price paths graph
        ax1.plot(x, stock_price_paths.T, alpha=0.5, color='0.5')
        mean_price_path, = ax1.plot(x, np.mean(stock_price_paths, axis=0).T, alpha=0.8, label="Mean of price paths")
        ax1.set_title("Price Paths")
        ax1.legend(handles=[mean_price_path], loc=0)  # Position the legend in the "best" place

        # Plot the payout paths graph
        ax2.plot(x, payouts.T, alpha=0.5, color='0.5')
        mean_payout_path, = ax2.plot(x, np.mean(payouts, axis=0).T, alpha=0.8, label="Mean of payout paths")
        ax2.set_title("Payout Paths")
        ax2.legend(handles=[mean_payout_path], loc=0)  # Position the legend in the "best" place

        # Plot the terminal payout paths graph
        ax3.plot(x, terminal_payouts.T, alpha=0.5, color='0.5')
        mean_terminal_payout_path, = ax3.plot(x, np.mean(terminal_payouts, axis=0).T, alpha=0.8,
                                              label="Mean of terminal payout paths")
        ax3.set_title("Terminal Payout Paths")
        ax3.legend(handles=[mean_terminal_payout_path], loc=0)  # Position the legend in the "best" place

        # Set common labels
        f.text(0.5, 0.04, 'Exercise Dates', ha='center', va='center')
        f.text(0.06, 0.5, 'Price', ha='center', va='center', rotation='vertical')

        # Set the window title
        f.canvas.set_window_title('Monte Carlo Simulation')

        # Show the plot
        plt.show(block=True)

        return None