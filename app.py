
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


if __name__ == "__main__":
    app.run(debug=False)
