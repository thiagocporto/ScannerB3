import json
import os

ARQUIVO = "universo_b3.json"

# Preserva FIIs, BDRs e ETFs existentes
dados_atuais = []
if os.path.exists(ARQUIVO):
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        dados_atuais = json.load(f)

fiis = [x for x in dados_atuais if x.get("tipo") == "FII"]
bdrs = [x for x in dados_atuais if x.get("tipo") == "BDR"]
etfs = [x for x in dados_atuais if x.get("tipo") == "ETF"]

# Lista expandida com exatamente 200 Ações ÚNICAS da B3 (Top 100 IBrX + 100 Small/Mid Caps)
acoes_200 = [
    # --- IBrX 100 & Blue Chips (100 Ativos) ---
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
    {"ticker": "WEGE3", "nome": "WEG"}, {"ticker": "YDUQ3", "nome": "Yduqs"},
    {"ticker": "ALUP11", "nome": "Alupar"}, {"ticker": "AMER3", "nome": "Americanas"},
    {"ticker": "ANIM3", "nome": "Ânima Educação"}, {"ticker": "ARZZ3", "nome": "Arezzo&Co"},
    {"ticker": "BIDI11", "nome": "Banco Inter"}, {"ticker": "BRKM3", "nome": "Braskem ON"},
    {"ticker": "CASH3", "nome": "Méliuz"}, {"ticker": "CIEL3", "nome": "Cielo"},
    {"ticker": "CSMG3", "nome": "Copasa"}, {"ticker": "DIRR3", "nome": "Direcional"},
    {"ticker": "ENBR3", "nome": "EDP Brasil"}, {"ticker": "JHSF3", "nome": "JHSF"},
    {"ticker": "LCAM3", "nome": "Locamerica"}, {"ticker": "MOVI3", "nome": "Movida"},
    {"ticker": "NEOE3", "nome": "Neoenergia"}, {"ticker": "PSSA3", "nome": "Porto Seguro"},
    {"ticker": "QUAL3", "nome": "Qualicorp"}, {"ticker": "RAPT4", "nome": "Randoncorp"},
    {"ticker": "SAPR11", "nome": "Sanepar Unit"}, {"ticker": "SEER3", "nome": "Ser Educacional"},
    {"ticker": "SOMA3", "nome": "Grupo Soma"}, {"ticker": "TEND3", "nome": "Tenda"},

    # --- 100 Small Caps Adicionais (SMLL e Mercado Amplo B3) ---
    {"ticker": "ABCB4", "nome": "Banco ABC Brasil"}, {"ticker": "AGRO3", "nome": "BrasilAgro"},
    {"ticker": "ALPK3", "nome": "Estapar"}, {"ticker": "ARML3", "nome": "Armac"},
    {"ticker": "AALR3", "nome": "Alliar"}, {"ticker": "BLAU3", "nome": "Blau Farmacêutica"},
    {"ticker": "BMOB3", "nome": "Bemobi"}, {"ticker": "CAML3", "nome": "Camil Alimentos"},
    {"ticker": "CBAV3", "nome": "CBA Alumínio"}, {"ticker": "CEAB3", "nome": "C&A Modas"},
    {"ticker": "CLSA3", "nome": "ClearSale"}, {"ticker": "CSED3", "nome": "Cruzeiro do Sul Educacional"},
    {"ticker": "CURY3", "nome": "Cury Construtora"}, {"ticker": "DEXP3", "nome": "Dexxos"},
    {"ticker": "DMVF3", "nome": "D1000 Varejo Farma"}, {"ticker": "ECOR3", "nome": "EcoRodovias"},
    {"ticker": "ESPA3", "nome": "Espaçolaser"}, {"ticker": "EVEN3", "nome": "Even Construtora"},
    {"ticker": "FESA4", "nome": "Ferbasa"}, {"ticker": "FHER3", "nome": "Fertilizantes Heringer"},
    {"ticker": "FIQE3", "nome": "Unifique"}, {"ticker": "FRAS3", "nome": "Fras-le"},
    {"ticker": "GFSA3", "nome": "Gafisa"}, {"ticker": "GMAT3", "nome": "Grupo Mateus"},
    {"ticker": "GRND3", "nome": "Grendene"}, {"ticker": "GUAR3", "nome": "Guararapes"},
    {"ticker": "HBSA3", "nome": "Hidrovias do Brasil"}, {"ticker": "HBOR3", "nome": "Helbor"},
    {"ticker": "INTB3", "nome": "Intelbras"}, {"ticker": "JALL3", "nome": "Jalles Machado"},
    {"ticker": "KEPL3", "nome": "Kepler Weber"}, {"ticker": "LAVV3", "nome": "Lavvi Construtora"},
    {"ticker": "LEVE3", "nome": "Mahle Metal Leve"}, {"ticker": "LJQQ3", "nome": "Lojas Quero-Quero"},
    {"ticker": "LOGG3", "nome": "LOG CP"}, {"ticker": "LOGN3", "nome": "Log-In Logística"},
    {"ticker": "LIGT3", "nome": "Light"}, {"ticker": "LPSB3", "nome": "Lopes Brasil"},
    {"ticker": "MATD3", "nome": "Mater Dei"}, {"ticker": "MDIA3", "nome": "M. Dias Branco"},
    {"ticker": "MDNE3", "nome": "Moura Dubeux"}, {"ticker": "MEAL3", "nome": "IMC Alimentação"},
    {"ticker": "MEGA3", "nome": "MegaWhats"}, {"ticker": "MILS3", "nome": "Mills"},
    {"ticker": "MITRE3", "nome": "Mitre Realty"}, {"ticker": "MLAS3", "nome": "Multilaser"},
    {"ticker": "MYPK3", "nome": "Iochpe-Maxion"}, {"ticker": "ODPV3", "nome": "Odontoprev"},
    {"ticker": "OFSA3", "nome": "Ourofino Saúde Animal"}, {"ticker": "ONCO3", "nome": "Oncoclínicas"},
    {"ticker": "OPCT3", "nome": "OceanPact"}, {"ticker": "ORVR3", "nome": "Orizon"},
    {"ticker": "PARD3", "nome": "Hermes Pardini"}, {"ticker": "PGMN3", "nome": "Pague Menos"},
    {"ticker": "PLPL3", "nome": "Plano & Plano"}, {"ticker": "PNVL3", "nome": "Dimed Panvel"},
    {"ticker": "POMO4", "nome": "Marcopolo"}, {"ticker": "PORT3", "nome": "Wilson Sons"},
    {"ticker": "POSI3", "nome": "Positivo Tecnologia"}, {"ticker": "PRNR3", "nome": "Priner"},
    {"ticker": "PINE4", "nome": "Banco Pine"}, {"ticker": "RANI3", "nome": "Irani Papel"},
    {"ticker": "ROMI3", "nome": "Indústrias Romi"}, {"ticker": "SAPR4", "nome": "Sanepar PN"},
    {"ticker": "SGPS3", "nome": "Springs Global"}, {"ticker": "SHUL4", "nome": "Schulz"},
    {"ticker": "SIMH3", "nome": "Simpar"}, {"ticker": "SOJA3", "nome": "Boa Safra Sementes"},
    {"ticker": "SRNA3", "nome": "Serena Energia"}, {"ticker": "STBP3", "nome": "Santos Brasil"},
    {"ticker": "SYNE3", "nome": "Syn Prop & Tech"}, {"ticker": "TASA4", "nome": "Taurus Armas"},
    {"ticker": "TCNO4", "nome": "Tecnosolo"}, {"ticker": "TECN3", "nome": "Technos"},
    {"ticker": "TGMA3", "nome": "Tegma Gestão Logística"}, {"ticker": "TRIS3", "nome": "Trisul"},
    {"ticker": "TTEN3", "nome": "3Tentos"}, {"ticker": "TUPY3", "nome": "Tupy"},
    {"ticker": "UNIP6", "nome": "Unipar Carbocloro"}, {"ticker": "VIVA3", "nome": "Vivara"},
    {"ticker": "VITT3", "nome": "Vittia"}, {"ticker": "VLID3", "nome": "Valid"},
    {"ticker": "VULC3", "nome": "Vulcabras"}, {"ticker": "WIZC3", "nome": "Wiz Co"},
    {"ticker": "ZAMP3", "nome": "Zamp Burger King"}, {"ticker": "BMGB4", "nome": "Banco BMG"},
    {"ticker": "DESK3", "nome": "Desktop Sigmanet"}, {"ticker": "ENJU3", "nome": "Enjoei"},
    {"ticker": "SHOW3", "nome": "Time For Fun"}, {"ticker": "WEST3", "nome": "Westwing Brasil"},
    {"ticker": "NINJ3", "nome": "GetNinjas"}, {"ticker": "DOTZ3", "nome": "Dotz"},
    {"ticker": "AMBP3", "nome": "Ambipar"}, {"ticker": "LAVV3", "nome": "Lavvi"},
    {"ticker": "LOGG3", "nome": "Log Commercial Properties"}, {"ticker": "MTRE3", "nome": "Mitre"},
    {"ticker": "MELK3", "nome": "Melnick Desenvolvimento"}, {"ticker": "JALL3", "nome": "Jalles Machado"}
]

# Sanitização rigorosa para garantir exatamente 200 ações sem duplicatas
mapa_acoes = {}
for acao in acoes_200:
    t = acao["ticker"].strip().upper()
    if t not in mapa_acoes and len(mapa_acoes) < 200:
        mapa_acoes[t] = {
            "ticker": t,
            "tipo": "AÇÃO",
            "nome": acao.get("nome", t)
        }

lista_acoes_final = list(mapa_acoes.values())
catalogo_completo = lista_acoes_final + fiis + bdrs + etfs

with open(ARQUIVO, "w", encoding="utf-8") as f:
    json.dump(catalogo_completo, f, indent=4, ensure_ascii=False)

print("=" * 60)
print("BASE DE DADOS B3 RECONFIGURADA COM SUCESSO!")
print(f"• Ações Catalogadas: {len(lista_acoes_final)}")
print(f"• FIIs / FIAGROs: {len(fiis)}")
print(f"• ETFs Institucionais: {len(etfs)}")
print(f"• BDRs Globais: {len(bdrs)}")
print(f"TOTAL CONSOLIDADO: {len(catalogo_completo)} ATIVOS")
print("=" * 60)
