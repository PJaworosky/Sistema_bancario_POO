import textwrap
import json
from abc import ABC, abstractmethod
from datetime import datetime

# --- Persistência de Dados ---
ARQUIVO_DADOS = "banco_dados.json"

def salvar_dados(clientes, contas):
    """Salva os dados no arquivo JSON."""
    dados = {
        "clientes": [
            {
                "nome": c.nome,
                "data_nascimento": c.data_nascimento,
                "cpf": c.cpf,
                "endereco": c.endereco,
                "contas": [conta.numero for conta in c.contas],
            }
            for c in clientes
        ],
        "contas": [
            {
                "numero": conta.numero,
                "agencia": conta.agencia,
                "saldo": conta.saldo,
                "cliente_cpf": conta.cliente.cpf,
                "transacoes": conta.historico.transacoes,
            }
            for conta in contas
        ]
    }
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def carregar_dados():
    """Carrega os dados do arquivo JSON."""
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"clientes": [], "contas": []}

# --- Classes (Modelagem Orientada a Objetos) ---

class Cliente:
    """Representa um cliente do banco."""
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        """Realiza uma transação na conta do cliente."""
        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        """Adiciona uma conta à lista de contas do cliente."""
        self.contas.append(conta)

class PessoaFisica(Cliente):
    """Representa uma pessoa física, herdando de Cliente."""
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf

class Conta:
    """Representa uma conta bancária."""
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    def sacar(self, valor):
        """Realiza um saque."""
        if valor <= 0:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False
        if valor > self._saldo:
            print("\n@@@ Operação falhou! Saldo insuficiente. @@@")
            return False

        self._saldo -= valor
        print("\n=== Saque realizado com sucesso! ===")
        return True

    def depositar(self, valor):
        """Realiza um depósito."""
        if valor <= 0:
            print("\n@@@ Operação falhou! Valor inválido. @@@")
            return False

        self._saldo += valor
        print("\n=== Depósito realizado com sucesso! ===")
        return True

class ContaCorrente(Conta):
    """Representa uma conta corrente."""
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self.limite = limite
        self.limite_saques = limite_saques
        self.numero_saques = 0

    def sacar(self, valor):
        """Saque com limites adicionais."""
        if valor > self.limite:
            print("\n@@@ Operação falhou! Saque excede o limite. @@@")
            return False
        if self.numero_saques >= self.limite_saques:
            print("\n@@@ Operação falhou! Limite de saques excedido. @@@")
            return False

        if super().sacar(valor):
            self.numero_saques += 1
            return True
        return False

class Historico:
    """Armazena o histórico de transações."""
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        )

class Transacao(ABC):
    @property
    @abstractmethod
    def valor(self):
        pass

    @abstractmethod
    def registrar(self, conta):
        pass

class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.sacar(self.valor):
            conta.historico.adicionar_transacao(self)

class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        if conta.depositar(self.valor):
            conta.historico.adicionar_transacao(self)

# --- Funções de Ajuda ---

def menu():
    menu_str = """\n
    [d] Depositar
    [s] Sacar
    [e] Extrato
    [nu] Novo Usuário
    [nc] Nova Conta
    [lc] Listar Contas
    [q] Sair
    => """
    return input(textwrap.dedent(menu_str)).strip().lower()

def filtrar_cliente(cpf, clientes):
    return next((cliente for cliente in clientes if cliente.cpf == cpf), None)

def escolher_conta(cliente):
    """Permite selecionar qual conta o cliente quer usar."""
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta. @@@")
        return None

    print("\n=== Contas do Cliente ===")
    for i, conta in enumerate(cliente.contas, start=1):
        print(f"[{i}] Conta {conta.numero} | Saldo: R$ {conta.saldo:.2f}")
    escolha = input("Escolha a conta: ")

    try:
        indice = int(escolha) - 1
        return cliente.contas[indice]
    except (ValueError, IndexError):
        print("\n@@@ Opção inválida. @@@")
        return None

def criar_cliente(clientes):
    while True:
        cpf = input("Informe o CPF (somente números): ").strip()
        if cpf.isdigit():
            break
        print("@@@ CPF inválido. Digite apenas números! @@@")

    if filtrar_cliente(cpf, clientes):
        print("\n@@@ Já existe cliente com este CPF. @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = PessoaFisica(nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco)
    clientes.append(cliente)
    print("\n=== Cliente criado com sucesso! ===")

def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado. @@@")
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    cliente.adicionar_conta(conta)

    print("\n=== Conta criada com sucesso! ===")

def listar_contas(contas):
    print("\n================ LISTA DE CONTAS ================")
    if not contas:
        print("Nenhuma conta cadastrada.")
    for conta in contas:
        print(f"\nAgência:\t{conta.agencia}")
        print(f"Número:\t\t{conta.numero}")
        print(f"Titular:\t{conta.cliente.nome}")
        print(f"Saldo:\t\tR$ {conta.saldo:.2f}")
        print("------------------------------------------")
    print("================================================")

def main():
    dados = carregar_dados()
    clientes = []
    contas = []

    # Reconstruindo objetos a partir do JSON
    for cliente_data in dados["clientes"]:
        cliente = PessoaFisica(
            nome=cliente_data["nome"],
            data_nascimento=cliente_data["data_nascimento"],
            cpf=cliente_data["cpf"],
            endereco=cliente_data["endereco"],
        )
        clientes.append(cliente)

    for conta_data in dados["contas"]:
        cliente = filtrar_cliente(conta_data["cliente_cpf"], clientes)
        conta = ContaCorrente.nova_conta(cliente, conta_data["numero"])
        conta._saldo = conta_data["saldo"]
        conta.historico._transacoes = conta_data["transacoes"]
        contas.append(conta)
        cliente.adicionar_conta(conta)

    while True:
        opcao = menu()

        if opcao == "d":
            cpf = input("Informe o CPF do cliente: ")
            cliente = filtrar_cliente(cpf, clientes)
            if not cliente:
                print("\n@@@ Cliente não encontrado! @@@")
                continue

            conta = escolher_conta(cliente)
            if not conta:
                continue

            try:
                valor = float(input("Informe o valor do depósito: R$ "))
            except ValueError:
                print("\n@@@ Valor inválido! @@@")
                continue

            cliente.realizar_transacao(conta, Deposito(valor))

        elif opcao == "s":
            cpf = input("Informe o CPF do cliente: ")
            cliente = filtrar_cliente(cpf, clientes)
            if not cliente:
                print("\n@@@ Cliente não encontrado! @@@")
                continue

            conta = escolher_conta(cliente)
            if not conta:
                continue

            try:
                valor = float(input("Informe o valor do saque: R$ "))
            except ValueError:
                print("\n@@@ Valor inválido! @@@")
                continue

            cliente.realizar_transacao(conta, Saque(valor))

        elif opcao == "e":
            cpf = input("Informe o CPF do cliente: ")
            cliente = filtrar_cliente(cpf, clientes)
            if not cliente:
                print("\n@@@ Cliente não encontrado! @@@")
                continue

            conta = escolher_conta(cliente)
            if not conta:
                continue

            print("\n================ EXTRATO ================")
            transacoes = conta.historico.transacoes
            if not transacoes:
                print("Nenhuma movimentação.")
            else:
                for t in transacoes:
                    print(f"{t['data']} | {t['tipo']} | R$ {t['valor']:.2f}")
            print(f"\nSaldo atual: R$ {conta.saldo:.2f}")
            print("==========================================")

        elif opcao == "nu":
            criar_cliente(clientes)

        elif opcao == "nc":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "q":
            salvar_dados(clientes, contas)
            print("\nObrigado por usar nosso sistema bancário. Até mais!")
            break

        else:
            print("\n@@@ Opção inválida. @@@")

if __name__ == "__main__":
    main()
