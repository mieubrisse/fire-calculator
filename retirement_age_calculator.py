from enum import Enum, auto

# TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO 
# This whole class models data as arrays, but
#  it could (and probably should) be modeled as mathematical functions
# TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO TODO 

class ContributionFunction:
    """
    Function that returns the yearly contribution amount for any given year in the [0, years_to_live),
     taking into account contrib increases and changes.
    """
    def __init__(self, years_to_live, manual_contrib_changes, initial_contrib_amount, initial_contrib_rate):
        self.contribs = []
        current_base_contrib = initial_contrib_amount
        current_contrib_rate = initial_contrib_rate
        years_since_last_change = 0
        for i in range(0, years_to_live):
            if i in manual_contrib_changes:
                current_base_contrib, current_contrib_rate = manual_contrib_changes[i]
                years_since_last_change = 0
            self.contribs.append(current_base_contrib * (1 + current_contrib_rate) ** years_since_last_change)
            years_since_last_change = years_since_last_change + 1

    def apply(self, years_in_future):
        return self.contribs[years_in_future]

    def data(self):
        return self.contribs.copy()

class NoRetirementNetWorthFunction:
    """
    Function that returns net worth for a given year in range [0, years_to_live), accounting for net worth and
     contribution changes.
    """
    def __init__(self, years_to_live, manual_net_worth_changes, current_retirement_savings, pre_retirement_growth_rate, contribution_function):
        # TODO make this a nice math formula
        # We assume:
        # 1. This money is withdrawn at the start of the year, with the 0th entry being how much you'd need if you were to retire RIGHT NOW
        # 2. The amount you'd withdraw to last you this year doesn't have inflation applied (it will only increase the amount of next year)
        # E.g. if I have 2 years to live, this array will look like [gross_retirement_income, gross_retirement_income * (1 + inflation)]
        self.net_worth = []
        for i in range(0, years_to_live):
            value_to_append = None
            if i == 0:
                value_to_append = current_retirement_savings
            else:
                # Growth from your balance, and then add your annual contribution afterwards (this is conservative)
                value_to_append = self.net_worth[i-1] * (1 + pre_retirement_growth_rate) + contribution_function.apply(i-1)
            value_with_net_worth_change = max(0, value_to_append + manual_net_worth_changes.get(i, 0))
            self.net_worth.append(value_with_net_worth_change)

    def apply(self, years_in_future):
        return self.net_worth[years_in_future]

    def data(self):
        return self.net_worth.copy()

class RetirementWithdrawalsFunction:
    """
    Describes, for each year in [0, years_to_live), the inflation-adjusted absolute withdrawal amount required to meet the desired net retirement income in today's dollars
    """
    def __init__(self, years_to_live, net_retirement_income_todays_dollars, retirement_tax_rate, inflation_rate, manual_retirement_income_changes):
        net_income = net_retirement_income_todays_dollars
        self.withdrawals = []
        for i in range(0, years_to_live):
            if i in manual_retirement_income_changes:
                net_income = manual_retirement_income_changes[i]
            gross_income = net_income / (1.0 - retirement_tax_rate)
            # We subract one year from the exponentiation because inflation will only kick in one year from today
            self.withdrawals.append(gross_income * (1.0 + inflation_rate) ** i)

    def apply(self, years_in_future):
        return self.withdrawals[years_in_future]

    def data(self):
        return self.withdrawals.copy()

class RetirementMinWorthFunction:
    """
    Function to describe the minimum worth needed at every year in [0,years_to_live) to not run out of money before dying
    """
    def __init__(self, years_to_live, withdrawal_function, post_retirement_growth_rate):
        # This is a super stupid, but super clear, way to do this
        min_worth_for_last_x_year = []
        for i in range(0, years_to_live):
            withdrawal = withdrawal_function.apply((years_to_live - 1) - i)
            value_to_append = None
            if i == 0:
                value_to_append = withdrawal
            else:
                # Our bank account can be a little lower because we'll get in-year growth
                remaining_balance_needed = min_worth_for_last_x_year[i - 1] / (1 + post_retirement_growth_rate)
                value_to_append = withdrawal + remaining_balance_needed
            min_worth_for_last_x_year.append(value_to_append)

        # Necessary to reverse so this makes sense
        self.min_worth = list(reversed(min_worth_for_last_x_year))

    def apply(self, years_in_future):
        return self.min_worth[years_in_future]

    def data(self):
        return self.min_worth.copy()

class AccountValueFunction:
    """
    Function representing the actual account value over time, with
     retirement factored in.
    """
    def __init__(self, years_to_live, retirement, no_retirement_func, post_retirement_growth_rate, withdrawal_func):
        self.account_value = None
        if retirement is not None:
            # Because we're a little cautious in that we'll only say you can retire when your bank account is >= the amount you'd need for the rest of your life, re-calculate to get exact values of your bank account after you retire
            self.account_value = []
            for i in range(0, years_to_live):
                if i <= retirement:
                    value_to_append = no_retirement_func.apply(i)
                # After first retirement year
                else:
                    # To be conservative, we assume you take out your retirement income at the start of the year (i.e. no market growth on it)
                    last_year_value = self.account_value[i - 1]
                    last_year_withdrawal = withdrawal_func.apply(i - 1)
                    value_to_append = max(
                        0,
                        (last_year_value - last_year_withdrawal) * (1 + post_retirement_growth_rate)
                    )
                self.account_value.append(value_to_append)

    def apply(self, years_in_future):
        return self.account_value[years_in_future]

    def data(self):
        return self.account_value.copy()

class ActualWithdrawalsFunction:
    def __init__(self, years_to_live, retirement, withdrawals_func):
        self.withdrawals = None
        if retirement is not None:
            self.withdrawals = []
            for i in range(0, years_to_live):
                value_to_append = 0 if i < retirement else withdrawals_func.apply(i)
                self.withdrawals.append(value_to_append)

    def apply(self, years_in_future):
        return self.withdrawals[years_in_future]

    def data(self):
        return self.withdrawals.copy()


class Series(Enum):
    # Represents hypothetical withdrwaw
    ALL_WITHDRAWALS = auto()
    MIN_RETIREMENT_WORTH = auto()
    CONTRIBUTIONS = auto()
    NO_RETIREMENT = auto()

    # Represents actual account value including retirement
    ACCOUNT_VALUE = auto()

    # Represents the actual withdrawals, with pre-retirement withdrawals at 0
    ACTUAL_WITHDRAWALS = auto()

class RetirementAgeCalculator:
    """
    Main class, used to calculate the earliest age of retirement given the various inputs
    """
    def __init__(self,
            current_retirement_savings,
            annual_contribution,
            annual_contribution_increase_rate,
            pre_retirement_growth_rate,
            post_retirement_growth_rate,
            inflation_rate,
            years_to_live,
            desired_net_retirement_income_todays_dollars,
            retirement_tax_rate,
            manual_contrib_changes=None,
            manual_net_worth_changes=None,
            manual_retirement_income_changes=None):
        # TODO actually handle net worth changes at any point in time
        """
        Pregenerates a retirement model based off the given inputs, allowing you to query various characteristics of the model
        after creation.

        NOTE: As of 2020-04-19, any net worth or contribution changes that end up AFTER the projected retirement date
        are ignored, leading to incorrect projections

        Args:
            current_retirement_savings: current amount saved for retirement right now
            annual_contribution: current amount being contributed to retirement right now
            annual_contribution_increase_rate: year-over-year growth of annual contribution, as double (0.XX)
            pre_retirement_growth_rate: market growth rate before retirement, as double (0.XX)
            post_retirement_growth_rate: market growth rate after retirement, as double (0.XX)
            inflation_rate: inflation rate, as double (0.XX)
            years_to_live: estimated remaining years to live
            desired_net_retirement_income_todays_dollars: desired NET retirement income, in today's dollars
            retirement_tax_rate: estimated tax rate during reitrement, as double (0.XX)
            manual_contrib_changes: dictionary indicating changes to contrib amount and rate in the future, in the form:
                <num years in future of change>: (<new contribution amount>, <new contribution rate>)
                e.g. {2: (100000, 0.05)}
            manual_net_worth_changes: dictionary indicating one-off changes to net worth in the future, in the form:
                <num years in future of change>: <net worth change>
                e.g. {2: 10000}
                e.g. {3: -5000}
            manual_retirement_income_changes: dicionary indicating changes to net retirement income in the future, in the form:
                <num years in future of change>: <new retirement income>
                e.g. {2: 50000}
        """
        manual_contrib_changes = manual_contrib_changes if manual_contrib_changes is not None else {}
        manual_net_worth_changes = manual_net_worth_changes if manual_net_worth_changes is not None else {}
        manual_retirement_income_changes = manual_retirement_income_changes if manual_retirement_income_changes is not None else {}

        for years_out in manual_contrib_changes.keys():
            if years_out < 0 or years_out >= years_to_live:
                raise ValueError("Invalid contrib change year '%s'; must be in range [0,%s)" % years_out, years_to_live)
        for years_out in manual_net_worth_changes.keys():
            if years_out < 0 or years_out >= years_to_live:
                raise ValueError("Invalid net worth change year '%s'; must be in range [0,%s)" % years_out, years_to_live)
        for years_out in manual_retirement_income_changes.keys():
            if years_out < 0 or years_out >= years_to_live:
                raise ValueError("Invalid retirement income change year '%s'; must be in range [0,%s)" % years_out, years_to_live)
        if years_to_live < 1:
            raise ValueError("Years to live must be >= 1")

        all_withdrawals_function = RetirementWithdrawalsFunction(years_to_live, desired_net_retirement_income_todays_dollars, retirement_tax_rate, inflation_rate, manual_retirement_income_changes)
        min_worth_function = RetirementMinWorthFunction(years_to_live, all_withdrawals_function, post_retirement_growth_rate)

        contribution_function = ContributionFunction(
            years_to_live,
            manual_contrib_changes,
            annual_contribution,
            annual_contribution_increase_rate)
        no_retirement_function = NoRetirementNetWorthFunction(years_to_live, manual_net_worth_changes, current_retirement_savings, pre_retirement_growth_rate, contribution_function)

        # Contigent-on-retirement-solution
        self.years_to_retirement = None
        for i in range(0, years_to_live):
            if no_retirement_function.apply(i) >= min_worth_function.apply(i):
                self.years_to_retirement = i
                break
        actual_withdrawals_function = ActualWithdrawalsFunction(years_to_live, self.years_to_retirement, all_withdrawals_function)
        account_value_function = AccountValueFunction(years_to_live, self.years_to_retirement, no_retirement_function, post_retirement_growth_rate, all_withdrawals_function)

        self.waste = None
        if self.years_to_retirement is not None:
            last_year = years_to_live - 1
            self.waste = account_value_function.apply(last_year) - actual_withdrawals_function.apply(last_year)

        self.underlying_funcs = {
            Series.ALL_WITHDRAWALS: all_withdrawals_function,
            Series.MIN_RETIREMENT_WORTH: min_worth_function,
            Series.CONTRIBUTIONS: contribution_function,
            Series.NO_RETIREMENT: no_retirement_function,
            Series.ACCOUNT_VALUE: account_value_function,
            Series.ACTUAL_WITHDRAWALS: actual_withdrawals_function,
        }

    def get_earliest_retirement(self):
        """
        Get the smallest number of years after which you'll be able to retire, or None if not possible
        """
        return self.years_to_retirement

    def get_waste(self):
        """
        Dollars you'd die with (or None if you never get to retire). Less waste signifies close to retiring
         one year later if you increase costs; more waste signifies closeness to retiring one year earlier
         if you reduce costs.
        """
        return self.waste

    def get_series_data(self, series):
        return self.underlying_funcs[series].data()
