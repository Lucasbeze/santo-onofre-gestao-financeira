
import sqlite3
from pathlib import Path

CAMINHO_BANCO = Path(__file__).parent / "santo_onofre.db"


def conectar():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabelas():
    conexao = conectar()

    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS categorias_financeiras (
                id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL
                    CHECK (tipo IN ('PAGAR', 'RECEBER')),
                descricao TEXT,
                UNIQUE (nome, tipo)
            );

            CREATE TABLE IF NOT EXISTS contas_financeiras (
                id_conta INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                tipo TEXT NOT NULL
                    CHECK (tipo IN ('PAGAR', 'RECEBER')),
                valor_total NUMERIC NOT NULL
                    CHECK (valor_total > 0),
                data_vencimento TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDENTE'
                    CHECK (status IN ('PENDENTE', 'PARCIAL', 'QUITADA')),
                id_categoria INTEGER,
                observacao TEXT,
                FOREIGN KEY (id_categoria)
                    REFERENCES categorias_financeiras(id_categoria)
            );

            CREATE TABLE IF NOT EXISTS movimentacoes_financeiras (
                id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
                id_conta INTEGER NOT NULL,
                tipo TEXT NOT NULL
                    CHECK (tipo IN ('ENTRADA', 'SAIDA')),
                valor NUMERIC NOT NULL
                    CHECK (valor > 0),
                data_movimentacao TEXT NOT NULL,
                descricao TEXT,
                FOREIGN KEY (id_conta)
                    REFERENCES contas_financeiras(id_conta)
            );
        """)

        conexao.commit()
        print("Tabelas criadas com sucesso!")

    finally:
        conexao.close()


if __name__ == "__main__":
    criar_tabelas()
