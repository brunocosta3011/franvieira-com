# Esquenta Black Friday 23/11 — modo campanha na home

> **Status:** Mockup C aprovado em 12/11/2026. T-01 a T-05 executadas (capturas em `assets/esquenta-black-friday/prints/`). Faltam T-06 (publicar e conferir no ar) e T-07 (remover a campanha a partir de 24/11/2026). Premissas P1 a P4 seguem como assumidas.
> **Repo:** `franvieira-com` (site estático: HTML + CSS + JS puro, sem build, sem testes automatizados, sem `package.json`).
> **Nota sobre convenções:** a skill `gestao3d-conventions` descreve o app Angular/FastAPI de gestão de cortadores e **não se aplica** a este repo (não há `DataService`, `_tokens.scss` nem `docs/`). A fonte da verdade visual aqui é `home.css` (tokens em `home.css:3-14`). Skills carregadas: `gestao3d-conventions` (lida e descartada por não se aplicar), `writing-plans`, `senior-architect`, `frontend-design`.

## Entendi

Durante a campanha, a home deve **ocultar** o Destaque "Comunidade do Aplique", o cartão "Curso" e o cartão "Mentoria" (as duas caixas vermelhas do print) e mostrar **um cartão novo, comum (não destaque)**, "Esquenta Black Friday 23/11", cujo clique abre o grupo do WhatsApp. Isso vale **só até 23/11**; depois a home volta ao normal. Quero poder **validar a versão alternativa** antes e depois voltar ao normal sem retrabalho.

## Fase 1 — Enquadramento

- **Problema real:** nos dias da campanha, a primeira dobra da home empurra para a Comunidade, o Curso e a Mentoria, e não para o grupo de ofertas do WhatsApp, que é o objetivo da campanha. Depois do dia 23/11, o grupo deixa de ser prioridade e tudo precisa voltar a ser como era, sem alguém lembrar de mexer.
- **Resultado esperado:** até 23/11 23:59 (Brasília) a home mostra Instagram → Esquenta → Loja → Catálogo → Encomendas. A partir de 24/11 00:00 mostra a home de hoje, sem deploy.
- **Tipo:** feature temporária (campanha) com auto-reversão.
- **Camadas:** UI (HTML/CSS/JS da home). Sem API, sem dados, sem infra.
- **Fora de escopo:** alterar `/comunidade-aplique/`, `/temas/`, `/linktree/`; trocar link do Curso/Mentoria; criar imagem nova; analytics; contagem regressiva.

## Fase 2 — Mapa do código

- `index.html:17` — carrega `home.css`. Só a home usa esse CSS (`home.css:1`), então não afeta as outras páginas.
- `index.html:40-53` — `#btn-comunidade.estrela` (o Destaque). Hoje aponta para `https://comunidadedoaplique.lovable.app/` (revertido em `ace0feb`).
- `index.html:55-65` — `#btn-curso.cartao.c-curso` (preço de/por R$ 397,00 → R$ 147,90, link Hotmart).
- `index.html:67-76` — `#btn-mentoria.cartao.cartao--inv.c-mentoria`.
- `index.html:78-106` — Loja, Catálogo e Encomendas: **permanecem visíveis** em ambos os modos.
- `home.css:48-57` — molde `.cartao` (reutilizável para o cartão novo). `home.css:58-69` — variantes por cor (`.c-*`). `home.css:72-82` — `.estrela` e `.selo-estrela` (não reutilizar: é o visual de Destaque que o pedido manda abandonar).
- `index.html:113` / `global.js:74-79` — `global.js` é **compartilhado com outras páginas** (scroll reveal, contadores, ano no rodapé). Não colocar lógica da campanha nele.
- `assets/home/comunidade.webp` — única ilustração de comunidade/WhatsApp disponível; o cartão novo a reutiliza (premissa P3).
- **Padrão análogo:** não existe lógica por data no repo. É padrão novo, introduzido de forma isolada (arquivo próprio) para ser fácil de apagar.
- **Testes existentes:** nenhum. A verificação é por script `node` (lógica de data) e por captura de tela com Chrome headless.
- **Armadilha 1:** a data vem do relógio do aparelho do visitante. Aparelho com data errada vê o modo errado (aceito; ver risco R1).
- **Armadilha 2:** esconder só com CSS por data exigiria JS no `<head>` para não piscar o conteúdo antigo; por isso o script entra no `<head>`, síncrono e minúsculo.
- **Hospedagem/deploy:** `[NÃO VERIFICADO]` — o remoto é `github.com/brunocosta3011/franvieira-com`, mas não sei como o site é publicado. Ver T-06.

## Fase 3 — Decisões

Sem bloqueios técnicos. Premissas assumidas (`[PREMISSA — CONFIRMAR]`):

- **P1.** "Ocultar estes itens" = os 3 itens dentro das caixas vermelhas do print: Destaque Comunidade, Curso e Mentoria. Instagram, Loja, Catálogo e Encomendas ficam.
- **P2.** "Até dia 23/11" = a campanha vale **durante todo o dia 23/11**; volta ao normal em 24/11 00:00, horário de Brasília. Sem data de início: ativa assim que for publicada.
- **P3.** Textos novos (o título é o que você pediu): etiqueta **"Black Friday"**, descrição **"Entre no grupo do WhatsApp e receba as ofertas em primeira mão."** (varia por mockup), imagem reutilizada `comunidade.webp`, posição **no topo** da lista (onde estava o Destaque), `target="_blank"` e `rel="noopener noreferrer"` como os demais.
- **P4.** Link: `https://chat.whatsapp.com/H1OACRw221B6r26wp1b9KZ?s=cl&p=a&iam=2` (o mesmo que você passou antes; no HTML o `&` vira `&amp;`).

## Fase 4 — Como ocultar e voltar ao normal

### Opção A — Trocar o HTML na mão (comentar blocos e restaurar depois)
Ganha: zero JavaScript, zero risco de lógica. Custa: depende de alguém lembrar de reverter no dia 24/11 e de publicar de novo. Reversível: sim, mas só com outro commit.

### Opção B — Dois conjuntos de cartões no HTML, alternados por data via JS no `<head>` (**recomendada**)
Como funciona: o HTML mantém os 3 cartões antigos (marcados `oculta-campanha`) e o cartão novo (marcado `so-campanha`, escondido por padrão). Um script minúsculo no `<head>` adiciona a classe `modo-campanha` em `<html>` quando `agora < 24/11/2026 00:00 -03:00`. O CSS faz o resto. Parâmetro `?modo=campanha` / `?modo=normal` na URL força um modo para validar a versão alternativa a qualquer momento.
Ganha: volta ao normal sozinha, previsível em preview, sem piscar, fallback seguro (sem JS = home normal). Custa: ~25 linhas de JS e algumas regras de CSS temporárias que depois devem ser removidas. Reversível: apagar o bloco novo e o script.

### Opção C — Página alternativa `index-campanha.html` e troca do arquivo no dia
Ganha: validação isolada e sem JS na home. Custa: duas homes para manter, link divulgado (`/`) só muda com renomeação manual, e a volta também depende de alguém lembrar.

### Recomendação: **B**
Porque: o pedido tem um prazo rígido e o risco real é esquecer de reverter. B é a única que reverte sozinha e ainda permite validar o modo alternativo antes (com `?modo=campanha`).

## Fase 4.5 — Mockups (obrigatório)

Visualização lado a lado: [`mockups/comparar.html`](assets/esquenta-black-friday/mockups/comparar.html) · captura: [`prints/comparar.png`](assets/esquenta-black-friday/prints/comparar.png)

Todos mostram o **estado campanha**, com o mesmo conteúdo e o mesmo conjunto de cartões. Usam os tokens reais do `home.css`; o cartão novo é **proposta**.

### Mockup A — Cartão padrão dourado
- **Visual:** [mockup-A.html](assets/esquenta-black-friday/mockups/mockup-A.html)
- **Hipótese de usabilidade:** o cartão parece mais um da lista e a pessoa o entende pelo mesmo padrão que já conhece (etiqueta, título, texto, imagem).
- **Ponto forte:** menor risco e menor CSS novo; reaproveita `.cartao`.
- **Trade-off:** pode passar despercebido entre os demais, já que o objetivo da campanha é levar ao grupo.

### Mockup B — Data em destaque + chamada "Entrar no grupo ›"
- **Visual:** [mockup-B.html](assets/esquenta-black-friday/mockups/mockup-B.html)
- **Hipótese de usabilidade:** o bloco "23 NOV" cria urgência de calendário e a linha "Entrar no grupo ›" deixa clara a ação.
- **Ponto forte:** destaca sem usar o selo de Destaque; a ação fica explícita.
- **Trade-off:** o texto rosa `--pink-500` de 14px sobre fundo claro tem contraste abaixo de AA (~3,4:1); na implementação usar `--navy-700` no texto e deixar só a seta rosa.

### Mockup C — Cartão escuro "Black"
- **Visual:** [mockup-C.html](assets/esquenta-black-friday/mockups/mockup-C.html)
- **Hipótese de usabilidade:** o contraste escuro faz o olho parar no cartão, e o botão rosa é o único elemento de ação forte.
- **Ponto forte:** mais impacto visual e combina com o tema "Black".
- **Trade-off:** sai do tom pastel da home e pode parecer um "novo destaque"; a imagem pastel precisa de um círculo claro atrás para funcionar no fundo navy.

### Comparação
| Critério | A | B | C |
|---|---|---|---|
| Clareza da ação principal | Média: o cartão inteiro é o link | Alta: "Entrar no grupo ›" | Alta: botão rosa |
| Eficiência do fluxo | 1 toque | 1 toque | 1 toque |
| Consistência com o produto | Alta | Média-alta | Média |
| Acessibilidade e responsividade | Boa (contraste AA) | Boa, com o ajuste de cor do texto | Boa (branco sobre navy), conferir a 320px |
| Complexidade de implementação | Baixa (~2 regras CSS) | Média (~8 regras CSS) | Média (~10 regras CSS) |

### Recomendação de UX: **B**
Porque o objetivo é levar ao grupo até uma data, e a combinação de data visível com chamada explícita atende isso sem voltar ao visual de "Destaque" que o pedido manda abandonar.

**Direção visual aprovada:** Mockup C (cartão escuro "Black")
**Aprovado por:** Bruno (em 12/11/2026, por mensagem no chat)
**Decisões incorporadas:** fundo navy com brilho ouro/rosa, etiqueta dourada "Black Friday", título em Playfair itálico branco, botão rosa "Entrar no grupo", ilustração da Comunidade em círculo claro, texto "Grupo no WhatsApp com as ofertas em primeira mão."

---

## Fase 5 — Plano de execução (válido depois da escolha do mockup)

Estados de UI relevantes: **modo normal** (hoje), **modo campanha**, **sem JavaScript** (cai no modo normal) e **após 23/11** (volta ao normal). Viewports a validar: 320, 375 e 448 px (máximo da `.tela` em `home.css:22`).

### Etapa 1 — Lógica de modo, ainda sem mudar o que a pessoa vê
**Marco:** o script decide o modo corretamente; a home continua idêntica à de hoje.

#### T-01 — Criar `home-campanha.js`
- **Arquivo(s):** `home-campanha.js` (criar)
- **Depende de:** nenhuma
- **Ação:** criar função pura `campanhaAtiva(agora, busca)` e, no fim do arquivo, adicionar a classe `modo-campanha` em `document.documentElement` quando a função retornar `true`. Constante `CAMPANHA_ATE = '2026-11-24T00:00:00-03:00'` (fim exclusivo, equivale a 23/11 23:59:59 em Brasília).
- **Contrato:**
  ```js
  // campanhaAtiva(agora: Date, busca: string): boolean
  // busca contém "modo=campanha" → true; "modo=normal" → false;
  // caso contrário → agora.getTime() < new Date(CAMPANHA_ATE).getTime()
  ```
  Exportar só quando houver `module` (`if (typeof module !== 'undefined') module.exports = { campanhaAtiva };`) para permitir teste no Node.
- **Critério de aceite:** a função retorna `true` em `2026-11-12T10:00:00-03:00` e `2026-11-23T23:59:59-03:00`; `false` em `2026-11-24T00:00:00-03:00`; `?modo=normal` retorna `false` em 12/11; `?modo=campanha` retorna `true` em 25/11.
- **Como verificar:**
  ```bash
  node -e "const {campanhaAtiva:c}=require('./home-campanha.js');const t=s=>new Date(s);console.log(c(t('2026-11-12T10:00:00-03:00'),''),c(t('2026-11-23T23:59:59-03:00'),''),c(t('2026-11-24T00:00:00-03:00'),''),c(t('2026-11-12T10:00:00-03:00'),'?modo=normal'),c(t('2026-11-25T10:00:00-03:00'),'?modo=campanha'))"
  ```
  Saída esperada: `true true false false true`
- **Risco:** baixo — arquivo isolado.
- **Se der errado:** apagar `home-campanha.js`.

#### T-02 — Carregar o script no `<head>` da home
- **Arquivo(s):** `index.html` (alterar, após a linha 17)
- **Depende de:** T-01
- **Ação:** adicionar `<script src="./home-campanha.js"></script>` **síncrono** (sem `defer`) logo depois do `<link rel="stylesheet" href="./home.css" />`, para a classe existir antes da primeira pintura.
- **Critério de aceite:** com `?modo=campanha`, `document.documentElement.classList.contains('modo-campanha')` é `true`; sem parâmetro, em 12/11, também `true`.
- **Como verificar:** abrir `index.html` no navegador e rodar esse `classList.contains(...)` no console (ou via `javascript_tool`).
- **Risco:** baixo.
- **Se der errado:** remover a linha.

### Etapa 2 — Cartão novo e ocultação (depende do mockup escolhido)
**Marco:** o modo campanha mostra o layout aprovado; o modo normal fica igual ao atual.

#### T-03 — Marcar os 3 cartões antigos como `oculta-campanha`
- **Arquivo(s):** `index.html` (alterar linhas 40, 55 e 67)
- **Depende de:** T-02
- **Ação:** acrescentar a classe `oculta-campanha` em `#btn-comunidade`, `#btn-curso` e `#btn-mentoria`. Não remover nem alterar nada mais deles (links, textos e preço permanecem).
- **Critério de aceite:** sem a classe `modo-campanha` na `<html>`, a home é idêntica à atual.
- **Como verificar:** `?modo=normal` e comparar visualmente com o print atual.
- **Risco:** baixo.
- **Se der errado:** remover as 3 classes.

#### T-04 — Inserir o cartão "Esquenta Black Friday 23/11" conforme o mockup aprovado `[BLOQUEADO: ESCOLHA_DE_MOCKUP]`
- **Arquivo(s):** `index.html` (alterar, inserir antes da linha 40); `home.css` (alterar, acrescentar no fim)
- **Depende de:** T-03 e da escolha do mockup
- **Ação:** copiar do arquivo `mockup-<X>.html` aprovado o bloco do cartão (e só ele) e o CSS dele para o `home.css`, renomeando classes para `.c-esquenta*`. Marcar o cartão com `id="btn-esquenta"` e a classe `so-campanha`; `href="https://chat.whatsapp.com/H1OACRw221B6r26wp1b9KZ?s=cl&amp;p=a&amp;iam=2"` `target="_blank"` `rel="noopener noreferrer"`. Acrescentar ao fim do `home.css`:
  ```css
  /* Campanha Esquenta Black Friday — remover depois de 23/11/2026 */
  .so-campanha { display: none; }
  .modo-campanha .so-campanha { display: flex; }
  .modo-campanha .oculta-campanha { display: none; }
  ```
  Se o mockup escolhido for o B, usar `--navy-700` no texto "Entrar no grupo" e manter só a seta em rosa.
- **Critério de aceite:** com `?modo=campanha`, a ordem visível é Instagram → Esquenta → Loja → Catálogo → Encomendas; Destaque, Curso e Mentoria não aparecem (nem recebem foco por Tab); o clique no cartão abre o link do WhatsApp. Com `?modo=normal`, a home é igual à atual. Em 320, 375 e 448 px não há rolagem horizontal nem texto cortado.
- **Como verificar:**
  ```bash
  CH="/c/Program Files/Google/Chrome/Application/chrome.exe"
  for w in 320 375 448; do "$CH" --headless=new --hide-scrollbars --window-size=$w,1400 --virtual-time-budget=6000 --screenshot="prints/campanha-$w.png" "file:///C:/Fontes/FVGestaoCortadores/franvieira-com/index.html?modo=campanha"; done
  ```
  e abrir as 3 imagens. Conferir o `href` com Grep: `grep -n "chat.whatsapp.com" index.html`.
- **Risco:** médio — CSS novo em página de produção; pode quebrar em 320 px.
- **Se der errado:** `git revert` do commit desta tarefa.

### Etapa 3 — Validação e publicação
**Marco:** campanha publicada, com data de término testada.

#### T-05 — Teste de aceitação visual dos dois modos
- **Arquivo(s):** nenhum (verificação)
- **Depende de:** T-04
- **Ação:** gerar capturas `?modo=normal` e `?modo=campanha` e mostrar ao dono para a validação da versão alternativa.
- **Critério de aceite:** o dono confirma "é isso" na versão campanha e "igual a antes" na versão normal.
- **Como verificar:** capturas em `prints/` + aprovação em chat.
- **Risco:** baixo.
- **Se der errado:** voltar ao T-04 com os ajustes pedidos.

#### T-06 — Publicar e conferir no ar `[MANUAL]`
- **Arquivo(s):** nenhum
- **Depende de:** T-05
- **Ação:** commit e push de `home-campanha.js`, `index.html` e `home.css` (staging seletivo). Conferir como o site é publicado `[NÃO VERIFICADO]` e abrir a URL pública com e sem `?modo=normal`.
- **Critério de aceite:** a URL pública mostra a campanha sem parâmetro e a home normal com `?modo=normal`.
- **Como verificar:** abrir a URL pública no celular.
- **Risco:** baixo.
- **Se der errado:** `git revert` e novo push.

### Etapa 4 — Encerramento (depois de 23/11)
**Marco:** código da campanha removido, home volta a ser só a home.

#### T-07 — Remover a campanha `[MANUAL — a partir de 24/11/2026]`
- **Arquivo(s):** `index.html` (alterar), `home.css` (alterar), `home-campanha.js` (remover)
- **Depende de:** T-06
- **Ação:** remover o `<script>` do `<head>`, o cartão `#btn-esquenta`, as classes `oculta-campanha` e as 3 regras do bloco "Campanha Esquenta Black Friday" no `home.css`; apagar `home-campanha.js`.
- **Critério de aceite:** `grep -rn "campanha\|esquenta" index.html home.css` não retorna nada, e a home é idêntica à de antes da campanha.
- **Como verificar:** o `grep` acima e uma captura de tela comparada ao print original.
- **Risco:** baixo.
- **Se der errado:** `git revert`.

## Ordem de execução
T-01 → T-02 → T-03 → T-04 (depende do mockup) → T-05 → T-06 → T-07 (após 23/11).

## Impacto colateral
- **R1.** Relógio do aparelho errado → modo errado (aceito; o grupo continua funcionando).
- **R2.** Bots e previews de link (WhatsApp, Instagram) não executam JS: veem a home normal. Por isso o cartão novo fica escondido por padrão e a página sem JS cai no modo normal.
- **R3.** Cache do `home.css`: a Hostinger serve com `Cache-Control: max-age=604800` (7 dias). Aconteceu de verdade em 12/11: o celular carregou o `index.html` novo com o `home.css` antigo e o cartão apareceu sem estilo, com Destaque e Curso visíveis. Correção: versionar na URL (`home.css?v=20261113`, `home-campanha.js?v=20261113`). **Sempre que mudar esses arquivos, trocar o `?v=` no `index.html`.** (Também vale na T-07: ao remover a campanha, trocar o `?v=`.)
  - *Correção ao plano original:* a premissa "se o CSS estiver desatualizado o cartão fica escondido" estava errada, porque o cartão só fica escondido com o CSS novo.
- **R4.** O Curso (com preço promocional) e a Mentoria ficam fora do ar durante a campanha: confirmar que é intencional (P1).

## Teste de aceitação (do ponto de vista de quem pediu)
1. Abrir a home pelo celular: aparece o cartão "Esquenta Black Friday 23/11" no topo; não aparecem Destaque, Curso e Mentoria.
2. Tocar no cartão: abre o grupo do WhatsApp.
3. Abrir `…/?modo=normal`: a home é igual à de antes.
4. No dia 24/11, abrir a home sem parâmetro: está igual à de antes, sem ninguém ter mexido em nada.

## Entrega
- **Commit 1 (T-01 e T-02):** `feat(home): modo campanha por data (script isolado)`
- **Commit 2 (T-03 e T-04):** `feat(home): cartão Esquenta Black Friday 23/11 e ocultação de Destaque, Curso e Mentoria na campanha`
- **Commit 3 (T-07, após 23/11):** `chore(home): remove a campanha Esquenta Black Friday`
- Os commits entram só com os arquivos da mudança (nunca `git add -A`: há pastas não rastreadas `franvieira-com/` e `harness-angular-kit/` na raiz). Não há PR: o fluxo atual é commit e push direto em `main`.
