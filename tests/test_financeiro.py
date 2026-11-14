
import pytest

import database
from app import app


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    # Cada teste recebe um banco temporário e vazio.
    banco_teste = tmp_path / "teste_financeiro.db"

    monkeypatch.setattr(
        database, "CAMINHO_BANCO", banco_teste
    )

    database.criar_tabelas()

    app.config.update(TESTING=True)

    with app.test_client() as cliente_teste:
        yield cliente_teste


def test_cadastro_valido(cliente):
    resposta = cliente.post("/cadastrar", data={
        "descricao": "Compra de materiais",
        "tipo": "PAGAR",
        "valor": "500.00",
        "vencimento": "2026-11-20"
    })

    assert resposta.status_code == 302

    conexao = database.conectar()
    try:
        conta = conexao.execute("""
            SELECT descricao, valor_centavos, status
            FROM contas_financeiras
        """).fetchone()
    finally:
        conexao.close()

    assert conta == (
        "Compra de materiais", 50000, "PENDENTE"
    )


def test_cadastro_valor_negativo(cliente):
    resposta = cliente.post("/cadastrar", data={
        "descricao": "Conta inválida",
        "tipo": "PAGAR",
        "valor": "-100.00",
        "vencimento": "2026-11-20"
    })

    assert resposta.status_code == 200
    assert "maior que zero" in resposta.get_data(
        as_text=True
    )

    conexao = database.conectar()
    try:
        quantidade = conexao.execute("""
            SELECT COUNT(*) FROM contas_financeiras
        """).fetchone()[0]
    finally:
        conexao.close()

    assert quantidade == 0


def test_pagamento_maior_que_saldo(cliente):
    cliente.post("/cadastrar", data={
        "descricao": "Compra de materiais",
        "tipo": "PAGAR",
        "valor": "500.00",
        "vencimento": "2026-11-20"
    })

    resposta = cliente.post("/movimentar/1", data={
        "valor": "600.00",
        "data_movimentacao": "2026-11-20"
    })

    assert resposta.status_code == 200
    assert "ultrapassa o saldo" in resposta.get_data(
        as_text=True
    )

    conexao = database.conectar()
    try:
        quantidade = conexao.execute("""
            SELECT COUNT(*)
            FROM movimentacoes_financeiras
        """).fetchone()[0]
    finally:
        conexao.close()

    assert quantidade == 0
