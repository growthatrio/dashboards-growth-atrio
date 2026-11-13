# Dashboards Atrio (Growth Atrio, Growth Hotéis e Growth Travel Week)

Versão para a equipe dos dashboards criados no Claude. Acesso só para quem estiver na lista, com e-mail e senha.
Os dados vêm da Nekt, consultados pelo servidor. A chave da Nekt nunca vai para o navegador.

## Como publicar (uma vez só)

1. **GitHub** (repositório privado `dashboards-growth-atrio`): clique em *Add file > Upload files* e arraste TODO o conteúdo desta pasta
   (`api`, `public`, `private`, `vercel.json`, `LEIA-ME.md`). Clique em *Commit changes*.
2. **Vercel**: *Add New > Project*, escolha `dashboards-growth-atrio`, em *Framework Preset* deixe **Other** e clique em *Deploy*.
3. Ainda na Vercel: *Settings > Environment Variables*. Crie estas 3 (marque *Production*; na chave da Nekt, marque *Sensitive*):
   - `NEKT_API_KEY`: a chave `dashboards-growth` da Nekt.
   - `SESSION_SECRET`: um texto aleatório de 40 caracteres ou mais (gere no gerenciador de senhas).
   - `ACCESS_USERS`: quem pode entrar e a senha de cada um, neste formato exato:
     `{"gabriel.fumagalli@atriohoteis.com.br":"SENHA_1","suzane.navarro@atriohoteis.com.br":"SENHA_2"}`
4. *Deployments > ... > Redeploy* para valer as variáveis.
5. Abra o endereço do projeto, entre, e depois abra `/api/health`: deve mostrar `"nekt": "ok"`.

## Dia a dia
- **Dar acesso a alguém:** inclua o e-mail e uma senha em `ACCESS_USERS` e faça Redeploy.
- **Tirar acesso:** remova o e-mail de `ACCESS_USERS` e faça Redeploy. A sessão dele deixa de valer na hora.
- **Trocar a chave da Nekt:** crie outra na Nekt, atualize `NEKT_API_KEY`, faça Redeploy e revogue a antiga.
- Senhas e chaves só na Vercel. Nunca em e-mail, chat ou GitHub.

## Observações
- Cada dado é guardado por 10 minutos no servidor para não consultar a Nekt toda hora.
- O plano gratuito da Vercel é só para testes. Para uso da empresa, use o plano Pro.
- Se algum bloco mostrar "Falha ao carregar", o motivo aparece no canto inferior esquerdo da tela.
