FIRE Calculator
===============
This small Python CLI takes in several variables, and predicts how many years until you can [FIRE](https://en.wikipedia.org/wiki/FIRE_movement) assuming you want to die with as close to $0 in your bank account as possible.

It accounts for inflation, different monetary needs at different points in time (e.g. you probably don't need as much money when you're 80 as when you're 40), etc.

### Usage
To use, run `python early-retirement-cli.py -h` and fill in the required positional args:

```
usage: early-retirement-cli.py [-h] [-w years_out value] [-c years_out contrib contrib_rate] [-i years_out net_income] [--no-table]
                               current_savings annual_contribution annual_contrib_increase_rate pre_growth_rate post_growth_rate inflation_rate years_to_live net_retirement_income
                               retirement_tax_rate

Calculate the earliest retirement is available based on the given parameters.

positional arguments:
  current_savings       Current retirement savings right now, in dollars
  annual_contribution   Annual contribution, in dollars
  annual_contrib_increase_rate
                        Annual contribution, in dollars
  pre_growth_rate       Market growth rate before retirement, in the form 0.XX
  post_growth_rate      Market growth rate during retirement, in the form 0.XX
  inflation_rate        Inflation rate, in the form 0.XX
  years_to_live         How many more years you estimate you'll live
  net_retirement_income
                        Desired net income in retirement, in *today's* dollars
  retirement_tax_rate   Estimated tax rate in retirement, in the form 0.XX

options:
  -h, --help            show this help message and exit
  -w years_out value, --change-worth years_out value
                        Indicate a one-off change in net worth at the start of year X (useful to represent a big cash in/outflux - e.g. selling equity). This option can be specified
                        multiple times.
  -c years_out contrib contrib_rate, --change-contrib years_out contrib contrib_rate
                        Indicate a change in annual contribution amount/rate at the start of year X (useful to represent changing life situation - e.g. a new job). This option can be
                        specified multiple times.
  -i years_out net_income, --change-retirement-income years_out net_income
                        Indicate a change in annual net retirement income, denominated in today's dollars, at the start of year X (useful to represent changing life situation - e.g.
                        children moving out of home). This option can be specified multiple times.
  --no-table            Don't show the table, just the number of years to retirement
```

### Example
E.g. to indicate that we have $1m, contribute $10k to our retirement account each year, expect 6% gains, 4% inflation, plan to live for 10 years, want $100k of today's dollars in retirement AFTER tax, and expect a 30% tax rate...

```
python early-retirement-cli.py 1000000 10000 0 0.06 0.06 0.04 10 100000 0.3
```

Assuming you've run `pip install tabulate` for pretty-printed tables, you'll get an output like so:

```
 > YEARS TO RETIREMENT: 3
 > WASTE: 226,529 (dollars at death)
NOTE: retirement withdrawal is taken out at the start of the year, i.e. immediately after the bank_statement
   years | account balance   | ret withdrawal   | min balance to ret   | balance if never retire   | annual contrib
---------+-------------------+------------------+----------------------+---------------------------+------------------
       0 | 1,000,000         | 0                | 1,313,183            | 1,000,000                 | 10,000
       1 | 1,070,000         | 0                | 1,240,545            | 1,070,000                 | 10,000
       2 | 1,144,200         | 0                | 1,157,492            | 1,144,200                 | 10,000
       3 | 1,222,852         | 160,694          | 1,063,157            | 1,222,852                 | 10,000
       4 | 1,125,886         | 167,122          | 956,610              | 1,306,223                 | 10,000
       5 | 1,016,289         | 173,807          | 836,856              | 1,394,596                 | 10,000
       6 | 893,031           | 180,759          | 702,832              | 1,488,272                 | 10,000
       7 | 755,007           | 187,990          | 553,396              | 1,587,568                 | 10,000
       8 | 601,038           | 195,509          | 387,330              | 1,692,822                 | 10,000
       9 | 429,860           | 203,330          | 203,330              | 1,804,392                 | 10,000
```

The columns explained:
- `years`: the number of years from today
- `account balance`: how much you'd have in your account on the given year
- `ret withdrawal`: how many dollars you need to withdraw in that year to receive $100k of today's dollars after tax
- `min balance to ret`: how many dollars you'd need in your bank account in that year to be able to FIRE
- `balance if never retire`: fun number to see how big your balance could go if you never retired
- `annual contrib`: the amount we contribute to our retirement fund each year before we retire (meaningless after retirement)

Interpreting this scenario:
- We can FIRE in 3 years (when `account balance` > `min balance to ret`)
- If we wanted to FIRE right now, we'd need $1,313,183 today
- Due to inflation, the amount we need to withdraw each year goes up by 4% (ending at $203,330 in our final year of life)
