import pandas as pd
import datetime

html_output_file = 'docs/CORDEX-CORE-CMIP6_WRF_status.html'

# HTML styling
span_style = '''
span.planned {color: #F54d4d; font-weight: bold}
span.running {color: #009900; font-weight: bold}
span.completed {color: #17202a; font-weight: bold}
span.published {color: #3399FF; font-weight: bold}

span.reginst {color: black; font-weight: bold}
span.unreginst {color: grey; font-style: italic; font-weight: bold}
span.unregistered {color: grey; font-style: italic; font-weight: bold}
span.ARCM {color: black; font-weight: bold}
span.AORCM {color: #2980b9; font-weight: bold}
span.AGCM {color: black; font-weight: bold}
span.AOGCM {color: #2980b9; font-weight: bold}
span.ESD {color: #ca6f1e; font-weight: bold}
'''

html_style = '''
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
<style>
body {
  font-family: 'Montserrat', sans-serif;
  padding-top: 15px;
  padding-left: 15px;
  padding-right: 15px;
  padding-bottom: 600px;
}
tr:hover {background-color:#f5f5f5;}
th, td {text-align: center; padding: 3px;}
table {border-collapse: collapse;}''' + span_style + '''
a {color: DodgerBlue}
a:link { text-decoration: none; }
a:visited { text-decoration: none; }
a:hover { text-decoration: underline; }
a:active { text-decoration: underline;}
ul.twocol { columns: 2; -webkit-columns: 2; -moz-columns: 2; }
.logo {
  text-align: center;
  margin-bottom: 20px;
}
</style>
'''

html_legend = '''
      <p style="font-size: smaller;"> Colour legend for status:
        (
        <span class="planned">planned</span>
        <span class="running">running</span>
        <span class="completed">completed</span>
        <span class="published">published</span>
        )
      </p>
'''

def html_header(title='CORDEX-CMIP6 downscaling plans', mip_era='CMIP6'):
    return f'''<!DOCTYPE html>
<html><head>
{html_style}
</head><body>
<div class="logo">
<img src="https://cordex.org/wp-content/uploads/2025/02/CORDEX_RGB_logo_baseline_positive-300x133.png" 
   alt="CORDEX Logo" >
<h1 id="top">{title}</h1>
</div>
<div style="display:table;width:100%;">
  <div style="display:table-row;">
    <div style="display:table-cell;width:50%;">
Check the status of the full CORDEX-CORE ensemble <a href="https://wcrp-cordex.github.io/simulation-status/CORDEX_CMIP6_status_by_experiment.html#All-CORDEX-CORE">here</a>.
    </div>
    <div style="display:table-cell;text-align:right;width:50%;">
      (Version: {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")} UTC)
    </div>
  </div>
</div>
<p style="text-align: justify;">
Simulation status according to CORDEX-{mip_era} downscaling plans reported by the groups and collected in <a href="https://github.com/WCRP-CORDEX/simulation-status/blob/main/{mip_era}_downscaling_plans.csv">{mip_era}_downscaling_plans.csv</a>. 
To contribute/update simulations open an issue or pull request at <a href="https://github.com/WCRP-CORDEX/simulation-status">https://github.com/WCRP-CORDEX/simulation-status</a>.
'''

def html_footer():
    return '</body></html>'

table_props = [('width', '100px')]

# Retrieve the CSV from GitHub
csv_url = 'https://raw.githubusercontent.com/WCRP-CORDEX/simulation-status/main/CMIP6_downscaling_plans.csv'
plans = pd.read_csv(csv_url, na_filter=False)

# Filter
plans = plans[plans['comments'].str.contains('#CORDEX-CORE', case=False, na=False)]
plans = plans[plans['source_id'].str.startswith('WRF', na=False)]
plans = plans[plans['driving_experiment_id'] != 'historical']

# Add HTML span with status coloring for each institution
def format_institution_with_status(group):
    """Format institutions with status-based coloring"""
    if len(group) == 0:
        return ''
    
    colored_insts = []
    for _, row in group.iterrows():
        status = row['status']
        inst = row['institution_id']
        colored_insts.append(f'<span class="{status}">{inst}</span>')
    
    return ', '.join(colored_insts)

# Create pivot table with colored institutions
pivot = plans.pivot_table(
    index='domain_id',
    columns='driving_source_id',
    values='institution_id',
    aggfunc=lambda x: format_institution_with_status(
        plans.loc[x.index, ['institution_id', 'status']]
    )
)

# Reorder columns to put ERA5 first
if 'ERA5' in pivot.columns:
    era5_col = pivot.pop('ERA5')
    pivot.insert(0, 'ERA5', era5_col)

# Generate HTML
f = open(html_output_file, 'w')
f.write(html_header('CORDEX-CORE WRF simulations', mip_era='CMIP6'))
f.write(html_legend)

# Style and output the table
d1 = dict(selector=".level1", props=table_props)
f.write(pivot.style
    .set_properties(**{'font-size': '8pt', 'border': '1px lightgrey solid !important'})
    .set_table_styles([d1, {
        'selector': 'th',
        'props': [('font-size', '8pt'), ('border-style', 'solid'), ('border-width', '1px')]
    }])
    .to_html()
    .replace('nan', '')
)

f.write(html_footer())
f.close()

print(f"Table saved to {html_output_file}")
print(f"\nFiltered data shape: {plans.shape[0]} simulations")
print(f"Domains: {sorted(plans['domain_id'].unique())}")
print(f"Driving GCMs: {sorted(plans['driving_source_id'].unique())}")
