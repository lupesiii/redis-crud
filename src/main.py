from InquirerPy import inquirer
from rich.table import Table
from InquirerPy.base.control import Choice

from db.login import loginUsuario, verificarSessao
from db.produtos import (
    atualizarProdutoRedis,
    buscarProdutos,
    cadastrarProduto,
    excluirProdutoRedis,
    listarProdutosRedis,
)
from lib.rich import console
from db.vendedores import (
    cadastrarVendedor,
    buscarVendedor,
    listarVendedoresRedis,
    atualizarVendedorRedis,
    excluirVendedorRedis,
)
from models.ErroException import ErroException
from lib.inquirrerPy import verificarInteiro, verificarVazio, verificarDecimal

CAMPOS = {
    "nome": "Nome",
    "descricao": "Descrição",
    "precoEmCentavos": "Preço em centavos (ex.: 9900 = R$ 99,00)",
    "estoque": "Estoque",
    "imagem": "Imagem (URL ou caminho)",
}


def perguntarCampo(campo, padrao=""):
    if campo in ["precoEmCentavos", "estoque"]:
        return inquirer.text(
            message=CAMPOS[campo] + ":",
            validate=(
                verificarDecimal if campo == "precoEmCentavos" else verificarInteiro
            ),
        ).execute()
    return inquirer.text(message=CAMPOS[campo] + ":", validate=verificarVazio).execute()


def mostrarProdutos(produtos):
    if not produtos:
        console.print("Nenhum produto encontrado no Redis.")
        return
    tabela = Table(title="Produtos")
    for coluna in ("ID", "Nome", "Descrição", "Preço", "Estoque", "Loja", "Imagem"):
        tabela.add_column(coluna)
    for produto in produtos:
        preco = f"{produto.precoEmCentavos // 100},{produto.precoEmCentavos % 100:02d}"
        tabela.add_row(
            produto.id,
            produto.nome,
            produto.descricao,
            f"R$ {preco}",
            str(produto.estoque),
            produto.vendedor.nome_loja,
            produto.imagem,
        )
    console.print(tabela)


def selecionarProduto():
    produtos = listarProdutosRedis()

    if not produtos:
        console.print("Nenhum produto encontrado no Redis.")
        return None

    return inquirer.select(
        message="Selecione o produto:",
        choices=[
            {"name": f"{produto.nome} — {produto.id}", "value": produto.id}
            for produto in produtos
        ]
        + [{"name": "Voltar", "value": None}],
    ).execute()


def mostrarVendedores(vendedores):
    if not vendedores:
        console.print("Nenhum vendedor encontrado no Redis.")
        return
    tabela = Table(title="Vendedores")
    for coluna in ("ID", "Nome da loja", "ID do usuário"):
        tabela.add_column(coluna)
    for vendedor in vendedores:
        tabela.add_row(vendedor.id, vendedor.nomeLoja, vendedor.usuarioId)
    console.print(tabela)


def selecionarVendedor():
    vendedores = listarVendedoresRedis()
    if not vendedores:
        console.print("Nenhum vendedor encontrado no Redis.")
        return None
    return inquirer.select(
        message="Selecione o vendedor:",
        choices=[
            Choice(vendedor.id, name=f"{vendedor.nomeLoja} — {vendedor.id}")
            for vendedor in vendedores
        ]
        + [Choice(None, name="Voltar")],
    ).execute()


def main():
    token = loginUsuario()

    try:
        while True:
            opcao = inquirer.select(
                message="Escolha a ação desejada: ",
                choices=[
                    Choice(
                        1, name="Copiar produtos de uma loja do MongoDB para o Redis"
                    ),
                    Choice(2, name="Listar produtos do Redis"),
                    Choice(3, name="Consultar produto pelo ID"),
                    Choice(4, name="Atualizar produto no Redis"),
                    Choice(5, name="Excluir produto do Redis"),
                    Choice(7, name="Copiar vendedores do MongoDB para o Redis"),
                    Choice(8, name="Listar vendedores do Redis"),
                    Choice(9, name="Consultar vendedor pelo ID"),
                    Choice(10, name="Atualizar vendedor no Redis"),
                    Choice(11, name="Excluir vendedor do Redis"),
                    Choice(6, name="Sair"),
                ],
            ).execute()

            match opcao:
                case 1:
                    if not verificarSessao(token):
                        loginUsuario()

                    try:
                        nomeLoja = inquirer.text(
                            message="Nome da Loja", validate=verificarVazio
                        ).execute()

                        produtos = cadastrarProduto(nomeLoja)

                        console.print(
                            f"{len(produtos)} produto(s) copiado(s) para o Redis."
                        )
                        mostrarProdutos(produtos)
                    except ErroException as e:
                        print(e)

                case 2:
                    if not verificarSessao(token):
                        loginUsuario()

                    try:
                        mostrarProdutos(listarProdutosRedis())
                    except ErroException as e:
                        print(e)

                case 3:
                    if not verificarSessao(token):
                        loginUsuario()

                    produtoId = inquirer.text(
                        message="ID do produto:", validate=verificarVazio
                    ).execute()

                    if produtoId:
                        try:
                            mostrarProdutos([buscarProdutos(produtoId)])
                        except ErroException as e:
                            print(e)

                case 4:
                    if not verificarSessao(token):
                        loginUsuario()

                    try:
                        produtoId = selecionarProduto()

                        if produtoId is None or not produtoId:
                            continue

                        produtoAtual = buscarProdutos(produtoId)
                        campos = inquirer.checkbox(
                            message="Quais campos deseja alterar? (Espaço seleciona; Enter confirma)",
                            choices=[
                                {"name": nome, "value": campo}
                                for campo, nome in CAMPOS.items()
                            ],
                            validate=lambda selecionados: bool(selecionados),
                            invalid_message="Selecione pelo menos um campo.",
                        ).execute()

                        dados = {
                            campo: perguntarCampo(campo, getattr(produtoAtual, campo))
                            for campo in campos
                        }
                        produto = atualizarProdutoRedis(produtoId, dados)
                        console.print("Produto atualizado no Redis.")
                        mostrarProdutos([produto])
                    except ErroException as e:
                        print(e)

                case 5:
                    try:
                        produtoId = selecionarProduto()
                        if produtoId is None or not produtoId:
                            continue
                        if inquirer.confirm(
                            message="Excluir este produto do Redis?", default=False
                        ).execute():
                            excluirProdutoRedis(produtoId)
                            console.print("Produto excluído do Redis.")
                    except ErroException as e:
                        print(e)
                case 7:
                    try:
                        vendedores = cadastrarVendedor()
                        console.print(
                            f"{len(vendedores)} vendedor(es) copiado(s) para o Redis."
                        )
                        mostrarVendedores(vendedores)
                    except ErroException as e:
                        console.print(str(e), style="red", markup=False)

                case 8:
                    try:
                        mostrarVendedores(listarVendedoresRedis())
                    except ErroException as e:
                        console.print(str(e), style="red", markup=False)

                case 9:
                    vendedorId = (
                        inquirer.text(
                            message="ID do vendedor:", validate=verificarVazio
                        )
                        .execute()
                        .strip()
                    )
                    try:
                        mostrarVendedores([buscarVendedor(vendedorId)])
                    except ErroException as e:
                        console.print(str(e), style="red", markup=False)

                case 10:
                    try:
                        vendedorId = selecionarVendedor()
                        if vendedorId is None:
                            continue
                        atual = buscarVendedor(vendedorId)
                        campos = inquirer.checkbox(
                            message="Quais campos deseja alterar?",
                            choices=[
                                Choice("nomeLoja", name="Nome da loja"),
                                Choice("usuarioId", name="ID do usuário"),
                            ],
                            validate=lambda selecionados: bool(selecionados),
                            invalid_message="Selecione pelo menos um campo.",
                        ).execute()
                        rotulos = {
                            "nomeLoja": "Nome da loja:",
                            "usuarioId": "ID do usuário:",
                        }
                        dados = {
                            campo: inquirer.text(
                                message=rotulos[campo],
                                default=getattr(atual, campo),
                                validate=verificarVazio,
                            )
                            .execute()
                            .strip()
                            for campo in campos
                        }
                        vendedor = atualizarVendedorRedis(vendedorId, dados)
                        console.print("Vendedor atualizado no Redis.")
                        mostrarVendedores([vendedor])
                    except ErroException as e:
                        console.print(str(e), style="red", markup=False)

                case 11:
                    try:
                        vendedorId = selecionarVendedor()
                        if vendedorId is None:
                            continue
                        if inquirer.confirm(
                            message="Excluir este vendedor do Redis?", default=False
                        ).execute():
                            excluirVendedorRedis(vendedorId)
                            console.print("Vendedor excluído do Redis.")
                    except ErroException as e:
                        console.print(str(e), style="red", markup=False)

                case 6:
                    break
    except (KeyboardInterrupt, EOFError):
        console.print("\nAplicação encerrada.")


if __name__ == "__main__":
    main()
