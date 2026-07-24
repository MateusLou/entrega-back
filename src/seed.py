"""Popula o banco com um cenário operacional realista do aeroporto de Cape Town (CPT).

Uso:
    python -m src.seed

O script é idempotente: apaga os dados existentes e recria tudo do zero.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.database.database import SessionLocal
from src.models.aeronave import Aeronave
from src.models.alocacao_vaga import AlocacaoVaga
from src.models.bagagem import Bagagem
from src.models.passageiro import Passageiro
from src.models.reserva import Reserva
from src.models.terminal import Terminal
from src.models.vaga import Vaga
from src.models.voo import Voo
from src.use_cases.reserva_use_case import ReservaUseCase
from src.entities.reserva import RealocarReserva
from src.utils.assentos import gerar_assentos
from src.utils.enums import (
    FinalidadeAlocacao,
    StatusBagagem,
    StatusReserva,
    StatusVaga,
    StatusVoo,
    TipoTerminal,
    TipoVaga,
)

rnd = random.Random(42)
AGORA = datetime.now().replace(second=0, microsecond=0)

NAC = "NACIONAL"
INT = "INTERNACIONAL"

AERONAVES = [
    ("ZS-ABC", "Boeing 737-800", "South African Airways", 174),
    ("ZS-DEF", "Airbus A320-200", "FlySafair", 186),
    ("ZS-GHI", "Embraer E190", "Airlink", 98),
    ("ZS-JKL", "Boeing 787-9", "KLM", 294),
    ("ZS-MNO", "Airbus A350-900", "LATAM", 324),
    ("ZS-PQR", "Bombardier CRJ900", "CemAir", 90),
    ("ZS-STU", "Boeing 777-300ER", "Emirates", 354),
    ("ZS-VWX", "Airbus A330-300", "British Airways", 288),
]

VAGAS = [
    # (codigo, terminal, tipo)
    ("A1", NAC, TipoVaga.GATE),
    ("A2", NAC, TipoVaga.GATE),
    ("A3", NAC, TipoVaga.GATE),
    ("A4", NAC, TipoVaga.GATE),
    ("A5", NAC, TipoVaga.GATE),
    ("R1", NAC, TipoVaga.REMOTA),
    ("R2", NAC, TipoVaga.REMOTA),
    ("B1", INT, TipoVaga.GATE),
    ("B2", INT, TipoVaga.GATE),
    ("B3", INT, TipoVaga.GATE),
    ("B4", INT, TipoVaga.GATE),
    ("R3", INT, TipoVaga.REMOTA),
]

VOOS = [
    # (codigo, origem, destino, horas_ate_partida, duracao_h, prefixo, terminal, status)
    ("SA301", "JNB", "CPT", -7.0, 2.0, "ZS-ABC", NAC, StatusVoo.FINALIZADO),
    ("FA202", "CPT", "JNB", -5.0, 2.0, "ZS-DEF", NAC, StatusVoo.FINALIZADO),
    ("4Z115", "DUR", "CPT", -3.0, 2.2, "ZS-GHI", NAC, StatusVoo.FINALIZADO),
    ("SA333", "CPT", "DUR", -0.5, 2.2, "ZS-PQR", NAC, StatusVoo.EMBARQUE),
    ("FA255", "CPT", "PLZ", 0.5, 1.5, "ZS-ABC", NAC, StatusVoo.EMBARQUE),
    ("SA345", "CPT", "JNB", 1.5, 2.0, "ZS-GHI", NAC, StatusVoo.ATRASADO),
    ("4Z128", "ELS", "CPT", 2.5, 1.8, "ZS-PQR", NAC, StatusVoo.NO_HORARIO),
    ("FA271", "CPT", "JNB", 4.0, 2.0, "ZS-DEF", NAC, StatusVoo.NO_HORARIO),
    ("SA360", "CPT", "DUR", 6.0, 2.2, "ZS-GHI", NAC, StatusVoo.NO_HORARIO),
    ("4Z140", "CPT", "JNB", 8.0, 2.0, "ZS-PQR", NAC, StatusVoo.NO_HORARIO),
    ("FA290", "CPT", "PLZ", 10.0, 1.5, "ZS-ABC", NAC, StatusVoo.CANCELADO),
    ("BA058", "LHR", "CPT", -6.0, 11.5, "ZS-VWX", INT, StatusVoo.FINALIZADO),
    ("EK770", "DXB", "CPT", -2.0, 9.5, "ZS-STU", INT, StatusVoo.FINALIZADO),
    ("KL597", "AMS", "CPT", -0.3, 11.5, "ZS-JKL", INT, StatusVoo.EMBARQUE),
    ("SA223", "CPT", "GRU", 1.0, 9.0, "ZS-MNO", INT, StatusVoo.ATRASADO),
    ("BA059", "CPT", "LHR", 3.0, 11.5, "ZS-VWX", INT, StatusVoo.NO_HORARIO),
    ("EK771", "CPT", "DXB", 5.0, 9.5, "ZS-STU", INT, StatusVoo.NO_HORARIO),
    ("QR137", "DOH", "CPT", 7.0, 9.0, "ZS-MNO", INT, StatusVoo.NO_HORARIO),
    ("KL598", "CPT", "AMS", 9.0, 11.5, "ZS-JKL", INT, StatusVoo.NO_HORARIO),
    ("SA224", "CPT", "GRU", 12.0, 9.0, "ZS-MNO", INT, StatusVoo.CANCELADO),
]

NOMES = [
    "Thabo Nkosi", "Amahle Dlamini", "Sipho Mokoena", "Lerato Khumalo",
    "Johan van der Merwe", "Anika Botha", "Pieter Steyn", "Marike du Plessis",
    "Nomsa Mahlangu", "Bongani Zulu", "Zanele Mthembu", "Kagiso Molefe",
    "Ayanda Sithole", "Naledi Mabaso", "Tshepo Radebe", "Refilwe Motaung",
    "Mateus Loureiro", "Camila Ferreira", "Rafael Almeida", "Beatriz Nogueira",
    "Lucas Carvalho", "Juliana Barros", "Gustavo Pereira", "Larissa Cardoso",
    "James Whitfield", "Emma Harrington", "Oliver Bennett", "Sophie Clarke",
    "Daniel Hughes", "Charlotte Reed", "Thomas Fletcher", "Isabelle Gray",
    "Ahmed Al-Farsi", "Fatima Hassan", "Omar Rashid", "Layla Mansour",
    "Youssef Haddad", "Noura Aziz", "Karim Nasser", "Salma Rahim",
    "Lars Jansen", "Fenna de Vries", "Bram Visser", "Sanne Bakker",
    "Hendrik Mulder", "Iris van Dijk", "Joost Meijer", "Lotte Smit",
    "Chen Wei", "Li Xiuying", "Zhang Ming", "Wang Fang",
    "Priya Naidoo", "Rajesh Pillay", "Anjali Reddy", "Vikram Govender",
    "Grace Achieng", "Samuel Okoro", "Aisha Bello", "Emeka Obi",
]

#: Tamanho do cadastro de passageiros. Precisa ser bem maior que a lotação de um
#: voo para que a ocupação média fique realista sem repetir passageiro no mesmo voo.
TOTAL_PASSAGEIROS = 200

#: Teto de reservas por voo, para o manifesto continuar navegável na tela.
MAX_RESERVAS_POR_VOO = 140

LOCAIS_BAGAGEM = {
    StatusBagagem.DESPACHADA: "Balcão de check-in",
    StatusBagagem.EM_TRIAGEM: "Esteira de triagem",
    StatusBagagem.CARREGADA: "Porão da aeronave",
    StatusBagagem.ENTREGUE: "Esteira de restituição",
    StatusBagagem.EXTRAVIADA: "Achados e perdidos",
}


def limpar(db: Session) -> None:
    """Apaga na ordem inversa das dependências para não violar as FKs."""
    for model in (Bagagem, AlocacaoVaga, Reserva, Voo, Vaga, Aeronave, Terminal, Passageiro):
        db.query(model).delete()
    db.commit()


def criar_terminais(db: Session) -> dict[str, Terminal]:
    terminais = {
        NAC: Terminal(nome="Terminal Nacional", tipo=TipoTerminal.NACIONAL),
        INT: Terminal(nome="Terminal Internacional", tipo=TipoTerminal.INTERNACIONAL),
    }
    db.add_all(terminais.values())
    db.commit()
    return terminais


def criar_vagas(db: Session, terminais: dict[str, Terminal]) -> dict[str, Vaga]:
    vagas = {
        codigo: Vaga(
            codigo=codigo,
            terminal_id=terminais[terminal].id,
            tipo=tipo,
            status=StatusVaga.LIVRE,
        )
        for codigo, terminal, tipo in VAGAS
    }
    db.add_all(vagas.values())
    db.commit()
    return vagas


def criar_aeronaves(db: Session) -> dict[str, Aeronave]:
    aeronaves = {
        prefixo: Aeronave(
            prefixo=prefixo, modelo=modelo, companhia=companhia, capacidade=capacidade
        )
        for prefixo, modelo, companhia, capacidade in AERONAVES
    }
    db.add_all(aeronaves.values())
    db.commit()
    return aeronaves


def criar_voos(
    db: Session, aeronaves: dict[str, Aeronave], terminais: dict[str, Terminal]
) -> dict[str, Voo]:
    voos: dict[str, Voo] = {}
    for codigo, origem, destino, offset, duracao, prefixo, terminal, status in VOOS:
        partida = AGORA + timedelta(hours=offset)
        chegada = partida + timedelta(hours=duracao)
        voo = Voo(
            codigo=codigo,
            origem=origem,
            destino=destino,
            partida_prevista=partida,
            chegada_prevista=chegada,
            partida_real=partida if status in (StatusVoo.EMBARQUE, StatusVoo.FINALIZADO) else None,
            chegada_real=chegada if status is StatusVoo.FINALIZADO else None,
            status=status,
            aeronave_id=aeronaves[prefixo].id,
            terminal_id=terminais[terminal].id,
        )
        voos[codigo] = voo
        db.add(voo)
    db.commit()
    return voos


def gerar_nomes(quantidade: int) -> list[str]:
    """Expande a lista curada combinando prenomes e sobrenomes, sem repetir nomes."""
    nomes = list(NOMES)
    vistos = set(nomes)
    prenomes = [n.split()[0] for n in NOMES]
    sobrenomes = [" ".join(n.split()[1:]) for n in NOMES]
    for prenome in prenomes:
        for sobrenome in sobrenomes:
            if len(nomes) >= quantidade:
                return nomes[:quantidade]
            combinacao = f"{prenome} {sobrenome}"
            if combinacao not in vistos:
                vistos.add(combinacao)
                nomes.append(combinacao)
    return nomes[:quantidade]


def criar_passageiros(db: Session) -> list[Passageiro]:
    passageiros = [
        Passageiro(
            nome=nome,
            documento=f"ZA{1000000 + i * 137:07d}",
            email=f"{nome.split()[0].lower()}.{nome.split()[-1].lower()}{i}@exemplo.com",
            telefone=f"+27 {rnd.randint(60, 84)} {rnd.randint(100, 999)} {rnd.randint(1000, 9999)}",
        )
        for i, nome in enumerate(gerar_nomes(TOTAL_PASSAGEIROS))
    ]
    db.add_all(passageiros)
    db.commit()
    return passageiros


def _statuses_para(status_voo: StatusVoo, quantidade: int) -> list[StatusReserva]:
    """Distribui os estados das reservas de forma coerente com o estado do voo."""
    if status_voo is StatusVoo.CANCELADO:
        return [StatusReserva.CANCELADA] * quantidade
    if status_voo is StatusVoo.FINALIZADO:
        estados = [StatusReserva.EMBARCADA] * quantidade
        for i in range(min(2, quantidade)):
            estados[i] = StatusReserva.NO_SHOW
        return estados
    if status_voo is StatusVoo.EMBARQUE:
        estados = [StatusReserva.CHECK_IN_FEITO] * quantidade
        for i in range(quantidade):
            if i % 4 == 3:
                estados[i] = StatusReserva.CONFIRMADA
            if i % 15 == 0:  # alguns passageiros perdem o voo
                estados[i] = StatusReserva.NO_SHOW
        return estados
    estados = [StatusReserva.CONFIRMADA] * quantidade
    for i in range(quantidade):
        if i % 3 == 0:
            estados[i] = StatusReserva.CHECK_IN_FEITO
    return estados


def criar_reservas(
    db: Session, voos: dict[str, Voo], passageiros: list[Passageiro]
) -> list[Reserva]:
    reservas: list[Reserva] = []
    for voo in voos.values():
        # Ocupação entre 35% e 85% da aeronave, limitada pelo tamanho do cadastro.
        alvo = int(voo.aeronave.capacidade * rnd.uniform(0.35, 0.85))
        quantidade = min(alvo, len(passageiros), MAX_RESERVAS_POR_VOO)
        escolhidos = rnd.sample(passageiros, quantidade)
        estados = _statuses_para(voo.status, quantidade)
        assentos = gerar_assentos(voo.aeronave.capacidade)
        rnd.shuffle(assentos)
        indice_assento = 0

        for passageiro, estado in zip(escolhidos, estados):
            # Reservas encerradas devolvem o assento ao inventário do voo.
            if estado in (StatusReserva.NO_SHOW, StatusReserva.CANCELADA, StatusReserva.REALOCADA):
                assento = None
            else:
                assento = assentos[indice_assento]
                indice_assento += 1

            check_in = None
            if estado in (StatusReserva.CHECK_IN_FEITO, StatusReserva.EMBARCADA):
                check_in = voo.partida_prevista - timedelta(minutes=rnd.randint(40, 180))

            reserva = Reserva(
                passageiro_id=passageiro.id,
                voo_id=voo.id,
                assento=assento,
                status=estado,
                check_in_em=check_in,
            )
            reservas.append(reserva)
            db.add(reserva)
    db.commit()
    return reservas


def criar_bagagens(db: Session, reservas: list[Reserva]) -> list[Bagagem]:
    status_por_voo = {
        StatusVoo.FINALIZADO: StatusBagagem.ENTREGUE,
        StatusVoo.EMBARQUE: StatusBagagem.CARREGADA,
        StatusVoo.ATRASADO: StatusBagagem.EM_TRIAGEM,
        StatusVoo.NO_HORARIO: StatusBagagem.DESPACHADA,
    }
    ativas = [
        r
        for r in reservas
        if r.status
        in (StatusReserva.CONFIRMADA, StatusReserva.CHECK_IN_FEITO, StatusReserva.EMBARCADA)
    ]
    bagagens: list[Bagagem] = []
    numero = 1
    for reserva in ativas:
        if rnd.random() > 0.6:  # nem todo passageiro despacha mala
            continue
        base = status_por_voo.get(reserva.voo.status, StatusBagagem.DESPACHADA)
        for _ in range(rnd.randint(1, 2)):
            status = StatusBagagem.EXTRAVIADA if rnd.random() < 0.06 else base
            bagagens.append(
                Bagagem(
                    etiqueta=f"CPT{numero:06d}",
                    reserva_id=reserva.id,
                    peso_kg=Decimal(str(rnd.randint(700, 2800) / 100)),
                    status=status,
                    local_atual=LOCAIS_BAGAGEM[status],
                )
            )
            numero += 1
    db.add_all(bagagens)
    db.commit()
    return bagagens


def criar_alocacoes(db: Session, voos: dict[str, Voo], vagas: dict[str, Vaga]) -> None:
    """Coloca nas vagas os voos que estão em pátio agora."""
    plano = [
        ("SA333", "A1", FinalidadeAlocacao.EMBARQUE),
        ("FA255", "A2", FinalidadeAlocacao.EMBARQUE),
        ("SA345", "A3", FinalidadeAlocacao.ABASTECIMENTO),
        ("4Z140", "R1", FinalidadeAlocacao.PERNOITE),
        ("KL597", "B1", FinalidadeAlocacao.DESEMBARQUE),
        ("SA223", "B2", FinalidadeAlocacao.EMBARQUE),
        ("BA059", "B3", FinalidadeAlocacao.ABASTECIMENTO),
    ]
    for codigo_voo, codigo_vaga, finalidade in plano:
        voo, vaga = voos[codigo_voo], vagas[codigo_vaga]
        db.add(
            AlocacaoVaga(
                voo_id=voo.id,
                vaga_id=vaga.id,
                inicio=min(voo.partida_prevista - timedelta(hours=1), AGORA),
                fim=None,
                finalidade=finalidade,
                ativa=True,
            )
        )
        vaga.status = StatusVaga.OCUPADA
    # Uma vaga fora de operação, para o mapa do terminal não ficar binário.
    vagas["R2"].status = StatusVaga.MANUTENCAO
    db.commit()


def realocar_exemplo(db: Session, voos: dict[str, Voo]) -> int:
    """Executa uma realocação real pelo use case, para o histórico nascer consistente.

    SA333 (CPT->DUR, em embarque) e SA360 (CPT->DUR, mais tarde) têm o mesmo destino,
    então um passageiro que perdeu o primeiro pode ser remanejado para o segundo.
    """
    destino = voos["SA360"]
    candidatas = (
        db.query(Reserva)
        .filter(Reserva.voo_id == voos["SA333"].id, Reserva.status == StatusReserva.NO_SHOW)
        .all()
    )
    ocupados_no_destino = {
        r.passageiro_id
        for r in db.query(Reserva).filter(Reserva.voo_id == destino.id).all()
    }
    for origem in candidatas:
        # Quem já está no voo de destino não pode ser realocado para lá.
        if origem.passageiro_id in ocupados_no_destino:
            continue
        ReservaUseCase(db).realocar(origem.id, RealocarReserva(voo_destino_id=destino.id))
        return 1

    # Nenhum no-show elegível: transforma uma reserva ativa em no-show para o exemplo.
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.voo_id == voos["SA333"].id,
            Reserva.status == StatusReserva.CHECK_IN_FEITO,
            Reserva.passageiro_id.notin_(ocupados_no_destino or {0}),
        )
        .first()
    )
    if reserva is None:
        return 0
    reserva.status = StatusReserva.NO_SHOW
    reserva.assento = None
    db.commit()
    ReservaUseCase(db).realocar(reserva.id, RealocarReserva(voo_destino_id=destino.id))
    return 1


def main() -> None:
    db = SessionLocal()
    try:
        print("Limpando dados existentes...")
        limpar(db)

        terminais = criar_terminais(db)
        vagas = criar_vagas(db, terminais)
        aeronaves = criar_aeronaves(db)
        voos = criar_voos(db, aeronaves, terminais)
        passageiros = criar_passageiros(db)
        reservas = criar_reservas(db, voos, passageiros)
        bagagens = criar_bagagens(db, reservas)
        criar_alocacoes(db, voos, vagas)
        realocadas = realocar_exemplo(db, voos)

        print(
            f"""
Seed concluído:
  {len(terminais):>4} terminais
  {len(vagas):>4} vagas
  {len(aeronaves):>4} aeronaves
  {len(voos):>4} voos
  {len(passageiros):>4} passageiros
  {len(reservas):>4} reservas ({realocadas} realocação de exemplo)
  {len(bagagens):>4} bagagens
"""
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
