import importlib
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class ProdutosTest(unittest.TestCase):
    def setUp(self):
        conexao = ModuleType('lib.connection')
        conexao.dbMongo = MagicMock()
        conexao.dbRedis = MagicMock()
        with patch.dict(sys.modules, {'lib.connection': conexao}):
            sys.modules.pop('db.produtos', None)
            self.mod = importlib.import_module('db.produtos')
        self.mongo = conexao.dbMongo
        self.redis = conexao.dbRedis
        self.hashes = {}
        pipe = self.redis.pipeline.return_value.__enter__.return_value
        pipe.exists.side_effect = lambda chave: chave in self.hashes
        def gravar(chave, mapping):
            self.hashes.setdefault(chave, {}).update({k: str(v) for k, v in mapping.items()})
        pipe.hset.side_effect = gravar
        self.redis.hgetall.side_effect = lambda chave: self.hashes.get(chave, {})
        self.redis.scan_iter.side_effect = lambda **kwargs: iter(self.hashes)
        self.redis.delete.side_effect = lambda chave: int(self.hashes.pop(chave, None) is not None)
        self.dados = dict(nome='Teclado', descricao='USB', precoEmCentavos=9900,
                          estoque=2, imagem='teclado.png',
                          vendedor=dict(vendedor_id='v1', nome_loja='Loja'))

    def test_crud_e_devolucao(self):
        produto = self.mod.criarProdutoRedis(self.dados)
        self.assertEqual(self.mod.buscarProdutos(produto.id).precoEmCentavos, 9900)
        self.assertEqual(len(self.mod.listarProdutosRedis()), 1)
        self.mod.atualizarProdutoRedis(produto.id, {'estoque': 0})
        self.assertEqual(self.mod.buscarProdutos(produto.id).estoque, 0)
        self.mongo.produtos.find_one.return_value = None
        self.mod.salvarProdutoNoMongo(produto.id)
        filtro, update = self.mongo.produtos.update_one.call_args.args
        self.assertEqual(str(filtro['_id']), produto.id)
        self.assertEqual(update['$set']['estoque'], 0)
        self.assertNotIn('_id', update['$set'])
        self.assertTrue(self.mod.excluirProdutoRedis(produto.id))
        self.mongo.produtos.delete_one.assert_not_called()
        with self.assertRaises(self.mod.ErroException):
            self.mod.buscarProdutos(produto.id)

    def test_copia_dois_preserva_origem(self):
        documentos = [{**self.dados, '_id': 'a'}, {**self.dados, '_id': 'b'}]
        cursor = self.mongo.produtos.find.return_value
        cursor.sort.return_value.limit.return_value = documentos
        self.assertEqual(len(self.mod.cadastrarProduto('Loja')), 2)
        cursor.sort.return_value.limit.assert_called_once_with(2)
        self.mongo.produtos.delete_many.assert_not_called()
        self.mongo.produtos.delete_one.assert_not_called()

    def test_validacao_e_duplicidade(self):
        self.mod.criarProdutoRedis({**self.dados, '_id': 'a'})
        with self.assertRaises(self.mod.ErroException):
            self.mod.criarProdutoRedis({**self.dados, '_id': 'a'})
        for dados in ({'estoque': -1}, {'estoque': None}, {'campo_invalido': 1}, {}):
            with self.assertRaises(self.mod.ErroException):
                self.mod.atualizarProdutoRedis('a', dados)
        self.assertEqual(self.mod.buscarProdutos('a').estoque, 2)

    def test_copia_insuficiente_nao_grava(self):
        cursor = self.mongo.produtos.find.return_value
        cursor.sort.return_value.limit.return_value = [{**self.dados, '_id': 'a'}]
        with self.assertRaises(self.mod.ErroException):
            self.mod.cadastrarProduto('Loja')
        self.assertEqual(self.hashes, {})


if __name__ == '__main__':
    unittest.main()
