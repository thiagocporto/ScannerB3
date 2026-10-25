import json
import os

ARQUIVO = "universo_b3.json"

# 1. Carrega dados já existentes (para preservar FIIs, BDRs e ETFs)
dados_atuais = []
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        dados_atuais = json.load(f)

# Filtra o que não for ação para reaproveitar
fiis_existentes = [x for x in dados_atuais if x.get("tipo") == "FII"]
bdrs_existentes = [x for x in dados_atuais if x.get("tipo") == "BDR"]
etfs_existentes = [x for x in dados_atuais if x.get("tipo") == "ETF"]

# 2. Base IBrX 100 (Blue & Mid Caps)
ibrx_100 = [
    {"ticker": "ABEV3", "nome": "Ambev"}, {"ticker": "ALOS3", "nome": "Allos"},
    {"ticker": "ALPA4", "nome": "Alpargatas"}, {"ticker": "ASAI3", "nome": "Assaí"},
    {"ticker": "AURE3", "nome": "Auren Energia"}, {"ticker": "AZUL4", "nome": "Azul"},
    {"ticker": "B3SA3", "nome": "B3"}, {"ticker": "BBAS3", "nome": "Banco do Brasil"},
    {"ticker": "BBDC3", "nome": "Bradesco ON"}, {"ticker": "BBDC4", "nome": "Bradesco PN"},
    {"ticker": "BBSE3", "nome": "BB Seguridade"}, {"ticker": "BEEF3", "nome": "Minerva"},
    {"ticker": "BPAC11", "nome": "BTG Pactual"}, {"ticker": "BRAP4", "nome": "Bradespar"},
    {"ticker": "BRFS3", "nome": "BRF"}, {"ticker": "BRKM5", "nome": "Braskem"},
    {"ticker": "CCRO3", "nome": "CCR"}, {"ticker": "CMIG4", "nome": "Cemig"},
    {"ticker": "CMIN3", "nome": "CSN Mineração"}, {"ticker": "COGN3", "nome": "Cogna"},
    {"ticker": "CPFE3", "nome": "CPFL Energia"}, {"ticker": "CPLE6", "nome": "Copel"},
    {"ticker": "CRFB3", "nome": "Carrefour Brasil"}, {"ticker": "CSAN3", "nome": "Cosan"},
    {"ticker": "CSNA3", "nome": "CSN"}, {"ticker": "CVCB3", "nome": "CVC Brasil"},
    {"ticker": "CYRE3", "nome": "Cyrela"}, {"ticker": "DXCO3", "nome": "Dexco"},
    {"ticker": "EGIE3", "nome": "Engie Brasil"}, {"ticker": "ELET3", "nome": "Eletrobras ON"},
    {"ticker": "ELET6", "nome": "Eletrobras PN"}, {"ticker": "EMBR3", "nome": "Embraer"},
    {"ticker": "ENEV3", "nome": "Eneva"}, {"ticker": "ENGI11", "nome": "Energisa"},
    {"ticker": "EQTL3", "nome": "Equatorial"}, {"ticker": "EZTC3", "nome": "EZTec"},
    {"ticker": "FLRY3", "nome": "Fleury"}, {"ticker": "GGBR4", "nome": "Gerdau"},
    {"ticker": "GOAU4", "nome": "Metalúrgica Gerdau"}, {"ticker": "GOLL4", "nome": "Gol"},
    {"ticker": "HAPV3", "nome": "Hapvida"}, {"ticker": "HYPE3", "nome": "Hypera"},
    {"ticker": "IGTI11", "nome": "Iguatemi"}, {"ticker": "IRBR3", "nome": "IRB Brasil"},
    {"ticker": "ITSA4", "nome": "Itaúsa"}, {"ticker": "ITUB4", "nome": "Itaú Unibanco"},
    {"ticker": "JBSS3", "nome": "JBS"}, {"ticker": "KLBN11", "nome": "Klabin"},
    {"ticker": "LREN3", "nome": "Lojas Renner"}, {"ticker": "LWSA3", "nome": "Locaweb"},
    {"ticker": "MGLU3", "nome": "Magazine Luiza"}, {"ticker": "MRFG3", "nome": "Marfrig"},
    {"ticker": "MRVE3", "nome": "MRV Engenharia"}, {"ticker": "MULT3", "nome": "Multiplan"},
    {"ticker": "NTCO3", "nome": "Natura"}, {"ticker": "PCAR3", "nome": "Pão de Açúcar"},
    {"ticker": "PETR3", "nome": "Petrobras ON"}, {"ticker": "PETR4", "nome": "Petrobras PN"},
    {"ticker": "PRIO3", "nome": "PRIO"}, {"ticker": "RADL3", "nome": "RaiaDrogasil"},
    {"ticker": "RAIZ4", "nome": "Raízen"}, {"ticker": "RDOR3", "nome": "Rede D'Or"},
    {"ticker": "RECV3", "nome": "PetroRecôncavo"}, {"ticker": "RENT3", "nome": "Localiza"},
    {"ticker": "SANB11", "nome": "Santander Brasil"}, {"ticker": "SBSP3", "nome": "Sabesp"},
    {"ticker": "SLCE3", "nome": "SLC Agrícola"}, {"ticker": "SMTO3", "nome": "São Martinho"},
    {"ticker": "SUZB3", "nome": "Suzano"}, {"ticker": "TAEE11", "nome": "Taesa"},
    {"ticker": "TIMS3", "nome": "TIM Brasil"}, {"ticker": "TOTS3", "nome": "Totvs"},
    {"ticker": "TRPL4", "nome": "ISA Cteep"}, {"ticker": "UGPA3", "nome": "Ultrapar"},
    {"ticker": "USIM5", "nome": "Usiminas"}, {"ticker": "VALE3", "nome": "Vale"},
    {"ticker": "VAMO3", "nome": "Vamos"}, {"ticker": "VBBR3", "nome": "Vibra Energia"},
    {"ticker": "VIVA3", "nome": "Vivara"}, {"ticker": "VIVT3", "nome": "Telefônica Brasil"},
    {"ticker": "WEGE3", "nome": "WEG"}, {"ticker": "YDUQ3", "nome": "Yduqs"}
]

# 3. Componentes do Índice SMLL (Small Caps da B3)
smll_100 = [
    {"ticker": "ABCB4", "nome": "Banco ABC Brasil"}, {"ticker": "AGRO3", "nome": "BrasilAgro"},
    {"ticker": "ALPK3", "nome": "Estapar"}, {"ticker": "ANIM3", "nome": "Ânima Educação"},
    {"ticker": "ARML3", "nome": "Armac"}, {"ticker": "BMOB3", "nome": "Bemobi"},
    {"ticker": "CAML3", "nome": "Camil Alimentos"}, {"ticker": "CBAV3", "nome": "CBA"},
    {"ticker": "CEAB3", "nome": "C&A Modas"}, {"ticker": "CLSA3", "nome": "ClearSale"},
    {"ticker": "CSED3", "nome": "Cruzeiro do Sul Educacional"}, {"ticker": "CURY3", "nome": "Cury Construtora"},
    {"ticker": "DIRR3", "nome": "Direcional Engenharia"}, {"ticker": "DEXP3", "nome": "Dexxos"},
    {"ticker": "ECOR3", "nome": "EcoRodovias"}, {"ticker": "ESPA3", "nome": "Espaçolaser"},
    {"ticker": "EVEN3", "nome": "Even Construtora"}, {"ticker": "EZTC3", "nome": "EZTec"},
    {"ticker": "FESA4", "nome": "Ferbasa"}, {"ticker": "FIQE3", "nome": "Unifique"},
    {"ticker": "GFSA3", "nome": "Gafisa"}, {"ticker": "GMAT3", "nome": "Grupo Mateus"},
    {"ticker": "GRND3", "nome": "Grendene"}, {"ticker": "GUAR3", "nome": "Guararapes"},
    {"ticker": "HBSA3", "nome": "Hidrovias do Brasil"}, {"ticker": "INTB3", "nome": "Intelbras"},
    {"ticker": "JALL3", "nome": "Jalles Machado"}, {"ticker": "KEPL3", "nome": "Kepler Weber"},
    {"ticker": "LAVV3", "nome": "Lavvi Construtora"}, {"ticker": "LEVE3", "nome": "Mahle Metal Leve"},
    {"ticker": "LJQQ3", "nome": "Lojas Quero-Quero"}, {"ticker": "LOGG3", "nome": "LOG CP"},
    {"ticker": "LIGT3", "nome": "Light"}, {"ticker": "MATD3", "nome": "Mater Dei"},
    {"ticker": "MDIA3", "nome": "M. Dias Branco"}, {"ticker": "MEAL3", "nome": "IMC Alimentação"},
    {"ticker": "MEGA3", "nome": "MegaWhats"}, {"ticker": "MILS3", "nome": "Mills"},
    {"ticker": "MLAS3", "nome": "Multilaser"}, {"ticker": "MOVI3", "nome": "Movida"},
    {"ticker": "MYPK3", "nome": "Iochpe-Maxion"}, {"ticker": "ODPV3", "nome": "Odontoprev"},
    {"ticker": "ONCO3", "nome": "Oncoclínicas"}, {"ticker": "ORVR3", "nome": "Orizon"},
    {"ticker": "PARD3", "nome": "Instituto Hermes Pardini"}, {"ticker": "PGMN3", "nome": "Pague Menos"},
    {"ticker": "PLPL3", "nome": "Plano & Plano"}, {"ticker": "PNVL3", "nome": "Dimed Panvel"},
    {"ticker": "POMO4", "nome": "Marcopolo"}, {"ticker": "POSI3", "nome": "Positivo Tecnologia"},
    {"ticker": "PRNR3", "nome": "Priner"}, {"ticker": "QUAL3", "nome": "Qualicorp"},
    {"ticker": "RANI3", "nome": "Irani Papel"}, {"ticker": "RAPT4", "nome": "Randoncorp"},
    {"ticker": "ROMI3", "nome": "Indústrias Romi"}, {"ticker": "SEER3", "nome": "Ser Educacional"},
    {"ticker": "SHUL4", "nome": "Schulz"}, {"ticker": "SIMH3", "nome": "Simpar"},
    {"ticker": "SOJA3", "nome": "Boa Safra Sementes"}, {"ticker": "SRNA3", "nome": "Serena Energia"},
    {"ticker": "STBP3", "nome": "Santos Brasil"}, {"ticker": "SYNE3", "nome": "Syn Prop & Tech"},
    {"ticker": "TASA4", "nome": "Taurus Armas"}, {"ticker": "TEND3", "nome": "Construtora Tenda"},
    {"ticker": "TGMA3", "nome": "Tegma Gestão Logística"}, {"ticker": "TRIS3", "nome": "Trisul"},
    {"ticker": "TTEN3", "nome": "3Tentos"}, {"ticker": "TUPY3", "nome": "Tupy"},
    {"ticker": "UNIP6", "nome": "Unipar Carbocloro"}, {"ticker": "VITT3", "nome": "Vittia"},
    {"ticker": "VLID3", "nome": "Valid"}, {"ticker": "VULC3", "nome": "Vulcabras"},
    {"ticker": "WIZC3", "nome": "Wiz Co"}, {"ticker": "ZAMP3", "nome": "Zamp (Burger King)"}
]

# 4. Deduplicação e Consolidação de Ações
mapa_acoes = {}
for acao in ibrx_100 + smll_100:
    t = acao["ticker"].strip().upper()
    if t not in mapa_acoes:
        mapa_acoes[t] = {
            "ticker": t,
            "tipo": "AÇÃO",
            "nome": acao.get("nome", t)
        }

lista_acoes = list(mapa_acoes.values())

# 5. Montagem do Universo Final
catalogo_final = lista_acoes + fiis_existentes + bdrs_existentes + etfs_existentes

with open(ARQUIVO, "w", encoding="utf-8") as f:
    json.dump(catalogo_final, f, indent=4, ensure_ascii=False)

cont_acoes = len(lista_acoes)
cont_fiis = len(fiis_existentes)
cont_etfs = len(etfs_existentes)
cont_bdrs = len(bdrs_existentes)

print("=" * 60)
print("UNIVERSO B3 ATUALIZADO COM SUCESSO!")
print(f"• Ações (IBrX 100 + SMLL unificados): {cont_acoes}")
print(f"• FIIs / FIAGROs: {cont_fiis}")
print(f"• ETFs: {cont_etfs}")
print(f"• BDRs: {cont_bdrs}")
print(f"TOTAL DE ATIVOS CONSOLIDADOS: {len(catalogo_final)}")
print("=" * 60)
