import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from database import conectar, criar_tabelas
from datetime import date
from decimal import Decimal, InvalidOperation

app = Flask(__name__)

criar_tabelas()


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    erro = None

    if request.method == "POST":
        descricao = request.form.get("descricao", "").strip()
        tipo = request.form.get("tipo", "")
        valor_texto = request.form.get("valor", "").strip()
        vencimento = request.form.get("vencimento", "")

        try:
            valor = Decimal(valor_texto)
            data_vencimento = date.fromisoformat(vencimento)

            if not descricao:
                erro = "Informe a descrição da conta."
            elif tipo not in ("PAGAR", "RECEBER"):
                erro = "Selecione um tipo de conta válido."
            elif not valor.is_finite() or valor <= 0:
                erro = "O valor deve ser maior que zero."
            elif valor.as_tuple().exponent < -2:
                erro = "Informe no máximo duas casas decimais."
            else:
                conexao = conectar()

                try:
                    conexao.execute("""
                        INSERT INTO contas_financeiras
                        (descricao, tipo, valor_centavos, data_vencimento)
                        VALUES (?, ?, ?, ?)
                    """, (
                        descricao,
                        tipo,
                        int(valor * 100),
                        data_vencimento.isoformat()
                    ))

                    conexao.commit()

                finally:
                    conexao.close()

                return redirect(url_for("inicio"))

        except (InvalidOperation, ValueError, OverflowError):
            erro = "Verifique o valor e a data informados."

    return render_template("cadastrar.html", erro=erro)

    

@app.route("/consultar")
def consultar():
    conexao = conectar()
    conexao.row_factory = sqlite3.Row

    try:
        contas = conexao.execute("""
            SELECT
                c.id_conta,
                c.descricao,
                c.tipo,
                c.valor_centavos,
                c.data_vencimento,
                c.status,
                COALESCE(
                    SUM(m.valor_centavos), 0
                ) AS movimentado_centavos,
                c.valor_centavos -
                    COALESCE(
                        SUM(m.valor_centavos), 0
                    ) AS saldo_centavos
            FROM contas_financeiras AS c
            LEFT JOIN movimentacoes_financeiras AS m
                ON m.id_conta = c.id_conta
            GROUP BY
                c.id_conta,
                c.descricao,
                c.tipo,
                c.valor_centavos,
                c.data_vencimento,
                c.status
            ORDER BY c.data_vencimento ASC
        """).fetchall()

    finally:
        conexao.close()

    return render_template(
        "consultar.html",
        contas=contas
    )

@app.route("/movimentar/<int:id_conta>", methods=["GET", "POST"])
def movimentar(id_conta):
    erro = None
    conexao = conectar()
    conexao.row_factory = sqlite3.Row

    try:
        if request.method == "POST":
            valor_texto = request.form.get("valor", "").strip()
            data_texto = request.form.get("data_movimentacao", "")

            try:
                valor = Decimal(valor_texto)
                data_movimentacao = date.fromisoformat(data_texto)

                if not valor.is_finite() or valor <= 0:
                    erro = "Informe um valor maior que zero."
                elif valor.as_tuple().exponent < -2:
                    erro = "Use no máximo duas casas decimais."
                else:
                    valor_centavos = int(valor * 100)

            except (InvalidOperation, ValueError, OverflowError):
                erro = "Informe um valor e uma data válidos."

            if erro is None:
                conexao.execute("BEGIN IMMEDIATE")

                conta = conexao.execute("""
                    SELECT id_conta, tipo, valor_centavos
                    FROM contas_financeiras
                    WHERE id_conta = ?
                """, (id_conta,)).fetchone()

                if conta is None:
                    conexao.rollback()
                    return "Conta não encontrada.", 404

                total_pago = conexao.execute("""
                    SELECT COALESCE(SUM(valor_centavos), 0)
                    FROM movimentacoes_financeiras
                    WHERE id_conta = ?
                """, (id_conta,)).fetchone()[0]

                saldo = conta["valor_centavos"] - total_pago

                if valor_centavos > saldo:
                    erro = "O valor ultrapassa o saldo pendente."
                    conexao.rollback()
                else:
                    tipo = (
                        "SAIDA" if conta["tipo"] == "PAGAR"
                        else "ENTRADA"
                    )

                    conexao.execute("""
                        INSERT INTO movimentacoes_financeiras
                        (id_conta, tipo, valor_centavos,
                         data_movimentacao)
                        VALUES (?, ?, ?, ?)
                    """, (
                        id_conta, tipo, valor_centavos,
                        data_movimentacao.isoformat()
                    ))

                    novo_saldo = saldo - valor_centavos

                    status = (
                        "QUITADA" if novo_saldo == 0
                        else "PARCIAL"
                    )

                    conexao.execute("""
                        UPDATE contas_financeiras
                        SET status = ?
                        WHERE id_conta = ?
                    """, (status, id_conta))

                    conexao.commit()

                    return redirect(url_for("consultar"))

        conta = conexao.execute("""
            SELECT id_conta, descricao, tipo, valor_centavos
            FROM contas_financeiras
            WHERE id_conta = ?
        """, (id_conta,)).fetchone()

        if conta is None:
            return "Conta não encontrada.", 404

        total_pago = conexao.execute("""
            SELECT COALESCE(SUM(valor_centavos), 0)
            FROM movimentacoes_financeiras
            WHERE id_conta = ?
        """, (id_conta,)).fetchone()[0]

        saldo = conta["valor_centavos"] - total_pago

        return render_template(
            "movimentar.html",
            conta=conta,
            saldo=saldo,
            erro=erro
        )

    finally:
        conexao.close()

if __name__ == "__main__":
    app.run(debug=False)
