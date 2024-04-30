####################################################################################################
##                                   LIBRARIES AND DEPENDENCIES                                   ##
####################################################################################################
import geoglows
import numpy as np
import math
import plotly.graph_objs as go
import datetime as dt
import pandas as pd
import hydrostats.data as hd
import hydrostats as hs
import plotly.io as pio

###################################################################################################
##                                 UTILS AND AUXILIAR FUNCTIONS                                   ##
####################################################################################################
def get_format_data(sql_statement, conn):
    # Retrieve data from database
    data =  pd.read_sql(sql_statement, conn)
    # Datetime column as dataframe index
    data.index = data.datetime
    data = data.drop(columns=['datetime'])
    # Format the index values
    data.index = pd.to_datetime(data.index)
    data.index = data.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    data.index = pd.to_datetime(data.index)
    # Return result
    return(data)

def get_bias_corrected_data(sim, obs):
    outdf = geoglows.bias.correct_historical(sim, obs)
    outdf.index = pd.to_datetime(outdf.index)
    outdf.index = outdf.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
    outdf.index = pd.to_datetime(outdf.index)
    return(outdf)

def gumbel_1(std: float, xbar: float, rp: int) -> float:
  return -math.log(-math.log(1 - (1 / rp))) * std * .7797 + xbar - (.45 * std)

def get_return_periods(comid, data):
    # Stats
    max_annual_flow = data.groupby(data.index.strftime("%Y")).max()
    mean_value = np.mean(max_annual_flow.iloc[:,0].values)
    std_value = np.std(max_annual_flow.iloc[:,0].values)
    # Return periods
    return_periods = [100, 50, 25, 10, 5, 2]
    return_periods_values = []
    # Compute the corrected return periods
    for rp in return_periods:
      return_periods_values.append(gumbel_1(std_value, mean_value, rp))
    # Parse to list
    d = {'rivid': [comid], 
         'return_period_100': [return_periods_values[0]], 
         'return_period_50': [return_periods_values[1]], 
         'return_period_25': [return_periods_values[2]], 
         'return_period_10': [return_periods_values[3]], 
         'return_period_5': [return_periods_values[4]], 
         'return_period_2': [return_periods_values[5]]}
    # Parse to dataframe
    corrected_rperiods_df = pd.DataFrame(data=d)
    corrected_rperiods_df.set_index('rivid', inplace=True)
    return(corrected_rperiods_df)

def ensemble_quantile(ensemble, quantile, label):
    df = ensemble.quantile(quantile, axis=1).to_frame()
    df.rename(columns = {quantile: label}, inplace = True)
    return(df)

def get_ensemble_stats(ensemble):
    high_res_df = ensemble['ensemble_52_m^3/s'].to_frame()
    ensemble.drop(columns=['ensemble_52_m^3/s'], inplace=True)
    ensemble.dropna(inplace= True)
    high_res_df.dropna(inplace= True)
    high_res_df.rename(columns = {'ensemble_52_m^3/s':'high_res_m^3/s'}, inplace = True)
    stats_df = pd.concat([
        ensemble_quantile(ensemble, 1.00, 'flow_max_m^3/s'),
        ensemble_quantile(ensemble, 0.75, 'flow_75%_m^3/s'),
        ensemble_quantile(ensemble, 0.50, 'flow_avg_m^3/s'),
        ensemble_quantile(ensemble, 0.25, 'flow_25%_m^3/s'),
        ensemble_quantile(ensemble, 0.00, 'flow_min_m^3/s'),
        high_res_df
    ], axis=1)
    return(stats_df)



def get_corrected_forecast(simulated_df, ensemble_df, observed_df):
    monthly_simulated = simulated_df[simulated_df.index.month == (ensemble_df.index[0]).month].dropna()
    monthly_observed = observed_df[observed_df.index.month == (ensemble_df.index[0]).month].dropna()
    min_simulated = np.min(monthly_simulated.iloc[:, 0].to_list())
    max_simulated = np.max(monthly_simulated.iloc[:, 0].to_list())
    min_factor_df = ensemble_df.copy()
    max_factor_df = ensemble_df.copy()
    forecast_ens_df = ensemble_df.copy()
    for column in ensemble_df.columns:
      tmp = ensemble_df[column].dropna().to_frame()
      min_factor = tmp.copy()
      max_factor = tmp.copy()
      min_factor.loc[min_factor[column] >= min_simulated, column] = 1
      min_index_value = min_factor[min_factor[column] != 1].index.tolist()
      for element in min_index_value:
        min_factor[column].loc[min_factor.index == element] = tmp[column].loc[tmp.index == element] / min_simulated
      max_factor.loc[max_factor[column] <= max_simulated, column] = 1
      max_index_value = max_factor[max_factor[column] != 1].index.tolist()
      for element in max_index_value:
        max_factor[column].loc[max_factor.index == element] = tmp[column].loc[tmp.index == element] / max_simulated
      tmp.loc[tmp[column] <= min_simulated, column] = min_simulated
      tmp.loc[tmp[column] >= max_simulated, column] = max_simulated
      forecast_ens_df.update(pd.DataFrame(tmp[column].values, index=tmp.index, columns=[column]))
      min_factor_df.update(pd.DataFrame(min_factor[column].values, index=min_factor.index, columns=[column]))
      max_factor_df.update(pd.DataFrame(max_factor[column].values, index=max_factor.index, columns=[column]))
    corrected_ensembles = geoglows.bias.correct_forecast(forecast_ens_df, simulated_df, observed_df)
    corrected_ensembles = corrected_ensembles.multiply(min_factor_df, axis=0)
    corrected_ensembles = corrected_ensembles.multiply(max_factor_df, axis=0)
    return(corrected_ensembles)


def get_corrected_forecast_records(records_df, simulated_df, observed_df):
    date_ini = records_df.index[0]
    month_ini = date_ini.month
    date_end = records_df.index[-1]
    month_end = date_end.month
    meses = np.arange(month_ini, month_end + 1, 1)
    fixed_records = pd.DataFrame()
    for mes in meses:
        values = records_df.loc[records_df.index.month == mes]
        monthly_simulated = simulated_df[simulated_df.index.month == mes].dropna()
        monthly_observed = observed_df[observed_df.index.month == mes].dropna()
        min_simulated = np.min(monthly_simulated.iloc[:, 0].to_list())
        max_simulated = np.max(monthly_simulated.iloc[:, 0].to_list())
        min_factor_records_df = values.copy()
        max_factor_records_df = values.copy()
        fixed_records_df = values.copy()
        column_records = values.columns[0]
        tmp = records_df[column_records].dropna().to_frame()
        min_factor = tmp.copy()
        max_factor = tmp.copy()
        min_factor.loc[min_factor[column_records] >= min_simulated, column_records] = 1
        min_index_value = min_factor[min_factor[column_records] != 1].index.tolist()
        for element in min_index_value:
            min_factor[column_records].loc[min_factor.index == element] = tmp[column_records].loc[tmp.index == element] / min_simulated
        max_factor.loc[max_factor[column_records] <= max_simulated, column_records] = 1
        max_index_value = max_factor[max_factor[column_records] != 1].index.tolist()
        for element in max_index_value:
            max_factor[column_records].loc[max_factor.index == element] = tmp[column_records].loc[tmp.index == element] / max_simulated
        tmp.loc[tmp[column_records] <= min_simulated, column_records] = min_simulated
        tmp.loc[tmp[column_records] >= max_simulated, column_records] = max_simulated
        fixed_records_df.update(pd.DataFrame(tmp[column_records].values, index=tmp.index, columns=[column_records]))
        min_factor_records_df.update(pd.DataFrame(min_factor[column_records].values, index=min_factor.index, columns=[column_records]))
        max_factor_records_df.update(pd.DataFrame(max_factor[column_records].values, index=max_factor.index, columns=[column_records]))
        corrected_values = geoglows.bias.correct_forecast(fixed_records_df, simulated_df, observed_df)
        corrected_values = corrected_values.multiply(min_factor_records_df, axis=0)
        corrected_values = corrected_values.multiply(max_factor_records_df, axis=0)
        fixed_records = fixed_records.append(corrected_values)
    fixed_records.sort_index(inplace=True)
    return(fixed_records)



####################################################################################################
##                                  AUXILIAR PLOTTING FUNCTIONS                                   ##
####################################################################################################
def _plot_colors():
    return {
        '2 Year': 'rgba(254, 240, 1, .4)',
        '5 Year': 'rgba(253, 154, 1, .4)',
        '10 Year': 'rgba(255, 56, 5, .4)',
        '20 Year': 'rgba(128, 0, 246, .4)',
        '25 Year': 'rgba(255, 0, 0, .4)',
        '50 Year': 'rgba(128, 0, 106, .4)',
        '100 Year': 'rgba(128, 0, 246, .4)',
    }


def _rperiod_scatters(startdate: str, enddate: str, rperiods: pd.DataFrame, y_max: float, max_visible: float = 0):
    colors = _plot_colors()
    x_vals = (startdate, enddate, enddate, startdate)
    r2 = round(rperiods['return_period_2'].values[0], 1)
    if max_visible > r2:
        visible = True
    else:
        visible = 'legendonly'

    def template(name, y, color, fill='toself'):
        return go.Scatter(
            name=name,
            x=x_vals,
            y=y,
            legendgroup='returnperiods',
            fill=fill,
            visible=visible,
            mode="lines",
            line=dict(color=color, width=0))

    r5 = round(rperiods['return_period_5'].values[0], 1)
    r10 = round(rperiods['return_period_10'].values[0], 1)
    r25 = round(rperiods['return_period_25'].values[0], 1)
    r50 = round(rperiods['return_period_50'].values[0], 1)
    r100 = round(rperiods['return_period_100'].values[0], 1)
    rmax = int(max(2 * r100 - r25, y_max))
    
    return [
        template('Periodos de retorno', (rmax, rmax, rmax, rmax), 'rgba(0,0,0,0)', fill='none'),
        template(f'2 años: {r2}', (r2, r2, r5, r5), colors['2 Year']),
        template(f'5 años: {r5}', (r5, r5, r10, r10), colors['5 Year']),
        template(f'10 años: {r10}', (r10, r10, r25, r25), colors['10 Year']),
        template(f'25 años: {r25}', (r25, r25, r50, r50), colors['25 Year']),
        template(f'50 años: {r50}', (r50, r50, r100, r100), colors['50 Year']),
        template(f'100 años: {r100}', (r100, r100, rmax, rmax), colors['100 Year']),
    ]



def get_date_values(startdate, enddate, df):
    date_range = pd.date_range(start=startdate, end=enddate)
    month_day = date_range.strftime("%m-%d")
    pddf = pd.DataFrame()
    pddf.index = month_day
    pddf.index.name = "datetime"
    combined_df = pd.merge(pddf, df, how='left', left_index=True, right_index=True)
    combined_df.index = pd.to_datetime(date_range)
    return(combined_df)


####################################################################################################
##                                      PLOTTING FUNCTIONS                                        ##
####################################################################################################

def get_forecast_stats(stats, rperiods, comid, records, sim):
    # Define the records 
    records = records.loc[records.index >= pd.to_datetime(stats.index[0] - dt.timedelta(days=8))]
    records = records.loc[records.index <= pd.to_datetime(stats.index[0])]
    
    # Start processing the inputs
    dates_forecast = stats.index.tolist()
    dates_records = records.index.tolist()
    try:
        startdate = dates_records[0]
    except:
        startdate = dates_forecast[0]
    enddate = dates_forecast[-1]

    # Generate the average values
    daily = sim.groupby(sim.index.strftime("%m-%d"))
    daymin_df = get_date_values(startdate, enddate, daily.min())
    daymax_df = get_date_values(startdate, enddate, daily.max()) 

    plot_data = {
        'x_stats': stats['flow_avg_m^3/s'].dropna(axis=0).index.tolist(),
        'x_hires': stats['high_res_m^3/s'].dropna(axis=0).index.tolist(),
        'y_max': max(stats['flow_max_m^3/s']),
        'flow_max': list(stats['flow_max_m^3/s'].dropna(axis=0)),
        'flow_75%': list(stats['flow_75%_m^3/s'].dropna(axis=0)),
        'flow_avg': list(stats['flow_avg_m^3/s'].dropna(axis=0)),
        'flow_25%': list(stats['flow_25%_m^3/s'].dropna(axis=0)),
        'flow_min': list(stats['flow_min_m^3/s'].dropna(axis=0)),
        'high_res': list(stats['high_res_m^3/s'].dropna(axis=0)),
    }
    
    plot_data.update(rperiods.to_dict(orient='index').items())
    max_visible = max(max(plot_data['flow_max']), max(plot_data['flow_avg']), max(plot_data['high_res']))
    rperiod_scatters = _rperiod_scatters(startdate, enddate, rperiods, plot_data['y_max'], max_visible)

    scatter_plots = [
        go.Scatter(
            name='Máximos y mínimos históricos',
            x=np.concatenate([daymax_df.index, daymin_df.index[::-1]]),
            y=np.concatenate([daymax_df.iloc[:, 0].values, daymin_df.iloc[:, 0].values[::-1]]),
            legendgroup='historical',
            fill='toself',
            line=dict(color='lightgrey', dash='dash'),
            mode="lines",
        ),
        go.Scatter(
            name='Maximum',
            x=daymax_df.index,
            y=daymax_df.iloc[:, 0].values,
            legendgroup='historical',
            showlegend=False,
            line=dict(color='grey', dash='dash'),
            mode="lines",
        ),
        go.Scatter(
            name='Minimum',
            x=daymin_df.index,
            y=daymin_df.iloc[:, 0].values,
            legendgroup='historical',
            showlegend=False,
            line=dict(color='grey', dash='dash'),
            mode="lines",
        ),

        #go.Scatter(name='Máximos y mínimos pronosticados',
        #           x=plot_data['x_stats'] + plot_data['x_stats'][::-1],
        #           y=plot_data['flow_max'] + plot_data['flow_min'][::-1],
        #           legendgroup='boundaries',
        #           fill='toself',
        #           line=dict(color='lightblue', dash='dash')),
        #go.Scatter(name='Máximo pronosticado',
        #           x=plot_data['x_stats'],
        #           y=plot_data['flow_max'],
        #           legendgroup='boundaries',
        #           showlegend=False,
        #           line=dict(color='darkblue', dash='dash')),
        #go.Scatter(name='Minimo pronosticado',
        #           x=plot_data['x_stats'],
        #           y=plot_data['flow_min'],
        #           legendgroup='boundaries',
        #           showlegend=False,
        #           line=dict(color='darkblue', dash='dash')),

        go.Scatter(name='Rango percentílico 25%-75%',
                   x=plot_data['x_stats'] + plot_data['x_stats'][::-1],
                   y=plot_data['flow_75%'] + plot_data['flow_25%'][::-1],
                   legendgroup='percentile_flow',
                   fill='toself',
                   line=dict(color='lightgreen'), ),
        go.Scatter(name='75%',
                   x=plot_data['x_stats'],
                   y=plot_data['flow_75%'],
                   showlegend=False,
                   legendgroup='percentile_flow',
                   line=dict(color='green'), ),
        go.Scatter(name='25%',
                   x=plot_data['x_stats'],
                   y=plot_data['flow_25%'],
                   showlegend=False,
                   legendgroup='percentile_flow',
                   line=dict(color='green'), ),

        go.Scatter(name='Pronóstico de alta resolución',
                   x=plot_data['x_hires'],
                   y=plot_data['high_res'],
                   line={'color': 'black'}, ),
        go.Scatter(name='Promedio del ensamble',
                   x=plot_data['x_stats'],
                   y=plot_data['flow_avg'],
                   line=dict(color='blue'), ),
    ]
    
    if len(records.index) > 0:
        records_plot = [go.Scatter(
            name='Condiciones antecedentes',
            x=records.index,
            y=records.iloc[:, 0].values,
            line=dict(color='#FFA15A',))]
        scatter_plots += records_plot

    #scatter_plots += rperiod_scatters

    layout = go.Layout(
        #title=f"Pronóstico de Niveles <br>COMID:{comid}",
        yaxis={'title': 'Nivel (m)', 'range': [0, 'auto']},
        xaxis={'title': 'Fecha (UTC +0:00)', 'range': [startdate, enddate], 'hoverformat': '%b %d %Y %H:%M',
               'tickformat': '%b %d %Y'},
    )
    figure = go.Figure(scatter_plots, layout=layout)
    figure.update_layout(template='simple_white', width = 1000, height = 400)
    figure.update_yaxes(linecolor='gray', mirror=True, showline=True) 
    figure.update_xaxes(linecolor='gray', mirror=True, showline=True)
    figure.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    return(figure)

def get_historic_simulation(cor, obs, code, name):
    dates = cor.index.tolist()
    startdate = dates[0]
    enddate = dates[-1]
    corrected_data = {
        'x_datetime': cor.index.tolist(),
        'y_flow': cor.values.flatten(),
    }
    observed_data = {
        'x_datetime': obs.index.tolist(),
        'y_flow': obs.values.flatten(),
    }
    scatter_plots = [
        go.Scatter(name='Simulación histórica corregida', x=corrected_data['x_datetime'], y=corrected_data['y_flow']),
        go.Scatter(name='Datos observados', x=observed_data['x_datetime'], y=observed_data['y_flow'])
    ]
    layout = go.Layout(
        title=f"Simulación histórica <br>{str(code).upper()} - {name}",
        yaxis={'title': 'Nivel (m)', 'range': [0, 'auto']},
        xaxis={'title': 'Fecha (UTC +0:00)', 'range': [startdate, enddate], 'hoverformat': '%b %d %Y', 'tickformat': '%Y'},
    )
    figure = go.Figure(scatter_plots, layout=layout)
    figure.update_layout(template='simple_white')
    figure.update_yaxes(linecolor='gray', mirror=True, showline=True) 
    figure.update_xaxes(linecolor='gray', mirror=True, showline=True)
    return figure

####################################################################################################
##                                        MAIN FUNCTION                                           ##
####################################################################################################
def plot(comid, observed_data, conn, outpath):
    # Data series
    simulated_data = get_format_data("select * from r_{0} where datetime < '2022-06-01 00:00:00';".format(comid), conn)
    corrected_data = get_bias_corrected_data(simulated_data, observed_data)
    #
    # Raw forecast
    ensemble_forecast = get_format_data("select * from f_{0};".format(comid), conn)
    forecast_records = get_format_data("select * from fr_{0};".format(comid), conn)
    return_periods = get_return_periods(comid, simulated_data)
    #
    # Corrected forecast
    corrected_ensemble_forecast = get_corrected_forecast(simulated_data, ensemble_forecast, observed_data)
    corrected_forecast_records = get_corrected_forecast_records(forecast_records, simulated_data, observed_data)
    corrected_return_periods = get_return_periods(comid, corrected_data)
    #
    # Stats for raw and corrected forecast
    ensemble_stats = get_ensemble_stats(ensemble_forecast)
    corrected_ensemble_stats = get_ensemble_stats(corrected_ensemble_forecast)
    #
    # Forecast plot
    forecast_plot = get_forecast_stats(
        stats = corrected_ensemble_stats,
        rperiods = corrected_return_periods,
        comid = comid,
        records = corrected_forecast_records,
        sim = observed_data)
    #
    pio.write_image(forecast_plot, outpath)
    #
    daily_avg = corrected_ensemble_stats.resample('D').mean().round(2)
    daily_avg.index = pd.to_datetime(daily_avg.index)
    daily_avg["Fecha"] = daily_avg.index.to_series().dt.strftime("%Y-%m-%d")
    daily_avg = daily_avg[['Fecha', 'flow_avg_m^3/s', "high_res_m^3/s"]]
    daily_avg = daily_avg.rename(columns={  'flow_avg_m^3/s': 'Nivel medio pronosticado (m)', 
                                            "high_res_m^3/s": "Pronóstico de Alta resolución (m)"})
    return(daily_avg)
