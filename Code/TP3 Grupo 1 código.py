import requests
from bs4 import BeautifulSoup
import json
import xmltojson
import html_to_json
import csv
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML

URL = "https://www.hoqueipatins.pt/liga/1-divisao-regular/"
r = requests.get(URL)
print(r)
pars = BeautifulSoup(r.content, 'html.parser')
# print(pars)
with open("hoquei.html", 'w', encoding="utf-8") as arquivo:
    arquivo.write(pars.decode())

table = pars.find('div', attrs={'id': "resultados"})
# print(table)

'''
#estava a tentar retirar um a um mas eu queria que os dicionarios fossem agregados por jogo

for row in table.findAll('span', attrs={"class":"eventDate"}):
    data = {}
    data['dia'] = row.text
    resultados.append(data)

for row in table.findAll('div', attrs={"class":"teamHome textNoBreak"}):
    data = {}
    data['equipa da casa'] = row.text
    resultados.append(data)

print(resultados)

#vizualização em csv 

filename = 'inspirational_quotes.csv'
with open(filename, 'w', newline='') as f:
    w = csv.DictWriter(f,['dia','equipa da casa'])
    w.writeheader()
    for linha in resultados:
        w.writerow(linha)

'''
resultados = []
# ciclo que por cada evento retira os dados q queremos.
# usamos uma funçao lambda para verificar se o atrubto class contem a sub string container-event-
for row in table.findAll('tr', class_=lambda x: x and 'container-event-' in x):
    # extrair a data
    data_span = row.select_one('td.timeGame span.eventDate')
    data = data_span.text.strip()

    # extrair o nome das equipas
    equipa_casa = row.select_one('td.teamsGame div.teamHome').text.strip()
    equipa_fora = row.select_one('td.teamsGame div.teamAway').text.strip()

    # extrair o resultado
    resultado_casa = row.select_one('span.resultHome').text.strip()
    resultado_fora = row.select_one('span.resultAway').text.strip()
    resultado_jogo = f"{resultado_casa}-{resultado_fora}"

    # extrair o emblema equipa da casa
    emblema_casa = row.select_one('td.teamsGame div.teamHome div.logoTeam img')['src'] if row.select_one(
        'td.teamsGame div.teamHome div.logoTeam img') else 'N/A'

    # extrair o emblema equipa de fora
    emblema_fora = row.select_one('td.teamsGame div.teamAway div.logoTeam img')['src'] if row.select_one(
        'td.teamsGame div.teamAway div.logoTeam img') else 'N/A'

    # dicionário com a informaçao do jogo da iteraçao atual
    info_jogo = {
        'Data': data,
        'Equipa da Casa': equipa_casa,
        'Emblema da Casa': emblema_casa,
        'Resultado do Jogo': resultado_jogo,
        'Emblema de Fora': emblema_fora,
        'Equipa de Fora': equipa_fora
    }

    # adicionar o dicionario à lista resultados
    resultados.append(info_jogo)

print(resultados)

# guardar os resultados num ficheiro em formato json
with open("hoquei.json", 'w') as w:
    json.dump(resultados, w, indent=2)

# ler o json
with open("hoquei.json", 'r', encoding='utf-8') as i:
    corpus = json.load(i)


# Função para calcular o maior número de vitórias consecutivas de uma equipe
#nao utilizada na pagina web
def calcular_maior_numero_vitorias_consecutivas(corpus, equipa_alvo):
    max_vitorias_consecutivas = 0
    vitorias_consecutivas_atuais = 0
    games_of_max_streak = []

    for jogo in corpus:
        home_team = jogo['Equipa da Casa']
        away_team = jogo['Equipa de Fora']
        resultado = jogo['Resultado do Jogo']

        # Verifica se a equipe alvo participou do jogo
        if equipa_alvo in [home_team, away_team]:
            # Verifica se a equipe alvo venceu o jogo
            if (home_team == equipa_alvo and resultado[0] > resultado[2]) or (
                    away_team == equipa_alvo and resultado[2] > resultado[0]):
                vitorias_consecutivas_atuais += 1
                # Atualiza o maior número de vitórias consecutivas e a lista de jogos
                if vitorias_consecutivas_atuais > max_vitorias_consecutivas:
                    max_vitorias_consecutivas = vitorias_consecutivas_atuais
                    games_of_max_streak = [jogo]
                else:
                    games_of_max_streak.append(jogo)
            else:
                # Se a equipe alvo não venceu o jogo, reinicia o contador de vitórias consecutivas
                vitorias_consecutivas_atuais = 0

    return max_vitorias_consecutivas, games_of_max_streak


equipa_alvo = 'Sporting CP'  # Substitua pelo nome da equipe desejada
maior_numero_vitorias, jogos_da_sequencia = calcular_maior_numero_vitorias_consecutivas(corpus, equipa_alvo)

print(f'O maior número de vitórias consecutivas de {equipa_alvo} é: {maior_numero_vitorias}')
print(f'Jogos da sequência:{jogos_da_sequencia}')


# classificaçao da liga
def calculate_team_classification(corpus):
    team_points = {}

    for jogo in corpus:
        home_team = jogo['Equipa da Casa']
        away_team = jogo['Equipa de Fora']
        resultado = jogo['Resultado do Jogo']

        if resultado != "---":
            home_points = 3 if resultado[0] > resultado[2] else 1 if resultado[0] == resultado[2] else 0
            away_points = 3 if resultado[2] > resultado[0] else 1 if resultado[2] == resultado[0] else 0
            #soma os pontos aos pontos ja existentes e caso ainda nao haja pontos assume 0
            team_points[home_team] = team_points.get(home_team, 0) + home_points
            team_points[away_team] = team_points.get(away_team, 0) + away_points

    # ordena por ordem decrescente de pontos
    sorted_teams = sorted(team_points.items(), key=lambda x: -x[1])

    # cria um dicionário para a classificação
    team_classification = [{'Equpa': team, 'Pontos': points} for team, points in sorted_teams]

    return team_classification


team_classification_result = calculate_team_classification(corpus)
print(team_classification_result)


# funçao com golos marcados e sofridos por equipa
def calcular_estatisticas_golos(corpus):

    estatisticas_golos = {}

    for jogo in corpus:
        home_team = jogo['Equipa da Casa']
        away_team = jogo['Equipa de Fora']
        resultado = jogo['Resultado do Jogo']

        # verifica se o jogo ja foi jogado e se a string - esta contida nos resultados
        if resultado != '---':
            golos_casa, golos_fora = map(str.strip, resultado.split('-'))

            # verificar se sao os dois numericos
            if golos_casa.isdigit() and golos_fora.isdigit():
                golos_casa = int(golos_casa)
                golos_fora = int(golos_fora)

                # Update goals scored for the home team
                estatisticas_golos[home_team] = estatisticas_golos.get(home_team, {'Jogos': 0, 'Golos Marcados': 0,
                                                                                   'Golos Sofridos': 0})
                estatisticas_golos[home_team]['Golos Marcados'] += golos_casa
                estatisticas_golos[home_team]['Golos Sofridos'] += golos_fora
                estatisticas_golos[home_team]['Jogos'] += 1

                # Update goals scored for the away team
                estatisticas_golos[away_team] = estatisticas_golos.get(away_team, {'Jogos': 0, 'Golos Marcados': 0,
                                                                                   'Golos Sofridos': 0})
                estatisticas_golos[away_team]['Golos Marcados'] += golos_fora
                estatisticas_golos[away_team]['Golos Sofridos'] += golos_casa
                estatisticas_golos[away_team]['Jogos'] += 1

    # calculo golos medios marcado e sofrido e diferença de golos
    for team, stats in estatisticas_golos.items():
        stats['Diferença de Golos'] = stats['Golos Marcados'] - stats['Golos Sofridos']
        stats['Média Golos Marcados por Jogo'] = round(stats['Golos Marcados'] / stats['Jogos'], 2)
        stats['Média Golos Sofridos por Jogo'] = round(stats['Golos Sofridos'] / stats['Jogos'], 2)

    # Sort teams by goal difference in descending order
    sorted_teams = sorted(estatisticas_golos.items(), key=lambda x: -x[1]['Diferença de Golos'])

    # Create a list of dictionaries for team statistics
    team_statistics = [{'Equipa': team, **stats} for team, stats in sorted_teams]

    return team_statistics


estatisticas_golos = calcular_estatisticas_golos(corpus)
print(estatisticas_golos)


# Função para calcular a sequencia atual de vitorias de cada equipa
def sequencia_de_vitorias_atual(corpus):
    win_streaks = {}

    for jogo in corpus:
        home_team = jogo['Equipa da Casa']
        away_team = jogo['Equipa de Fora']
        resultado = jogo['Resultado do Jogo']

        if resultado != "---":
            # atualiza vitorias consecutivas para a equipa da casa
            win_streaks[home_team] = win_streaks.get(home_team, 0) + (1 if resultado[0] > resultado[2] else 0)
            # quebra a sequencia se a equipa perde
            win_streaks[home_team] *= (resultado[0] > resultado[2])

            # atualiza vitorias consecutivas para a equipa de fora
            win_streaks[away_team] = win_streaks.get(away_team, 0) + (1 if resultado[2] > resultado[0] else 0)
            # quebra a sequencia se a equipa perde
            win_streaks[away_team] *= (resultado[2] > resultado[0])

    # ordena as equipas por ordem decrescente de vitorias consecutivas atuais
    sorted_teams = sorted(win_streaks.items(), key=lambda x: -x[1])

    # retorna a lista de equipas e a sua sequencia de vitorias atual
    teams_with_win_streaks = [{'Equipa': team, 'Vitórias consecutivas atuais': max_win_streak} for team, max_win_streak
                              in sorted_teams]

    return teams_with_win_streaks


seq = sequencia_de_vitorias_atual(corpus)
print(seq)


# funçao que calcula os pontos por jornada
def calcular_pontos_por_jornada(corpus):
    pontos_por_jornada = {}
    jornada1 = 0

    for i, jogo in enumerate(corpus):
        home_team = jogo['Equipa da Casa']
        away_team = jogo['Equipa de Fora']
        resultado = jogo['Resultado do Jogo']

        if resultado == '---':
            continue

        # a cada 7 jogos começa uma nova jornada
        if i % 7 == 0:
            jornada1 += 1

        # Verifica se a equipe da casa venceu, perdeu ou empatou
        if resultado[0] > resultado[2]:
            pontos_casa = 3
            pontos_fora = 0
        elif resultado[0] < resultado[2]:
            pontos_casa = 0
            pontos_fora = 3
        else:
            pontos_casa = 1
            pontos_fora = 1

        jornada = f'Jornada {jornada1}'
        if jornada not in pontos_por_jornada:
            pontos_por_jornada[jornada] = {}
        # Atualiza os pontos para a equipe da casa
        if home_team not in pontos_por_jornada[jornada]:
            pontos_por_jornada[jornada][home_team] = 0
        pontos_por_jornada[jornada][home_team] += pontos_casa

        # Atualiza os pontos para a equipe de fora
        if away_team not in pontos_por_jornada[jornada]:
            pontos_por_jornada[jornada][away_team] = 0
        pontos_por_jornada[jornada][away_team] += pontos_fora

    return pontos_por_jornada


pontos_por_jornada = calcular_pontos_por_jornada(corpus)
print(pontos_por_jornada)




# passar os resultados da funçao anterior para data frame
df = pd.DataFrame(pontos_por_jornada).fillna(0)

# matriz transposta
df_transposed = df.T

# soma cumulativa das colunas
df_cumsum_columns = df_transposed.cumsum(axis=0)

# grafico da evolução da tabela classificativa
df_cumsum_columns.plot(kind='line', marker='o', figsize=(16, 8))
# plt.title('Evolução da Tabela Classificativa')
plt.xlabel('Jornada')
plt.ylabel('Pontos')
plt.legend(title='Equipas', bbox_to_anchor=(0, 1), loc='upper left')


#plt.show()

# guardar o plot como um png
plt.savefig('evolucao_tabela_classificativa.png')

# Converter os resultados para DataFrame
df_resultados = pd.DataFrame(resultados)
df_pontos_por_jornada = pd.DataFrame(pontos_por_jornada).fillna(0)
df_sequencia_vitorias = pd.DataFrame(seq)
df_classificacao = pd.DataFrame(team_classification_result)
df_golos = pd.DataFrame(estatisticas_golos)

# converter os urls dos logos em etiquetas html img
df_resultados['Emblema da Casa'] = df_resultados['Emblema da Casa'].apply(
    lambda x: f'<img src="{x}" height="40" width="40">' if x != 'N/A' else '')
df_resultados['Emblema de Fora'] = df_resultados['Emblema de Fora'].apply(
    lambda x: f'<img src="{x}" height="40" width="40">' if x != 'N/A' else '')


'''
# guardar os nomes de todas as equipas para permitir ao utilizador selecionar 
# uma equipa para o maximo de vitoriasa consecutivas
# Extract the team names from your data
team_names = set()
for jogo in corpus:
    home_team = jogo['Equipa da Casa']
    away_team = jogo['Equipa de Fora']
    team_names.add(home_team)
    team_names.add(away_team)

# Create a dropdown list with team names
team_dropdown_options = "\n".join(f"<option value='{team}'>{team}</option>" for team in sorted(team_names))
'''

'''
team_names = sorted(set(df_resultados['Equipa da Casa'].unique()) | set(df_resultados['Equipa de Fora'].unique()))
team_dropdown_options = "\n".join(f"<option value='{team}'>{team}</option>" for team in team_names)
print(team_names)

# adiciona um form com a lista para escolher a equipa para ver a sequencia de vitorias
html_content += "<h2>Selecionar Equipa para Maior Número de Vitórias Consecutivas</h2>\n"
html_content += """
<form action="" method="get">
  <label for="equipa_alvo">Escolha a equipa:</label>
  <select id="equipa_alvo" name="equipa_alvo">
    {team_options}
  </select>
  <input type="submit" value="Selecionar">
</form>
""".format(team_options=team_dropdown_options)


# selecionar se o form foi submitdo e atualiza a equipa escolhida
if 'equipa_alvo' in request.args:
    equipa_alvo = request.args['equipa_alvo']

# update da equipa na funçao calcular_maior_numero_vitorias_consecutivas
maior_numero_vitorias, jogos_da_sequencia = calcular_maior_numero_vitorias_consecutivas(corpus, equipa_alvo)

# mostrar a informação para essa equipa
html_content += f"<h2>Maior Número de Vitórias Consecutivas</h2>\n"
html_content += f"<p>O maior número de vitórias consecutivas de {equipa_alvo} é: {maior_numero_vitorias}</p>\n"
'''

# Criar uma estrutura HTML usando BeautifulSoup
html_content = f"""
<html>
<head>
    <title>Campeonato Nacional de Hóquei em Patins</title>
    <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <h1>Campeonato Nacional de Hóquei em Patins</h1>
    <!-- unordered list com as list items com as opções e cada opção tem um link <a> -->
    <ul>
        <li><a href="javascript:void(0);" onclick="showSection('resultados')">Resultados</a></li>
        <li><a href="javascript:void(0);" onclick="showSection('classificacao')">Classificação</a></li>
        <li><a href="javascript:void(0);" onclick="showSection('evolucao')">Evolução da Tabela Classificativa</a></li>
        <li><a href="javascript:void(0);" onclick="showSection('golos')">Golos</a></li>
        <li><a href="javascript:void(0);" onclick="showSection('sequencia')">Sequência de Vitórias Atuais</a></li>
    </ul>

    <!--hidden para estarem escondidas incialmente-->
    <div id="resultados" class="hidden">
        <h2>Resultados</h2>
        {df_resultados.to_html(index=False, escape=False, render_links=True)}
    </div>

    <div id="evolucao" class="hidden">
        <h2>Evolução da Tabela Classificativa</h2>
        <img src="evolucao_tabela_classificativa.png" alt="Evolução da Tabela Classificativa" width="1600" height="800">
    </div>

    <div id="classificacao" class="hidden">
        <h2>Classificação</h2>
        {df_classificacao.to_html(index=False, escape=False)}
    </div>

    <div id="golos" class="hidden">
        <h2>Golos</h2>
        {df_golos.to_html(index=False, escape=False)}
    </div>

    <div id="sequencia" class="hidden">
        <h2>Sequência de Vitórias</h2>
        {df_sequencia_vitorias.to_html(index=False, escape=False)}
    </div>

    <!--Esta função é chamada quando um link é selecionado e recebe o sectionId,
    que representa o ID da seção a ser mostrada. -->
    <script>

        function showSection(sectionId) {{
            //esta função obtém o elemento HTML com o ID especificado
            var section = document.getElementById(sectionId);

            //se a secção existe:
            if (section) {{
                // esconde todas as secções
                var sections = document.querySelectorAll('.hidden');
                sections.forEach(function (sec) {{
                    sec.style.display = 'none';
                }});

                // mostra so a secção selecionada
                section.style.display = 'block';
            }}
        }}
    </script>
</body>
</html>
"""


with open('Campeonato Nacional de Hóquei em Patins.html', 'w') as html_file:
    html_file.write(html_content)