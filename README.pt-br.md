# ⛽ Canteiros Analytics (Smart Stock Control)

🇺🇸 [English](README.md) | 🇧🇷 Português

---

## 🇧🇷 Português

### 📌 Sobre o Projeto

O **Canteiros Analytics** é um sistema de automação e integração de dados (ETL) desenvolvido para modernizar o controle de estoque de um posto de combustíveis (Posto Canteiros).

**O Problema:** Anteriormente, a conferência de produtos (filtros, óleos, aditivos) era feita de forma manual através da leitura linha por linha de relatórios em PDF gerados pelo sistema legado, um processo demorado e suscetível a erros humanos.
**A Solução:** Este projeto automatiza a extração diária dos dados de estoque diretamente do sistema web do posto, limpa e organiza as informações, e as armazena em um banco de dados relacional estruturado. O objetivo final é criar uma inteligência de negócio que dispare alertas automatizados quando produtos atingirem o estoque mínimo.

### 🚀 Status Atual do Projeto

**Em desenvolvimento (Fase 2 de 3 concluída).**

- [x] **Fase 1:** Automação de Login e Navegação no sistema legado web.
- [x] **Fase 2:** Parsing de HTML complexo (tratamento de respostas AJAX/ExtJS escapadas) e persistência de dados em Banco SQL.
- [ ] **Fase 3 (Próximos Passos):** Implementação das regras de negócio estruturadas (tratamento de "Data Drift", reaproveitamento de códigos de produtos, Inativação Lógica/Soft Delete) e sistema de alertas.

### 🛠️ Tecnologias Utilizadas

- **Python 3:** Linguagem principal do projeto.
- **Playwright:** Utilizado para automação web, preenchimento de formulários de login e navegação no sistema do posto.
- **BeautifulSoup4 (bs4):** Responsável por ler e extrair os dados da resposta embutida do sistema (limpeza de caracteres de escape e extração de tags HTML).
- **SQLite3:** Banco de dados relacional leve nativo do Python, utilizado para manter o histórico diário (snapshots) do estoque e informações de cada produto.
- **python-dotenv:** Gerenciamento seguro de credenciais e variáveis de ambiente.
