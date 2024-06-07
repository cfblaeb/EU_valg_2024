import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

# load data
df = pd.read_feather("2024_EP_Lasse_data.feather").reset_index()
# df.parti.replace("Frie Grønne, Danmarks Nye Venstrefløjsparti", "Frie Grønne", inplace=True)
color_dict = pd.read_json("various.json").set_index('bogstav_leg')['farver'].to_dict()
# color_dict['Frie Grønne'] = color_dict['Frie Grønne, Danmarks Nye Venstrefløjsparti']
tv2_sprg = pd.read_json('tv2_sprg.json')
dr_sprgs = pd.read_json('dr1_sprg.json')

dk_spg = ['608', '609', '612', '613', '614', '615', '616', '617', '618', '620',
		  '621', '622', '623', '626', '627', '629', '630', '631', '634', '636',
		  '637', '639', '641', '644', '646', '1a', '1b', '2a', '2b', '3a', '3b', '4a', '4b', '5a', '5b', '6a', '6b',
		  '7a', '7b', '8a', '8b', '9a', '9b', '10a', '10b', '11a', '11b']

# do calcs
X = df[dk_spg]
y = df['parti']
lda = LinearDiscriminantAnalysis(n_components=2).fit(X, y)
q = pd.concat([df, pd.DataFrame(lda.transform(df[dk_spg]), columns=["X", "y"]).set_index(df.index)], axis=1)
# hjælp til farveblinde
q['bogstav'] = q.parti.map(pd.read_json("various.json").reset_index().set_index('bogstav_leg')['index'])
q['sized'] = 5

dr_sprgs.columns = dr_sprgs.columns.str.lower()
sprgs = pd.concat([tv2_sprg, dr_sprgs])[['id', 'question']].set_index('id')
sprgs.index = sprgs.index.astype('str')
sprgs = sprgs.loc[dk_spg]
svar_muligheder = ['helt uenig', 'uenig', 'neutral', 'enig', 'helt enig']


def confidence_ellipse(xs, ys, n_std=1.96, size=100):
	if len(xs) != 1:
		cov = np.cov(xs, ys)
		pearson = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
		ell_radius_x = np.sqrt(1 + pearson)
		ell_radius_y = np.sqrt(1 - pearson)
		theta = np.linspace(0, 2 * np.pi, size)
		ellipse_coords = np.column_stack([ell_radius_x * np.cos(theta), ell_radius_y * np.sin(theta)])
		x_scale = np.sqrt(cov[0, 0]) * n_std
		x_mean = np.mean(xs)
		y_scale = np.sqrt(cov[1, 1]) * n_std
		y_mean = np.mean(ys)
		translation_matrix = np.tile([x_mean, y_mean], (ellipse_coords.shape[0], 1))
		rotation_matrix = np.array([[np.cos(np.pi / 4), np.sin(np.pi / 4)], [-np.sin(np.pi / 4), np.cos(np.pi / 4)]])
		scale_matrix = np.array([[x_scale, 0], [0, y_scale]])
		ellipse_coords = ellipse_coords.dot(rotation_matrix).dot(scale_matrix) + translation_matrix

		path = f'M {ellipse_coords[0, 0]}, {ellipse_coords[0, 1]}'
		for k in range(1, len(ellipse_coords)):
			path += f'L{ellipse_coords[k, 0]}, {ellipse_coords[k, 1]}'
		path += ' Z'
		return path


app = Dash(
	title="EU2024 DumData analyse",
	external_stylesheets=[dbc.themes.SOLAR, dbc.icons.BOOTSTRAP],
	meta_tags=[{"name": "viewport", "content": "width=1000, initial-scale=1"}, ],
)
server = app.server

app.layout = dbc.Container([
	dcc.Store(id='bruger_coord'),
	dbc.Card(
		dbc.Container(
			[
				html.H2("EU valg 2024"),
				html.P("Analyse af hvor de enkelte kandidater står i forhold til hinanden og deres partier",
					   className="lead", ),
			],  # fluid=True,
		), body=True
	),
	dbc.Card(
		[
			dbc.Card([
				dbc.Switch(id='parti_shadow', value=True, label="Tegn cirkler om partierne"),
				dbc.Switch(id='farveblind', value=False, label="Farveblind mode"),
			], body=True)
		],
	),

	dbc.Card(dcc.Graph(id='viz')),
	dbc.Card(html.P("(her kommer forudsigelser om hvilket parti en 'klikket' politiker burde være i)", id="svar_res")),
	dbc.Card([
		dcc.Markdown('''
		# SVAR
		### Tryk på politiker for at se deres svar eller svar selv for at se hvor DU ligger
		helt uenig  --  uenig  --  neutral  --  enig  --  helt enig
		'''),
		dbc.ListGroup([
			dbc.ListGroupItem([
				html.P(sprgs.loc[spg]['question']),
				dcc.RadioItems(id=sprgs.loc[spg].name, options=[{'label': '', 'value': x / 4} for x in range(5)],
							   value=0, labelStyle={'display': 'inline-block'})
			]) for spg in dk_spg
		], flush=True)
	], body=True)
	, ],  # fluid=True
)


# %%
@app.callback(Output('viz', 'figure'), [
	Input('parti_shadow', 'value'),
	Input('farveblind', 'value'),
	Input('bruger_coord', 'data')])
def update_graph(shadow, farveblind, data):
	a = q  # efterladt sådan her pga vi ikke filtrere på samme måde som i 2022

	if farveblind:
		f1 = px.scatter(
			a, x='X', y='y', color='parti', color_discrete_map=color_dict, hover_data=['navn', 'job', 'alder'],
			custom_data=['index'], template="plotly_dark", labels={"X": "Hjalmesans", "y": "Fluplighed"},
			size='sized', text='bogstav', size_max=15
			# , width=1000  # , marginal_x='box'
		)
	else:
		f1 = px.scatter(
			a, x='X', y='y', color='parti', color_discrete_map=color_dict, hover_data=['navn', 'job', 'alder'],
			custom_data=['index'], template="plotly_dark", labels={"X": "Hjalmesans", "y": "Fluplighed"},
		)

	f1.layout.xaxis.fixedrange = True
	f1.layout.yaxis.fixedrange = True
	f1.update_layout(modebar_remove=['zoom', 'pan', 'select', 'lasso2d'])

	if shadow:
		for ii, (i, pari_data) in enumerate(q.groupby('parti')):
			if len(pari_data.X) != 1:
				f1.add_shape(type='path', path=confidence_ellipse(pari_data.X, pari_data.y),
							 line_color='rgb(255,255,255,1)', fillcolor=color_dict[i], opacity=.4, )
	if data['dine_aktiv']:
		# f1.add_scatter(x=[data['dine_coords'][0]], y=[data['dine_coords'][1]], mode='markers', marker_symbol='star', marker_size=15)
		f1.add_vline(data['dine_coords'][0], line_dash="dash", line_color="pink")
		f1.add_hline(data['dine_coords'][1], line_dash="dash", line_color="pink")

	return f1


@app.callback([*[Output(x, 'value') for x in dk_spg], Output('svar_res', 'children'), Output('bruger_coord', 'data')],
			  {'clickData': Input('viz', 'clickData'), 'spg_in': [Input(x, 'value') for x in dk_spg]})
def display_click_data(clickData, spg_in):
	ctx = callback_context
	trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
	if trigger_id == 'viz':
		dine_aktiv = False
		if clickData and len(clickData['points']) != 0:
			idx = clickData['points'][0]['customdata'][0]
			navn = clickData['points'][0]['customdata'][1]
		else:
			idx = 1350
			navn = "(klik på nogen)"
		row = q[q['index'] == idx]
		parti = row['parti'].iloc[0]
		nyt_parti = lda.predict(row[dk_spg])[0]
		return [*[row[x].iloc[0] for x in dk_spg],
				f"Du har klikket på {navn}, {parti}. Vedkomne burde overveje {nyt_parti}",
				{'dine_aktiv': dine_aktiv, 'dine_coords': [0, 0]}]
	else:
		dine_aktiv = True
		a = pd.DataFrame(spg_in, index=dk_spg).T
		dine_coords = lda.transform(a)[0]
		return [*[x for x in spg_in],
				f"Dine koordinater er {dine_coords[0]:.1f}, {dine_coords[1]:.1f}. Du burde overveje {lda.predict(a)[0]}",
				{'dine_aktiv': dine_aktiv, 'dine_coords': dine_coords}]


if __name__ == "__main__":
	app.run_server(port=9000)
# app.run_server(debug=True)
