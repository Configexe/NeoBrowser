import requests
from bs4 import BeautifulSoup
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input
from textual.containers import ScrollableContainer

class TerminalBrowser(App):

    CSS_PATH = "terminal_browser.css"
    BINDINGS = [("q", "quit", "Sair")]

    def compose(self) -> ComposeResult: #Cria os widgets da interface.
        yield Header(name="Navegador de Terminal")
        yield Input(placeholder="Digite uma URL e pressione Enter", id="url_input")
        with ScrollableContainer(id="content_display"):
            yield Static("Bem-vindo ao navegador de terminal!", id="content")
        yield Footer()

    def on_mount(self) -> None:
        #Foca no campo de entrada ao iniciar.
        self.query_one("#url_input").focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        #Busca e exibe o conteúdo da URL quando o Enter é pressionado.
        url = event.value
        content_widget = self.query_one("#content", Static)
        content_widget.update("Carregando...")

        try:
            # Garante que a URL tenha um esquema
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url

            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Lança um erro para códigos de status ruins

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extrai e formata o conteúdo
            title = soup.title.string if soup.title else "Sem título"
            page_content = f"[bold]{title}[/bold]\n\n"
            
            self.links = []
            for i, link in enumerate(soup.find_all('a', href=True)):
                link_text = link.get_text(strip=True)
                link_url = link['href']
                if link_text and link_url:
                    page_content += f"[{i+1}] {link_text}\n"
                    self.links.append(link_url)
            
            # Adiciona uma forma de navegar pelos links
            page_content += "\n\n[bold]Digite o número de um link para navegar ou uma nova URL.[/bold]"

            content_widget.update(page_content)

        except requests.RequestException as e:
            content_widget.update(f"Erro ao carregar a URL: {e}")
        except Exception as e:
            content_widget.update(f"Ocorreu um erro inesperado: {e}")
        
        # Limpa o input e foca para a próxima entrada
        url_input = self.query_one("#url_input", Input)
        url_input.value = ""
        url_input.focus()

        # Lógica para navegação por número
        self.query_one("#url_input").validate_on = [] # Permite entrada de números
        async def handle_link_navigation(event: Input.Submitted):
            try:
                link_number = int(event.value)
                if 1 <= link_number <= len(self.links):
                    new_url = self.links[link_number - 1]
                    # Constrói URL absoluta se for relativa
                    from urllib.parse import urljoin
                    base_url = response.url
                    absolute_url = urljoin(base_url, new_url)
                    
                    # Simula um novo submit com a URL do link
                    new_event = Input.Submitted(self.query_one("#url_input"))
                    new_event.value = absolute_url
                    await self.on_input_submitted(new_event)
            except ValueError:
                 # Se não for um número, assume que é uma nova URL
                await self.on_input_submitted(event)
            except IndexError:
                content_widget.update("Número do link inválido.")

        self.query_one("#url_input")._on_input_submitted = handle_link_navigation


if __name__ == "__main__":
    app = TerminalBrowser()
    app.run()