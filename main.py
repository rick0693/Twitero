from datetime import datetime
from time import sleep
import sqlite3
import google.generativeai as genai
import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(
    page_title="Consulta_SSW",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)



# Função para a página de Notícias
def Coleta_Dados():

    # Layout
    col1, col2, col3, col4 = st.columns(4)
    Twiter_postado = col1.empty()  # Indicação
    Noticia = col2.empty()  # Derrotas
    Noticia2 = col3.empty()  # Vitorias
    Noticia3 = col4.empty()  # Resultado da aposta anterior

    ganho_hora = st.empty()

    # Expander para o DataFrame
    with st.expander("Exibir DataFrame"):
        df_expander = st.empty()

    # Expander para o restante do código
    with st.expander("Configurações e Log"):
        log_expander = st.empty()

    # Classe do Scraper
    class CanalTechScraper:
        def __init__(self, db_file):
            self.db_file = db_file
            self.create_table()

        def create_table(self):
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS canaltech (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT,
                    categoria TEXT,
                    link_site TEXT UNIQUE,
                    creditos TEXT,
                    data TEXT,
                    url_imagem TEXT,
                    xtwiter TEXT,
                    instagram TEXT,
                    facebook TEXT,
                    threads TEXT,
                    vazio1 TEXT,
                    vazio2 TEXT,
                    vazio3 TEXT,
                    vazio4 TEXT
                )
            ''')

            conn.commit()
            conn.close()

        def get_column_names(self):
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(canaltech)")
            columns = [col[1] for col in cursor.fetchall()]
            conn.close()
            return columns

        def check_duplicate(self, link_site):
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM canaltech WHERE link_site = ?', (link_site,))
            count = cursor.fetchone()[0]

            conn.close()

            return count > 0

        def insert_data(self, data):
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            try:
                link_site = data[2]

                # Verifica se o link já existe no banco de dados
                if self.check_duplicate(link_site):
                    log_expander.write(f"O link já existe no banco de dados: {link_site}")
                    return f"O link já existe no banco de dados: {link_site}"

                # Se o link não existir, então podemos inseri-lo
                cursor.execute('''
                    INSERT INTO canaltech (
                        titulo, categoria, link_site, creditos, data,
                        url_imagem, xtwiter, instagram, facebook, threads,
                        vazio1, vazio2, vazio3, vazio4
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)

                conn.commit()
                log_expander.write(f"Registro inserido com sucesso para o link: {link_site}")
                return f"Registro inserido com sucesso para o link: {link_site}"

            except Exception as e:
                log_expander.write(f"Erro ao inserir dados: {str(e)}")

            finally:
                # Garante que o fechamento da conexão ocorra mesmo se houver uma exceção
                conn.close()
    fontes_urls = {
        "mais-lidas": "https://canaltech.com.br/mais-lidas/",
        "smartphone": "https://canaltech.com.br/smartphone/",
        "tutoriais": "https://canaltech.com.br/tutoriais/",
        "apps": "https://canaltech.com.br/apps/",
        "analises": "https://canaltech.com.br/analises/",
        "entretenimento": "https://canaltech.com.br/entretenimento/",
        "games": "https://canaltech.com.br/games/",
        "ctup": "https://canaltech.com.br/ctup/",
        "ciencia": "https://canaltech.com.br/ciencia/",
        "espaco": "https://canaltech.com.br/espaco/",
        "eventos": "https://canaltech.com.br/eventos/",
        "seguranca": "https://canaltech.com.br/seguranca/",
        "webstories": "https://canaltech.com.br/webstories/"
    }


    def main():
        st.title("CanalTech Scraper")

        # Conectar ao banco de dados
        canaltech_scraper = CanalTechScraper("Noticias.db")

        # Campo de entrada para o intervalo de tempo (em segundos)
        intervalo_tempo = st.number_input("Intervalo de tempo entre raspagens (segundos)", value=30)

        # Definir as colunas desejadas e permitir a renomeação
        colunas = st.multiselect("Selecione as colunas desejadas", ["titulo", "categoria", "link_site", "data", "conteudo"])

        # Botão para iniciar o scraper
        if st.button("Realizar Raspagem"):
            log_expander.write("Raspagem em andamento!")  # Adiciona um log indicando que a raspagem está em andamento

            # Cria uma lista vazia para armazenar os dados
            data_list = []

            # Loop sobre as páginas
            for source, base_url in fontes_urls.items():
                for page in range(1, 3):  # assumindo um máximo de 10 páginas
                    url = f"{base_url}p/{page}/"
                    response = requests.get(url)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')

                        articles = soup.find_all('article', class_='c-fbeGQw')

                        for article in articles:
                            link = article.find('a')['href']
                            time_read = article.find('span', class_='c-fePzow').text
                            category = article.find('span', class_='c-fdwzOI').text
                            title = article.find('h3', class_='c-kVPmWV').text

                            target_selector = '#NewsContainer > section > div > div:nth-child(3) > div > article:nth-child(6) > a > div.c-bzdKoz > span.c-fePzow'
                            target_element = article.select_one(target_selector)

                            if target_element:
                                data_value = target_element.text.strip()
                            else:
                                data_value = "N/A"

                            response = requests.get(link)
                            html_content = response.content
                            soup = BeautifulSoup(html_content, 'html.parser')
                            paragrafos = soup.find_all('p')
                            textos = [paragrafo.get_text() for paragrafo in paragrafos]

                            textos_acumulados = []
                            for i, texto in enumerate(textos):
                                if i == 0 or i == 1:
                                    continue
                                textos_acumulados.append(texto)

                            # Seleciona apenas as colunas desejadas
                            data = (
                                title, category, link, data_value, "\n".join(textos_acumulados)
                            )

                            # Renomeia as colunas conforme especificado pelo usuário
                            data_dict = {col: val for col, val in zip(["titulo", "categoria", "link_site", "data", "conteudo"], data)}

                            # Verifica se já existe no banco de dados
                            result = canaltech_scraper.insert_data(tuple(data_dict.values()))

                            # Aguarda o intervalo de tempo especificado antes de realizar a próxima raspagem
                            time.sleep(intervalo_tempo)

                            # Adiciona dados à lista
                            data_list.append(data_dict)

                            # Atualiza o DataFrame e exibe em tempo real
                            df = pd.DataFrame(data_list, columns=colunas)
                            df_expander.dataframe(df)

            # Limpa a barra de progresso no final da raspagem
            log_expander.write("Raspagem concluída!")

    # Executa o Streamlit
    if __name__ == "__main__":
        main()

    

# Função para a página de Dados
def bot_final_page():
    postagem = st.empty()


    def postar_no_twitter(tweet1, tweet2, cookies, headers, json_data):
        response = requests.post(
            'https://twitter.com/i/api/graphql/hYwT63a8BTYDoMqnDUQxxg/CreateTweet',
            cookies=cookies,
            headers=headers,
            json=json_data,
        )
        return response.json()

    def oprnt(noticia):
        # Configurar a chave API do Gemini
        genai.configure(api_key="AIzaSyCMzZgpHBsJhRYoyH3SWGdQT-3qU6zMKW8")

        # Configurar o modelo Gemini
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
        }

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config,
            safety_settings=safety_settings,
        )

        # Construir o prompt com base na notícia
        prompt = f"Resuma a seguinte notícia para o Twitter em dois tweets, cada um com no máximo 140 caracteres. Use palavras-chave impactantes e inclua elementos visuais e sempre #para que possa impulsionar se possível. Não ultrapasse o limite de caracteres por Twiter\n\n{noticia}"

        # Gerar conteúdo usando o modelo Gemini
        response = model.generate_content([prompt])

        # Esperar por 1 segundo antes de obter o texto da resposta
        time.sleep(1)

        try:
            text_parts = response.text.split('\n\n')
            tweet1 = text_parts[0]
            tweet2 = text_parts[1] if len(text_parts) > 1 else ""

            # Verificar se há pelo menos dois elementos antes de acessar o índice 1
            if len(text_parts) > 1:
                # Verificar se há pelo menos dois elementos antes de dividir a string
                tweet2 = tweet2.split(' ', 1)[1] if len(tweet2.split(' ', 1)) > 1 else ""

            return tweet1, tweet2
        except IndexError:
            # Tratar o erro de índice fora da faixa
            #print("Erro ao extrair tweets da resposta do modelo.")
            return "", ""

    # Função para realizar a raspagem e postagem no Twitter
    def realizar_raspagem_e_postar_twitter():
        # Conectar ao banco de dados
        conn = sqlite3.connect('Noticias.db')
        cursor = conn.cursor()

        # Selecionar os textos da coluna 'url_imagem' da tabela 'canaltech'
        cursor.execute('SELECT url_imagem FROM canaltech')
        noticias = cursor.fetchall()

        for noticia in noticias:
            if noticia[0] is not None and noticia[0] != 'N/A':
                # Verificar se a notícia já foi postada
                cursor.execute('SELECT xtwiter FROM canaltech WHERE url_imagem = ?', (noticia[0],))
                result = cursor.fetchone()

                # Se xtwiter já tiver 'Twitter postado', pular para a próxima notícia
                if result and result[0] == 'Twitter postado':
                    #print(f"Notícia já postada. Pulando para a próxima.")
                    continue

                tweet1, tweet2 = oprnt(noticia[0])

                # Verificar se ambos os tweets foram gerados
                if tweet1 and tweet2:
                    # Remover números do início dos tweets
                    tweet1 = tweet1.split(' ', 1)[1]
                    tweet2 = tweet2.split(' ', 1)[1]

                    # Imprimir os tweets formatados
                    #print(f"Tweet 1: {tweet1}")
                    #print(f"Tweet 2: {tweet2}")



                # Adicione os tweets ao DataFrame
                df_tweet = pd.DataFrame({
                    "Tweet 1": [tweet1],
                    "Tweet 2": [tweet2]
                })

                # Concatene o DataFrame com o DataFrame existente, se houver
                if 'df' in locals():
                    df = pd.concat([df, df_tweet], ignore_index=True)
                else:
                    df = df_tweet

                # Exiba o DataFrame usando Streamlit
                postagem.dataframe(df)

                cookies = {
                    '_ga': 'GA1.2.544235166.1701825735',
                    'g_state': '{"i_l":0}',
                    'kdt': 'TTuIFnRmiOZSJVbOTgzr5vC4MEkd9gNmtHV9qVFq',
                    'dnt': '1',
                    'guest_id': 'v1%3A170234031992733387',
                    'guest_id_marketing': 'v1%3A170234031992733387',
                    'guest_id_ads': 'v1%3A170234031992733387',
                    'auth_token': 'f6d91c03b803462f93a4a12f010a4abc5f903e51',
                    'ct0': 'b4e1f2058ee092c1ecc614f8f356f8cd0af88257542f385afd308441c6808040d1419782b044d9e49d5eb0743ce825fe963362de780ae96a097390f81c5c93bc6911ba07ec43e47e0bc1512024bca9f0',
                    'twid': 'u%3D720780782',
                    'lang': 'pt',
                    '_gid': 'GA1.2.2083020449.1702520061',
                    'personalization_id': '"v1_MHCBDYffghnqVeqFb981Xg=="',
                }

                headers = {
                    'authority': 'twitter.com',
                    'accept': '*/*',
                    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                    'content-type': 'application/json',
                    'origin': 'https://twitter.com',
                    'referer': 'https://twitter.com/compose/tweet',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'sec-gpc': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'x-client-transaction-id': 'WY5YOqm+qxnwwkvXbVe9QKEINFucrAwMXR4M/Pc9xKjvA/UWbEfnHvs8/XpbD/pwlSpfclh52xzJ8r6CK3Oz39NOFrp6WA',
                    'x-csrf-token': 'b4e1f2058ee092c1ecc614f8f356f8cd0af88257542f385afd308441c6808040d1419782b044d9e49d5eb0743ce825fe963362de780ae96a097390f81c5c93bc6911ba07ec43e47e0bc1512024bca9f0',
                    'x-twitter-active-user': 'yes',
                    'x-twitter-auth-type': 'OAuth2Session',
                    'x-twitter-client-language': 'pt',
                }

                json_data = {
                    'variables': {
                        'tweet_text': tweet1,
                        'dark_request': False,
                        'media': {
                            'media_entities': [],
                            'possibly_sensitive': False,
                        },
                        'semantic_annotation_ids': [],
                    },
                    'features': {
                        'c9s_tweet_anatomy_moderator_badge_enabled': True,
                        'tweetypie_unmention_optimization_enabled': True,
                        'responsive_web_edit_tweet_api_enabled': True,
                        'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                        'view_counts_everywhere_api_enabled': True,
                        'longform_notetweets_consumption_enabled': True,
                        'responsive_web_twitter_article_tweet_consumption_enabled': False,
                        'tweet_awards_web_tipping_enabled': False,
                        'responsive_web_home_pinned_timelines_enabled': True,
                        'longform_notetweets_rich_text_read_enabled': True,
                        'longform_notetweets_inline_media_enabled': True,
                        'responsive_web_graphql_exclude_directive_enabled': True,
                        'verified_phone_label_enabled': False,
                        'freedom_of_speech_not_reach_fetch_enabled': True,
                        'standardized_nudges_misinfo': True,
                        'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                        'responsive_web_media_download_video_enabled': False,
                        'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                        'responsive_web_graphql_timeline_navigation_enabled': True,
                        'responsive_web_enhance_cards_enabled': False,
                    },
                    'queryId': 'hYwT63a8BTYDoMqnDUQxxg',
                }
                response_data = postar_no_twitter(tweet1, tweet2, cookies, headers, json_data)

                # Verifica se a chave 'data' existe na resposta
                if 'data' in response_data:
                    # Acesse 'rest_id' se estiver presente
                    rest_id = response_data['data'].get('create_tweet', {}).get('tweet_results', {}).get('result', {}).get('rest_id', '')

                    #print(f"rest_id: {rest_id}")

                    json_data_resposta = {
                        'variables': {
                            'tweet_text': tweet2,
                            'reply': {
                                'in_reply_to_tweet_id': rest_id,
                                'exclude_reply_user_ids': [],
                            },
                            'batch_compose': 'BatchSubsequent',
                            'dark_request': False,
                            'media': {
                                'media_entities': [],
                                'possibly_sensitive': False,
                            },
                            'semantic_annotation_ids': [],
                        },
                        'features': {
                            'c9s_tweet_anatomy_moderator_badge_enabled': True,
                            'tweetypie_unmention_optimization_enabled': True,
                            'responsive_web_edit_tweet_api_enabled': True,
                            'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                            'view_counts_everywhere_api_enabled': True,
                            'longform_notetweets_consumption_enabled': True,
                            'responsive_web_twitter_article_tweet_consumption_enabled': False,
                            'tweet_awards_web_tipping_enabled': False,
                            'responsive_web_home_pinned_timelines_enabled': True,
                            'longform_notetweets_rich_text_read_enabled': True,
                            'longform_notetweets_inline_media_enabled': True,
                            'responsive_web_graphql_exclude_directive_enabled': True,
                            'verified_phone_label_enabled': False,
                            'freedom_of_speech_not_reach_fetch_enabled': True,
                            'standardized_nudges_misinfo': True,
                            'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                            'responsive_web_media_download_video_enabled': False,
                            'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                            'responsive_web_graphql_timeline_navigation_enabled': True,
                            'responsive_web_enhance_cards_enabled': False,
                        },
                        'queryId': 'hYwT63a8BTYDoMqnDUQxxg',
                    }

                    response = requests.post(
                        'https://twitter.com/i/api/graphql/hYwT63a8BTYDoMqnDUQxxg/CreateTweet',
                        cookies=cookies,
                        headers=headers,
                        json=json_data_resposta,
                    )
                    # Atualizar a coluna 'xtwiter' no banco de dados
                    cursor.execute('UPDATE canaltech SET xtwiter = ? WHERE url_imagem = ?', ('Twitter postado', noticia[0]))
                    conn.commit()
                else:
                    st.toast("Erro ao extrair tweets da resposta do modelo. Pulando para a próxima notícia.")

        # Fechar a conexão com o banco de dados
        conn.close()

    # Implementação do aplicativo Streamlit
    def main():
        st.title("Streamlit App para Raspagem e Postagem no Twitter")

        # Botão para iniciar a raspagem e postagem no Twitter
        if st.button("Iniciar Raspagem e Postagem no Twitter"):
            st.write("Botão pressionado!")  # Adiciona um log indicando que o botão foi pressionado

            # Chamada da função para realizar a raspagem e postagem no Twitter
            realizar_raspagem_e_postar_twitter()

    # Executa o Streamlit
    if __name__ == "__main__":
        main()


pages = {
    "Upload de dados": Coleta_Dados,
    "Atualizar plataforma": bot_final_page  

}

# Barra de navegação com as tabs
selected_page = st.sidebar.radio("Selecione uma página", list(pages.keys()))

# Exibir a página selecionada
pages[selected_page]()


