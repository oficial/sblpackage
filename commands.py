import os
import os.path
import textwrap
import sublime
import sublime_plugin
import sbldyad.objects as dyad

LICENCES = {
    1: "Dyad",
    2: "Bematech"
}


def reformat(template):
    return textwrap.dedent(template).lstrip()

class ConfigPortCommand(sublime_plugin.WindowCommand):
    def is_enabled(self):
        return self.window.project_data() is not None

    def run(self):
        try:
            self.cache = dyad.CacheManager(self.window)
            porta = self.cache.get_engine_port(False)
            self.window.show_input_panel(
                "Porta do engine", porta or "", self.handle_user_input, None, None)
        except Exception as e:
           sublime.error_message("Erro: %s" % e)

    def handle_user_input(self, port):
        try:
            self.cache.add_project_data('engine_port', port)
        except Exception as e:
            sublime.error_message("Erro:: %s" % e)

class ConfigUserCommand(sublime_plugin.WindowCommand):
    def is_enabled(self):
        return self.window.project_data() is not None

    def run(self):
        try:
            self.cache = dyad.CacheManager(self.window)
            usuario = self.cache.get_project_data('engine_user')
            self.window.show_input_panel(
                "Usuário", usuario or "", self.handle_user_input, None, None)
        except Exception as e:
            sublime.error_message("Erro: %s" % e)

    def handle_user_input(self, user):
        try:
            self.cache.add_project_data('engine_user', user)
        except Exception as e:
            sublime.error_message("Erro: %s" % e)

class LoadCacheCommand(sublime_plugin.WindowCommand):
    def is_enabled(self):
        try:
            if self.window.project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self):
        try:
            if sublime.yes_no_cancel_dialog(
                "Atenção! Todos os arquivos do projeto serão"
                "descartados e uma nova cópia da IVFS será gerada em disco.\n"
                "Deseja mesmo continuar ?",
                "Arrocha!", "Deixa quieto!") is not sublime.DIALOG_YES:
                return
            loader = dyad.CacheLoader(self.window)
            loader.start()
            self.check_load_progress( loader )
        except Exception as e:
            sublime.error_message("Erro: %s" % e)

    def check_load_progress(self, loader, i=0, dir=1):
        try:
            if loader.is_alive():
                before = i % 8
                after = (7) - before
                if not after:
                    dir = -1
                if not before:
                    dir = 1
                i += dir
                self.window.active_view().set_status(
                    '', 'Carregando [%s=%s]' % (' ' * before, ' ' * after))
                sublime.set_timeout(
                    lambda: self.check_load_progress( loader, i, dir), 100)
                return
            self.window.active_view().set_status('','')
            sublime.message_dialog("Cache carregado com sucesso!")
        except Exception as e:
            sublime.error_message("Erro: %s" % e)

class CopyKeyToClipboardCommand(sublime_plugin.WindowCommand):
    def is_visible(self, files=None):
        try:
            if files is None or len(files) <= 0:
                return False
            if self.window.project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self, files):
        for f in files:
            v = self.window.find_open_file(f)
            if v is None:
                return

            self.copy_file_key(v,f)

    def copy_file_key(self, view, file):
        cache = dyad.CacheManager(self.window)
        file = cache.file_path_to_vfs_path(file)
        print('copy_file_key:: File='+ file)
        dados_do_script = cache.get_script(file)
        if dados_do_script is None:
            print("Nao encontrou")
            return
        sublime.set_clipboard(str(dados_do_script.get('chave')))
        sublime.status_message("Chave %d copiada" % dados_do_script.get('chave'))

class CopyClassKeyToClipboardCommand(sublime_plugin.WindowCommand):
    def is_visible(self, files=None):
        try:
            if files is None or len(files) <= 0:
                return False
            if self.window.project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self, files):
        for f in files:
            v = self.window.find_open_file(f)
            if v is None:
                return

            self.copy_class_key(v,f)

    def copy_class_key(self, view, file):
        cache = dyad.CacheManager(self.window)
        file = cache.file_path_to_vfs_path(file)
        print('copy_class_key:: File='+ file)
        dados_do_script = cache.get_script(file)
        if dados_do_script is None:
            print("Nao encontrou")
            return
        sublime.set_clipboard(str(dados_do_script.get('mae')))
        sublime.status_message("Chave %d copiada" % dados_do_script.get('mae'))

class ShowLocalChangesCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        try:
            if self.window.project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self):
        v = self.window.new_file()
        v.set_name("Arquivos alterados apenas localmente")
        v.set_scratch(True)
        cache = dyad.CacheManager(self.window)
        titulo = "\nArquivos alterados e ainda não enviados ao engine:\n"
        text = ""
        for file in cache.get_local_changes():
            text = text + ("\t%d\t%s\n" % (file[1], file[5]))
        if text is "":
            text = "\tNenhum arquivo alterado apenas localmente"
        v.run_command('append', {'characters': (titulo + text)})
        v.set_read_only(True)

class GetRemoteChangesCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        try:
            if self.window.project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self):
        dados_do_projeto = self.window.project_data()
        passwd = dados_do_projeto.get('engine_passwd', None)
        if passwd is None:
            self.window.show_input_panel(
                "Senha do usuario", "", self.get_remote_changes, None, None)
        else:
            self.get_remote_changes(passwd)

    def get_remote_changes(self, passwd):
        cache = dyad.CacheManager(self.window)
        titulo = ("Atualizações na IVFS desde %s %s" % cache.get_most_recent_cache_update())
        text = cache.update_local_repository(passwd)
        cache.register_cache_load()

        v = self.window.new_file()
        v.set_name(titulo)
        v.set_scratch(True)
        v.run_command('append', {'characters': (titulo +":\n\n"+ text)})
        v.set_read_only(True)


class ShowFileInfoCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        try:
            if self.view.window().project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self, edit):
        filename = self.view.file_name()
        if not filename:
            return
        cache = dyad.CacheManager(self.view.window())
        filename = cache.file_path_to_vfs_path(filename)
        script   = cache.get_script(filename)
        if script is None:
            print("Script não encontrado no cache: %s" % filename)
        else:
            self.view.set_status(
                'a_chave', ("Chave:%d" % script.get('chave')))
            self.view.set_status(
                'b_versao', ("Versão:%d" % script.get('versao')))
            license = LICENCES.get(script.get('licenca'),"")
            if license:
                self.view.set_status('c_produto', ("Produto:%s" % license))
            if license is "Bematech":
                prj = self.view.window().project_data()
                if not prj.get("product_change", False):
                    self.view.set_read_only(True)

class OpenKeyCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        try:
            if self.view.window().project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self, edit):
        # proj_data = self.view.window().project_data()
        self.view.run_command('expand_selection', {"to":"word"})
        sels = self.view.sel()
        if len(sels) == 0:
            return
        regiao_da_palavra = self.view.word(sels[0])
        palavra = self.view.substr(regiao_da_palavra)
        if not palavra.isdigit():
            return
        regiao_da_palavra.a = regiao_da_palavra.a - 1
        palavra_expandida = self.view.substr(regiao_da_palavra)
        try:
            int(palavra_expandida)
            palavra = palavra_expandida
        except ValueError:
            pass
        searchkey = int(palavra)
        # print("Chave selecionada: %d" % searchkey)

        cache = dyad.CacheManager(self.view.window())
        dados_do_script = cache.get_script_or_class(searchkey)
        if dados_do_script is None:
            print("Nenhum script encontrado!")
            return
        if dados_do_script.get('erro') > 0:
            sublime.error_message("Aconteceu algum problema e não foi possível "
                "exportar esse arquivo para o projeto do sublime!")
            return

        pasta_raiz = cache.get_root_path()
        # print("Pasta raiz: %s" % pasta_raiz)

        caminho_script = pasta_raiz + dados_do_script.get('path')

        caminho_script = dyad.handle_filename(caminho_script)
        # print("Item para abrir: %s" % caminho_script)

        if os.path.isfile(caminho_script):
            self.view.window().open_file(caminho_script)
            return
        else:
            sublime.message_dialog("Não foi possível encontrar o arquivo!\n"
                "Path: "+ caminho_script)

class RegisterFileChangeCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        try:
            if self.view.window().project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self, edit):
        filename = self.view.file_name()
        if not filename:
            return
        cache = dyad.CacheManager(self.view.window())
        # dados_do_script = cache.get_script(filename)
        # if dados_do_script is None:
        #     # Trata-se de um script novo
        #     cache.insert_script()
        cache.set_file_changed(filename)

class SaveFileCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        try:
            if self.view.window().project_data().get('engine_port') is not None:
                return True
            return False
        except Exception as e:
            return False

    def run(self, edit):
        try:
            self.filename = self.view.file_name()
            if self.filename is None:
                return
            dados_do_projeto = self.view.window().project_data()
            self.user = dados_do_projeto.get('engine_user', None)
            if self.user is None:
                raise Exception("Configure a usuário antes de prosseguir!")

            passwd = dados_do_projeto.get('engine_passwd', None)
            if passwd is None:
                self.view.window().show_input_panel(
                    "Senha do usuario", "", self.save_file, None, None)
            else:
                self.save_file(passwd)
        except Exception as e:
           sublime.error_message("Erro: %s" % e)

    def save_file(self, passwd):
        try:
            cache = dyad.CacheManager(self.view.window())
            cache.save_file(self.filename, self.user, passwd)
        except Exception as e:
            sublime.error_message("Erro: %s" % e)


class ShowEngineHelp(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.set_name("Sobre o Engine IDE")
        v.set_scratch(True)
        template = reformat("""
            Esse plugin tem por objetivo possibilitar o uso do Sublime Text como uma IDE
            básica para o desenvolvimento no iEngine.

            Para isso, o sublime se comunica via HTTP com um engine LOCAL, acessando um script
            (que deve existir na base), e enviando comandos para o script e processando a resposta.

            Dessa forma, não é possível utilizar esse plugin para se comunicar com engines remotos.

            Exemplo de fluxo de trabalho:

            1. Criação inicial do projeto no sublime

                1.1. A partir de uma janela existente, selecione a opção "File/New Window".

                1.2. Na nova janela, selecione "Project/Save project As".

                1.3. Crie uma pasta para o projeto, informe o nome da base como nome do arquivo
                    do projeto e salve.

                1.4. Depois do projeto criado, use os comandos abaixo para configurar os dados
                    do projeto: "Project/Engine IDE/Configurar Porta" e "Configurar Usuário".

                1.5. Selecione a opção "Project/Engine IDE/Carregar Cache". Se essa opção já
                    tiver sido executada alguma vez, o cache anterior será completamente deletado
                    e uma nova cópia será criada em disco. Durante o carregamento a barra de
                    status apresentará uma mensagem característica. O tempo de carga pode
                    variar, dependendo do tamanho do cache.

                    OBS 1: Apenas arquivos texto serão exportados. Arquivos como imagens,
                    JARs, ZIPs, EXEs e demais arquivos binários não serão exportados.

                    OBS 2: Alguns arquivos, normalmente x-class, possuem a IURL tão grande que
                    o engine não consegue grava-los em disco, porque o parâmetro "filename"
                    da API File só aceita strings com aproximadamente 255 caracteres.

                1.6. Quando o cache terminar de carregar, será exibida uma mensagem. Selecione
                    a opção "Project/Refresh Folders" para atualizar a arvore de arquivos do
                    painel lateral. Se o painel lateral ainda não estiver visível selecione a
                    opção "View/Side Bar/Show Side Bar".

                1.7. No carregamento do cache, será criado um arquivo "cache.db" na pasta do
                    projeto. Esse arquivo é um banco de dados SQLite e será utilizado para
                    guardar os detalhes dos arquivos como chave, classe, versão, se ele foi
                    alterado pelo sublime etc.

            2. Edição de arquivos

                2.1. Os arquivos podem ser abertos e alterados à vontade. Ao abrir um arquivo
                    será exibido na barra de status a chave e a versão desse arquivo.
                    A navegação entre os arquivos usando CTRL+ENTER deve funcionar como esperado.
                    Na versão atual, o CTRL+ENTER em chaves de classes só funciona se a classe
                    possuir pelo menos um arquivo. A gravação normal com CTRL+S não irá gravar
                    as alterações no engine, apenas no projeto local. Também é possivel clicar
                    com o botão direito em um arquivo no painel lateral e selecionar a opção
                    "Copiar chave" para que a chave do arquivo seja colocada na área de
                    transferência.

                    OBS: Ao abrir um arquivo com CTRL+ENTER, ele não será selecionado no painel
                    lateral do Sublime. Se desejar que isso aconteça clique com o botão direito
                    na área de edição e selecione a opção "Reveal in Side Bar".

                2.2. Foi criada uma definição de sintaxe exclusiva para os scripts
                    do engine chamada  "Bematech javascript". Essa sintaxe será
                    usada automaticamente quando forem abertos scripts com as
                    extensões utilizadas no Engine. Foi criada uma sintaxe separada
                    basicamente para permitir strings multi-linha, o que é considerado
                    erro de sintaxe no Javascript normal.

                2.3. Para consultar os arquivos que já foram alterados, selecione a opção
                    "Project/Engine IDE/Mostrar arquivos alterados". Será aberta uma nova aba
                    no Sublime com a listagem dos scripts alterados apenas localmente.
                    Use o CTRL+ENTER nas chaves exibidas na listagem para acessar os arquivos.

                2.4. Quando desejar gravar um arquivo no engine, abra o arquivo e execute o
                    comando CTRL+SHIFT+S. Será solicitada a senha do seu usuário e depois
                    será enviado um comando para o engine gravar o arquivo na IVFS.
                    Se a gravação for bem sucedida a versão do arquivo será atualizada no
                    Sublime e ele deixará de aparecer na listagem citada acima.

                2.5. Se no momento da gravação houver conflito de versão, será possível optar
                    por fazer o merge das alterações. Depois do merge feito, tente gravar
                    novamente com CTRL+SHIFT+S e a gravação deve ser feita com sucesso.

                2.6. Para abrir rapidamente um arquivo, digite CTRL+P e comece a digitar o nome,
                    ou parte do nome do arquivo, que o Sublime fará uma busca e mostrará os
                    possíveis arquivos, semelhante a uma busca por x-find em campos lookup.

                2.7. Para realizar busca por uma string em toda a IVFS, use o comando CTRL+SHIFT+F
                    do Sublime. Essa busca normalmente é mais rápida do que rodar um select na IVFS,
                    e permite ainda buscar usando expressões regulares.

            Nessa versão ainda não estão implementadas algumas funções como: criar, excluir,
            renomear ou mover scripts, apenas alteração. Também ainda não temos um IDBC
            disponível, mas todas essas funcionalidades estão planejadas para as próximas versões.

        """)
        v.run_command('append', {'characters': template})
        v.set_read_only(True)

