"""Fluxo Principal do programa

    Returns:
        _type_: Controla a execução principal
    """

import json
import os
import requests

from flask import Flask, render_template, request
from dotenv import load_dotenv


class ClassificacaoApp:
    """Classe principal
    """

    def __init__(self):
        # Carregar variáveis de ambiente
        load_dotenv()

        # Configurando diretórios de templates e estáticos
        self.template_folder = 'views'
        self.static_folder = 'assets'

        # Caminho para o arquivo JSON de classificação
        self.json_file_path = os.path.join('resources', 'classificacao.json')

        # Inicializar a aplicação Flask
        self.app = Flask(__name__, template_folder=self.template_folder,
                         static_folder=self.static_folder, static_url_path='/assets')

        # Configurar rotas
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/tabela', 'mostrar_tabela', self.mostrar_tabela)
        self.app.add_url_rule('/predicao', 'predicao',
                              self.predicao, methods=['GET', 'POST'])

    def predicao(self):
        """Renderiza a previsão de partidas chamando a API GraphQL."""
        mandante = request.form.get('mandante')
        visitante = request.form.get('visitante')
        pos_mandante = request.form.get('posMandante')
        pos_visitante = request.form.get('posVisitante')

        # Verifica se todos os parâmetros necessários estão presentes
        if not mandante or not visitante or not pos_mandante or not pos_visitante:
            classificacao = self.carregar_dados_classificacao()
            # print("Classificação 1", classificacao)
            return render_template('index.html', show_modal=False,
                                   resultado="Você Ainda não previu nada.", classificacao=classificacao)

        query = f'''
        query {{
            predictMatch(mandante: "{mandante}", visitante: "{visitante}",
            posMandante: {pos_mandante}, posVisitante: {pos_visitante})
        }}
        '''

        try:
            # Enviar a requisição para o GraphQl
            response = requests.post(
                url=os.getenv("BACKENDURL"),
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=320
            )

            response.raise_for_status()
            data = response.json()
            # print("Requestdata", data)
            resultado = data.get('data', {}).get('predictMatch')

        except requests.RequestException as e:
            print(f"Erro ao buscar dados do back-end: {e}")
            resultado = "Erro ao buscar dados do back-end."

        # Recupera o JSON para popular os Lists da tela de predição
        classificacao = self.carregar_dados_classificacao()
        # print("Classificação", classificacao)

        return render_template('index.html', show_modal=False,
                               classificacao=classificacao, resultado=resultado)

    def carregar_dados_classificacao(self):
        """Carrega os dados de classificação de um arquivo JSON.

        Returns:
            list: Uma lista de dicionários contendo a classificação.
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                dados = json.load(file)
            return dados
        except FileNotFoundError:
            print(f"Erro: O arquivo JSON não foi encontrado: {
                  self.json_file_path}")
            return []  # Retorna uma lista vazia em caso de erro
        except json.JSONDecodeError:
            print("Erro: O arquivo JSON está mal formatado.")
            return []  # Retorna uma lista vazia em caso de erro
        except OSError as e:
            print(f"Erro ao ler o arquivo JSON: {e}")
            return []  # Retorna uma lista vazia em caso de erro

    def index(self):
        """Renderiza a página inicial.

        Retorna:
            str: O template da página inicial (index.html).
        """
        return render_template("index.html", show_modal=False)

    def mostrar_tabela(self):
        """Renderiza o modal de classificação
        Purpose: mantem o modal oculto até que a rota seja chamada e seja true
        """
        classificacao = self.carregar_dados_classificacao()
        return render_template('index.html', show_modal=True, classificacao=classificacao)


# Executar a aplicação
if __name__ == '__main__':
    app = ClassificacaoApp()
    app.app.run(debug=True, port=5001)
